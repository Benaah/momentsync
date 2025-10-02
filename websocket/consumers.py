import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from moments.models import Moment, WebRTCConnection, Notification
from api.services import NotificationService, WebRTCService
import logging

logger = logging.getLogger(__name__)


class MomentConsumer(AsyncWebsocketConsumer):
    """
    Enhanced WebSocket consumer for real-time moment updates
    """
    
    async def connect(self):
        self.moment_id = self.scope['url_route']['kwargs']['momentID']
        self.moment_group_name = f'moment_{self.moment_id}'
        self.user = self.scope['user']
        
        # Check if user has access to the moment
        if not await self.check_moment_access():
            await self.close()
            return
        
        # Join moment group
        await self.channel_layer.group_add(
            self.moment_group_name,
            self.channel_name
        )
        
        # Join user-specific group for notifications
        if self.user.is_authenticated:
            await self.channel_layer.group_add(
                f'user_{self.user.username}',
                self.channel_name
            )
        
        await self.accept()
        
        # Send initial moment data
        await self.send_moment_data()
        
        # Update user's last seen
        if self.user.is_authenticated:
            await self.update_user_last_seen()
    
    async def disconnect(self, close_code):
        # Leave moment group
        await self.channel_layer.group_discard(
            self.moment_group_name,
            self.channel_name
        )
        
        # Leave user group
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                f'user_{self.user.username}',
                self.channel_name
            )
        
        # Clean up WebRTC connections
        await self.cleanup_webrtc_connections()
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'add_media':
                await self.handle_add_media(data)
            elif message_type == 'remove_media':
                await self.handle_remove_media(data)
            elif message_type == 'webrtc_offer':
                await self.handle_webrtc_offer(data)
            elif message_type == 'webrtc_answer':
                await self.handle_webrtc_answer(data)
            elif message_type == 'webrtc_ice_candidate':
                await self.handle_webrtc_ice_candidate(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'ping':
                await self.send_pong()
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    async def check_moment_access(self):
        """Check if user has access to the moment"""
        if not self.user.is_authenticated:
            return False
        
        try:
            moment = await database_sync_to_async(Moment.objects.get)(
                momentID=self.moment_id
            )
            return (moment.owner_username == self.user.username or 
                   self.user.username in (moment.allowed_usernames or []))
        except Moment.DoesNotExist:
            return False
    
    async def send_moment_data(self):
        """Send initial moment data to client"""
        try:
            moment = await database_sync_to_async(Moment.objects.get)(
                momentID=self.moment_id
            )
            
            data = {
                'type': 'moment_data',
                'moment': {
                    'id': moment.momentID,
                    'name': moment.name,
                    'description': moment.description,
                    'media_count': len(moment.imgIDs),
                    'member_count': len(moment.allowed_usernames or []),
                    'is_public': moment.is_public,
                    'webrtc_enabled': moment.webrtc_enabled
                }
            }
            
            await self.send(text_data=json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending moment data: {str(e)}")
    
    async def handle_add_media(self, data):
        """Handle adding media to moment"""
        try:
            media_id = data.get('media_id')
            if not media_id:
                return
            
            moment = await database_sync_to_async(Moment.objects.get)(
                momentID=self.moment_id
            )
            
            if media_id not in moment.imgIDs:
                moment.imgIDs.append(media_id)
                await database_sync_to_async(moment.save)()
                
                # Broadcast to all connected clients
                await self.channel_layer.group_send(
                    self.moment_group_name,
                    {
                        'type': 'media_added',
                        'media_id': media_id,
                        'uploader': self.user.username,
                        'timestamp': data.get('timestamp')
                    }
                )
                
                # Send notification to other users
                await self.send_notification(
                    'media_upload',
                    f"{self.user.username} uploaded new media",
                    moment=moment
                )
                
        except Exception as e:
            logger.error(f"Error handling add media: {str(e)}")
    
    async def handle_remove_media(self, data):
        """Handle removing media from moment"""
        try:
            media_id = data.get('media_id')
            if not media_id:
                return
            
            moment = await database_sync_to_async(Moment.objects.get)(
                momentID=self.moment_id
            )
            
            if media_id in moment.imgIDs:
                moment.imgIDs.remove(media_id)
                await database_sync_to_async(moment.save)()
                
                # Broadcast to all connected clients
                await self.channel_layer.group_send(
                    self.moment_group_name,
                    {
                        'type': 'media_removed',
                        'media_id': media_id,
                        'remover': self.user.username,
                        'timestamp': data.get('timestamp')
                    }
                )
                
        except Exception as e:
            logger.error(f"Error handling remove media: {str(e)}")
    
    async def handle_webrtc_offer(self, data):
        """Handle WebRTC offer"""
        try:
            offer = data.get('offer')
            if not offer:
                return
            
            # Create WebRTC connection record
            connection_id = data.get('connection_id', f"{self.user.username}_{self.moment_id}")
            
            await database_sync_to_async(WebRTCConnection.objects.create)(
                moment_id=self.moment_id,
                user=self.user,
                connection_id=connection_id,
                peer_id=data.get('peer_id', ''),
                is_active=True
            )
            
            # Broadcast offer to other participants
            await self.channel_layer.group_send(
                self.moment_group_name,
                {
                    'type': 'webrtc_offer',
                    'offer': offer,
                    'from_user': self.user.username,
                    'connection_id': connection_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling WebRTC offer: {str(e)}")
    
    async def handle_webrtc_answer(self, data):
        """Handle WebRTC answer"""
        try:
            answer = data.get('answer')
            connection_id = data.get('connection_id')
            
            if not answer or not connection_id:
                return
            
            # Broadcast answer to specific connection
            await self.channel_layer.group_send(
                self.moment_group_name,
                {
                    'type': 'webrtc_answer',
                    'answer': answer,
                    'to_user': data.get('to_user'),
                    'connection_id': connection_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling WebRTC answer: {str(e)}")
    
    async def handle_webrtc_ice_candidate(self, data):
        """Handle WebRTC ICE candidate"""
        try:
            candidate = data.get('candidate')
            connection_id = data.get('connection_id')
            
            if not candidate or not connection_id:
                return
            
            # Broadcast ICE candidate
            await self.channel_layer.group_send(
                self.moment_group_name,
                {
                    'type': 'webrtc_ice_candidate',
                    'candidate': candidate,
                    'from_user': self.user.username,
                    'connection_id': connection_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling WebRTC ICE candidate: {str(e)}")
    
    async def handle_typing(self, data):
        """Handle typing indicator"""
        try:
            is_typing = data.get('is_typing', False)
            
            # Broadcast typing status to other users
            await self.channel_layer.group_send(
                self.moment_group_name,
                {
                    'type': 'user_typing',
                    'user': self.user.username,
                    'is_typing': is_typing
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling typing: {str(e)}")
    
    async def send_pong(self):
        """Send pong response to ping"""
        await self.send(text_data=json.dumps({'type': 'pong'}))
    
    async def media_added(self, event):
        """Handle media added event"""
        await self.send(text_data=json.dumps({
            'type': 'media_added',
            'media_id': event['media_id'],
            'uploader': event['uploader'],
            'timestamp': event['timestamp']
        }))
    
    async def media_removed(self, event):
        """Handle media removed event"""
        await self.send(text_data=json.dumps({
            'type': 'media_removed',
            'media_id': event['media_id'],
            'remover': event['remover'],
            'timestamp': event['timestamp']
        }))
    
    async def webrtc_offer(self, event):
        """Handle WebRTC offer event"""
        # Don't send to the user who sent the offer
        if event['from_user'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_offer',
                'offer': event['offer'],
                'from_user': event['from_user'],
                'connection_id': event['connection_id']
            }))
    
    async def webrtc_answer(self, event):
        """Handle WebRTC answer event"""
        await self.send(text_data=json.dumps({
            'type': 'webrtc_answer',
            'answer': event['answer'],
            'to_user': event['to_user'],
            'connection_id': event['connection_id']
        }))
    
    async def webrtc_ice_candidate(self, event):
        """Handle WebRTC ICE candidate event"""
        # Don't send to the user who sent the candidate
        if event['from_user'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_ice_candidate',
                'candidate': event['candidate'],
                'from_user': event['from_user'],
                'connection_id': event['connection_id']
            }))
    
    async def user_typing(self, event):
        """Handle user typing event"""
        # Don't send to the user who is typing
        if event['user'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'user_typing',
                'user': event['user'],
                'is_typing': event['is_typing']
            }))
    
    async def notification(self, event):
        """Handle notification event"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event['message']['title'],
            'body': event['message']['body'],
            'notification_type': event['message'].get('type', 'info')
        }))
    
    async def update_user_last_seen(self):
        """Update user's last seen timestamp"""
        try:
            if hasattr(self.user, 'profile'):
                await database_sync_to_async(self.user.profile.update_last_seen)()
        except Exception as e:
            logger.error(f"Error updating last seen: {str(e)}")
    
    async def cleanup_webrtc_connections(self):
        """Clean up WebRTC connections on disconnect"""
        try:
            await database_sync_to_async(WebRTCConnection.objects.filter(
                user=self.user,
                moment_id=self.moment_id,
                is_active=True
            ).update)(is_active=False)
        except Exception as e:
            logger.error(f"Error cleaning up WebRTC connections: {str(e)}")
    
    async def send_notification(self, notification_type, message, moment=None):
        """Send notification to other users"""
        try:
            notification_service = NotificationService()
            
            # Get other users in the moment
            if moment:
                other_users = [username for username in moment.allowed_usernames 
                             if username != self.user.username]
                
                for username in other_users:
                    await notification_service.send_websocket_message(
                        f'user_{username}',
                        {
                            'type': notification_type,
                            'title': 'MomentSync Update',
                            'body': message,
                            'moment_id': self.moment_id
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
