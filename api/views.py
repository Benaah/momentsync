from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from asgiref.sync import sync_to_async
import asyncio
import json

from moments.models import Moment, Profile
from .serializers import MomentSerializer, UserSerializer, MediaSerializer
from .permissions import IsOwnerOrReadOnly, IsMomentMember
from .services import MediaProcessingService, WebRTCService
from .ffmpeg_service import FFmpegService
from .storage_service import CloudStorageService
from .ai_service import AIService
from .security_service import SecurityService
from .mobile_service import MobileService
from .analytics_service import AnalyticsService
from .tasks import process_media_async, generate_video_thumbnails, convert_image_formats


class MomentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing moments with real-time capabilities
    """
    serializer_class = MomentSerializer
    permission_classes = [IsAuthenticated, IsMomentMember]
    
    def get_queryset(self):
        user = self.request.user
        return Moment.objects.filter(
            Q(owner_username=user.username) | 
            Q(allowed_usernames__contains=[user.username])
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def add_media(self, request, pk=None):
        """Add media to a moment with real-time updates and FFmpeg processing"""
        moment = self.get_object()
        media_file = request.FILES.get('media')
        
        if not media_file:
            return Response(
                {'error': 'No media file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size
        if media_file.size > settings.MAX_FILE_SIZE:
            return Response(
                {'error': f'File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create MediaItem record
        from moments.models import MediaItem
        import uuid
        import hashlib
        
        # Generate file ID
        file_content = media_file.read()
        media_file.seek(0)  # Reset file pointer
        file_id = hashlib.md5(file_content).hexdigest()
        
        # Create MediaItem
        media_item = MediaItem.objects.create(
            moment=moment,
            uploader=request.user,
            file_id=file_id,
            file_name=media_file.name,
            file_size=media_file.size,
            file_type=media_file.content_type.split('/')[0],
            mime_type=media_file.content_type,
            original_url='',  # Will be updated after processing
            is_processed=False
        )
        
        # Save file temporarily
        temp_path = f'/tmp/{file_id}_{media_file.name}'
        with open(temp_path, 'wb+') as destination:
            for chunk in media_file.chunks():
                destination.write(chunk)
        
        # Start async processing with FFmpeg
        task = process_media_async.delay(
            str(media_item.id),
            temp_path,
            media_file.content_type,
            {
                'generate_thumbnails': True,
                'convert_formats': True,
                'generate_gif': media_file.content_type.startswith('video/'),
                'extract_audio': media_file.content_type.startswith('video/'),
                'generate_blur': True
            }
        )
        
        # Add media ID to moment
        moment.imgIDs.append(file_id)
        moment.save()
        
        # Send real-time update via WebSocket
        asyncio.run(self._broadcast_media_update(moment, file_id, 'add'))
        
        return Response({
            'success': True,
            'media_id': file_id,
            'task_id': task.id,
            'message': 'Media uploaded and processing started'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def remove_media(self, request, pk=None):
        """Remove media from a moment with real-time updates"""
        moment = self.get_object()
        media_id = request.data.get('media_id')
        
        if not media_id:
            return Response(
                {'error': 'No media ID provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if media_id in moment.imgIDs:
            moment.imgIDs.remove(media_id)
            moment.save()
            
            # Send real-time update via WebSocket
            asyncio.run(self._broadcast_media_update(moment, media_id, 'remove'))
            
            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Media not found in moment'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def invite_user(self, request, pk=None):
        """Invite a user to join a moment"""
        moment = self.get_object()
        username = request.data.get('username')
        
        if not username:
            return Response(
                {'error': 'Username required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if username not in moment.allowed_usernames:
            moment.allowed_usernames.append(username)
            moment.save()
            
            # Send real-time notification
            asyncio.run(self._broadcast_invitation(moment, username))
            
            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'User already has access'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def webrtc_offer(self, request, pk=None):
        """Generate WebRTC offer for peer-to-peer communication"""
        moment = self.get_object()
        webrtc_service = WebRTCService()
        offer = asyncio.run(webrtc_service.create_offer(moment.momentID))
        return Response({'offer': offer}, status=status.HTTP_200_OK)
    
    async def _broadcast_media_update(self, moment, media_id, action):
        """Broadcast media updates to all connected clients"""
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        
        await channel_layer.group_send(
            f"moment_{moment.momentID}",
            {
                'type': 'media_update',
                'media_id': media_id,
                'action': action,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def _broadcast_invitation(self, moment, username):
        """Broadcast invitation to the invited user"""
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        
        await channel_layer.group_send(
            f"user_{username}",
            {
                'type': 'moment_invitation',
                'moment_id': moment.momentID,
                'moment_name': moment.name,
                'inviter': moment.owner_username
            }
        )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user management
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search users by username"""
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response(
                {'error': 'Query must be at least 2 characters'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        users = User.objects.filter(
            username__icontains=query
        ).exclude(id=request.user.id)[:10]
        
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)


class MediaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for media management
    """
    serializer_class = MediaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Return media from moments the user has access to
        user = self.request.user
        moments = Moment.objects.filter(
            Q(owner_username=user.username) | 
            Q(allowed_usernames__contains=[user.username])
        )
        
        media_ids = []
        for moment in moments:
            media_ids.extend(moment.imgIDs)
        
        return media_ids
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload media with AI processing"""
        media_file = request.FILES.get('media')
        
        if not media_file:
            return Response(
                {'error': 'No media file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process with AI features
        media_service = MediaProcessingService()
        result = asyncio.run(media_service.process_with_ai(media_file))
        
        return Response(result, status=status.HTTP_201_CREATED)


class AnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for analytics and monitoring
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard metrics"""
        analytics_service = AnalyticsService()
        result = asyncio.run(analytics_service.get_dashboard_metrics())
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """Get performance report"""
        time_range = request.query_params.get('range', '24h')
        analytics_service = AnalyticsService()
        result = asyncio.run(analytics_service.get_performance_report(time_range))
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def user_analytics(self, request):
        """Get user-specific analytics"""
        user_id = request.user.id
        analytics_service = AnalyticsService()
        result = asyncio.run(analytics_service.get_user_analytics(user_id))
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def export(self, request):
        """Export analytics data"""
        format_type = request.data.get('format', 'json')
        analytics_service = AnalyticsService()
        result = asyncio.run(analytics_service.export_analytics_data(format_type))
        return Response(result)


class SecurityViewSet(viewsets.ViewSet):
    """
    ViewSet for security features
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def check_rate_limit(self, request):
        """Check rate limit for user action"""
        action_type = request.data.get('action', 'api')
        ip_address = request.META.get('REMOTE_ADDR')
        security_service = SecurityService()
        result = security_service.check_rate_limit(request.user.id, action_type, ip_address)
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def validate_file(self, request):
        """Validate file upload for security"""
        file = request.FILES.get('file')
        max_size = request.data.get('max_size', 10485760)  # 10MB default
        allowed_types = request.data.get('allowed_types', ['image', 'video'])
        
        security_service = SecurityService()
        result = security_service.validate_file_upload(file, max_size, allowed_types)
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def moderate_text(self, request):
        """Moderate text content"""
        text = request.data.get('text', '')
        ai_service = AIService()
        result = asyncio.run(ai_service.moderate_text(text))
        return Response(result)


class MobileViewSet(viewsets.ViewSet):
    """
    ViewSet for mobile features
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def camera_capture(self, request):
        """Process camera capture from mobile"""
        image_data = request.data.get('image_data')
        metadata = request.data.get('metadata', {})
        
        if not image_data:
            return Response({'error': 'No image data provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        mobile_service = MobileService()
        result = asyncio.run(mobile_service.process_camera_capture(
            image_data.encode(), metadata, request.user.id
        ))
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def enable_offline(self, request):
        """Enable offline mode for moments"""
        moment_ids = request.data.get('moment_ids', [])
        mobile_service = MobileService()
        result = asyncio.run(mobile_service.enable_offline_mode(request.user.id, moment_ids))
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def sync_offline(self, request):
        """Sync offline data"""
        offline_data = request.data.get('offline_data', {})
        mobile_service = MobileService()
        result = asyncio.run(mobile_service.sync_offline_data(request.user.id, offline_data))
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def register_fcm(self, request):
        """Register FCM token for push notifications"""
        fcm_token = request.data.get('fcm_token')
        device_info = request.data.get('device_info', {})
        
        if not fcm_token:
            return Response({'error': 'FCM token required'}, status=status.HTTP_400_BAD_REQUEST)
        
        mobile_service = MobileService()
        result = asyncio.run(mobile_service.register_fcm_token(
            request.user.id, fcm_token, device_info
        ))
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def camera_config(self, request):
        """Get camera configuration"""
        mobile_service = MobileService()
        result = asyncio.run(mobile_service.get_camera_config())
        return Response(result)


class AIViewSet(viewsets.ViewSet):
    """
    ViewSet for AI features
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def analyze_image(self, request):
        """Analyze image with AI"""
        image_data = request.data.get('image_data')
        
        if not image_data:
            return Response({'error': 'No image data provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        ai_service = AIService()
        result = asyncio.run(ai_service.analyze_image(image_data.encode()))
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def smart_compress(self, request):
        """Smart compress image"""
        image_data = request.data.get('image_data')
        target_size = request.data.get('target_size', 500000)
        
        if not image_data:
            return Response({'error': 'No image data provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        ai_service = AIService()
        result = asyncio.run(ai_service.smart_compress(image_data.encode(), target_size))
        return Response({'compressed_data': result.decode()})
    
    @action(detail=False, methods=['post'])
    def generate_tags(self, request):
        """Generate tags from image analysis"""
        analysis = request.data.get('analysis', {})
        
        ai_service = AIService()
        result = asyncio.run(ai_service.generate_tags(analysis))
        return Response({'tags': result})


class StorageViewSet(viewsets.ViewSet):
    """
    ViewSet for cloud storage features
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def upload_media(self, request):
        """Upload media with optimized storage"""
        file_data = request.data.get('file_data')
        file_name = request.data.get('file_name')
        content_type = request.data.get('content_type')
        folder = request.data.get('folder', 'media')
        
        if not all([file_data, file_name, content_type]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
        
        storage_service = CloudStorageService()
        result = asyncio.run(storage_service.upload_media(
            file_data.encode(), file_name, content_type, folder
        ))
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def media_info(self, request):
        """Get media information"""
        file_id = request.query_params.get('file_id')
        
        if not file_id:
            return Response({'error': 'File ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        storage_service = CloudStorageService()
        result = asyncio.run(storage_service.get_media_info(file_id))
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def optimize_storage(self, request):
        """Optimize storage"""
        storage_service = CloudStorageService()
        result = asyncio.run(storage_service.optimize_storage())
        return Response(result)
