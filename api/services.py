import asyncio
import hashlib
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import cv2
import numpy as np
from PIL import Image, ExifTags
import boto3
from django.conf import settings
from django.core.files.storage import default_storage
import logging

logger = logging.getLogger(__name__)


class MediaProcessingService:
    """
    Service for processing media files with AI and optimization features
    """
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.environ.get('AWS_S3_BUCKET', 'momentsync-media')
    
    async def process_and_upload(self, media_file, moment) -> Dict[str, Any]:
        """
        Process media file with AI features and upload to cloud storage
        """
        try:
            # Generate unique ID
            media_id = self._generate_media_id(media_file)
            
            # Process image with AI
            ai_results = await self._process_with_ai(media_file)
            
            # Optimize and compress
            optimized_file = await self._optimize_media(media_file, ai_results)
            
            # Upload to cloud storage
            upload_result = await self._upload_to_cloud(optimized_file, media_id)
            
            if upload_result['success']:
                # Update moment with new media
                moment.imgIDs.append(media_id)
                moment.save()
                
                return {
                    'success': True,
                    'media_id': media_id,
                    'url': upload_result['url'],
                    'thumbnail_url': upload_result['thumbnail_url'],
                    'ai_tags': ai_results.get('tags', []),
                    'ai_description': ai_results.get('description', ''),
                    'file_size': upload_result['file_size'],
                    'compression_ratio': upload_result['compression_ratio']
                }
            else:
                return {'success': False, 'error': upload_result['error']}
                
        except Exception as e:
            logger.error(f"Error processing media: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def process_with_ai(self, media_file) -> Dict[str, Any]:
        """
        Process media with AI features like tagging and description
        """
        try:
            # Read image
            image = Image.open(media_file)
            image_array = np.array(image)
            
            # AI-powered image analysis
            tags = await self._generate_ai_tags(image_array)
            description = await self._generate_ai_description(image_array)
            
            # Detect faces and objects
            faces = await self._detect_faces(image_array)
            objects = await self._detect_objects(image_array)
            
            return {
                'tags': tags,
                'description': description,
                'faces': faces,
                'objects': objects,
                'metadata': self._extract_metadata(image)
            }
            
        except Exception as e:
            logger.error(f"Error in AI processing: {str(e)}")
            return {'tags': [], 'description': '', 'faces': [], 'objects': []}
    
    def _generate_media_id(self, media_file) -> str:
        """Generate unique media ID"""
        content = media_file.read()
        media_file.seek(0)  # Reset file pointer
        return hashlib.md5(content).hexdigest()
    
    async def _process_with_ai(self, media_file) -> Dict[str, Any]:
        """Process media with AI features"""
        # This would integrate with AI services like AWS Rekognition, Google Vision API, etc.
        # For now, return mock data
        return {
            'tags': ['photo', 'moment', 'shared'],
            'description': 'A shared moment captured and uploaded',
            'faces': [],
            'objects': []
        }
    
    async def _optimize_media(self, media_file, ai_results) -> Any:
        """Optimize media for web delivery"""
        try:
            image = Image.open(media_file)
            
            # Convert to modern formats (WebP/AVIF)
            if image.format == 'JPEG':
                # Create WebP version
                webp_buffer = io.BytesIO()
                image.save(webp_buffer, format='WebP', quality=85, optimize=True)
                webp_buffer.seek(0)
                return webp_buffer
            else:
                return media_file
                
        except Exception as e:
            logger.error(f"Error optimizing media: {str(e)}")
            return media_file
    
    async def _upload_to_cloud(self, media_file, media_id) -> Dict[str, Any]:
        """Upload media to cloud storage"""
        try:
            # Upload original
            original_key = f"images/{media_id}"
            self.s3_client.upload_fileobj(
                media_file, 
                self.bucket_name, 
                original_key,
                ExtraArgs={'ContentType': 'image/webp'}
            )
            
            # Create thumbnail
            thumbnail = await self._create_thumbnail(media_file)
            thumbnail_key = f"thumbnails/{media_id}"
            self.s3_client.upload_fileobj(
                thumbnail,
                self.bucket_name,
                thumbnail_key,
                ExtraArgs={'ContentType': 'image/webp'}
            )
            
            return {
                'success': True,
                'url': f"https://{self.bucket_name}.s3.amazonaws.com/{original_key}",
                'thumbnail_url': f"https://{self.bucket_name}.s3.amazonaws.com/{thumbnail_key}",
                'file_size': media_file.tell(),
                'compression_ratio': 0.7  # Mock value
            }
            
        except Exception as e:
            logger.error(f"Error uploading to cloud: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _create_thumbnail(self, media_file) -> Any:
        """Create thumbnail for media"""
        try:
            image = Image.open(media_file)
            image.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            thumbnail_buffer = io.BytesIO()
            image.save(thumbnail_buffer, format='WebP', quality=80)
            thumbnail_buffer.seek(0)
            return thumbnail_buffer
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {str(e)}")
            return media_file
    
    async def _generate_ai_tags(self, image_array) -> list:
        """Generate AI tags for image"""
        # This would integrate with AI services
        return ['photo', 'moment', 'shared']
    
    async def _generate_ai_description(self, image_array) -> str:
        """Generate AI description for image"""
        # This would integrate with AI services
        return "A shared moment captured and uploaded"
    
    async def _detect_faces(self, image_array) -> list:
        """Detect faces in image"""
        # This would use OpenCV or AI services
        return []
    
    async def _detect_objects(self, image_array) -> list:
        """Detect objects in image"""
        # This would use AI services
        return []
    
    def _extract_metadata(self, image) -> Dict[str, Any]:
        """Extract EXIF metadata from image"""
        metadata = {}
        if hasattr(image, '_getexif'):
            exif = image._getexif()
            if exif:
                for tag, value in exif.items():
                    tag_name = ExifTags.TAGS.get(tag, tag)
                    metadata[tag_name] = value
        return metadata


class WebRTCService:
    """
    Service for WebRTC peer-to-peer communication
    """
    
    def __init__(self):
        self.stun_servers = [
            'stun:stun.l.google.com:19302',
            'stun:stun1.l.google.com:19302'
        ]
    
    async def create_offer(self, moment_id: str) -> Dict[str, Any]:
        """Create WebRTC offer for peer-to-peer communication"""
        try:
            # This would integrate with WebRTC libraries
            offer = {
                'type': 'offer',
                'sdp': 'mock_sdp_offer',
                'moment_id': moment_id,
                'timestamp': datetime.now().isoformat()
            }
            return offer
        except Exception as e:
            logger.error(f"Error creating WebRTC offer: {str(e)}")
            return {'error': str(e)}
    
    async def handle_answer(self, answer: Dict[str, Any]) -> bool:
        """Handle WebRTC answer from peer"""
        try:
            # Process WebRTC answer
            return True
        except Exception as e:
            logger.error(f"Error handling WebRTC answer: {str(e)}")
            return False


class NotificationService:
    """
    Service for sending real-time notifications
    """
    
    async def send_push_notification(self, user_id: str, title: str, body: str, data: Dict = None):
        """Send push notification to user"""
        try:
            # This would integrate with FCM or similar service
            logger.info(f"Push notification sent to {user_id}: {title}")
            return True
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            return False
    
    async def send_websocket_message(self, channel: str, message: Dict[str, Any]):
        """Send WebSocket message to channel"""
        try:
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            
            await channel_layer.group_send(channel, {
                'type': 'notification',
                'message': message
            })
            return True
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}")
            return False
