import os
import json
import base64
import requests
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User
import logging
from datetime import datetime, timedelta
import asyncio
import aiohttp
from PIL import Image
import io
import hashlib
import secrets

logger = logging.getLogger(__name__)


class MobileService:
    """
    Mobile features service for MomentSync
    Includes native camera API, offline support, and push notifications
    """
    
    def __init__(self):
        self.firebase_server_key = os.environ.get('FIREBASE_SERVER_KEY')
        self.fcm_url = 'https://fcm.googleapis.com/fcm/send'
        self.offline_cache_ttl = 3600  # 1 hour
        self.push_notification_ttl = 86400  # 24 hours
        
        # Camera API configuration
        self.camera_config = {
            'max_resolution': {'width': 4096, 'height': 4096},
            'supported_formats': ['image/jpeg', 'image/png', 'image/webp'],
            'quality_presets': ['low', 'medium', 'high', 'ultra'],
            'flash_modes': ['auto', 'on', 'off', 'torch'],
            'focus_modes': ['auto', 'continuous', 'macro', 'fixed']
        }
    
    async def process_camera_capture(self, image_data: bytes, metadata: Dict[str, Any], 
                                   user_id: int) -> Dict[str, Any]:
        """
        Process image captured from native camera
        """
        try:
            # Extract camera metadata
            camera_info = self._extract_camera_metadata(metadata)
            
            # Process image
            processed_image = await self._process_camera_image(image_data, camera_info)
            
            # Generate unique file ID
            file_id = hashlib.md5(image_data).hexdigest()
            
            # Store in cache for offline access
            cache_key = f'camera_capture_{user_id}_{file_id}'
            cache.set(cache_key, {
                'image_data': base64.b64encode(image_data).decode(),
                'metadata': camera_info,
                'timestamp': timezone.now().isoformat(),
                'processed': processed_image
            }, timeout=self.offline_cache_ttl)
            
            return {
                'success': True,
                'file_id': file_id,
                'camera_info': camera_info,
                'processed_image': processed_image,
                'offline_available': True
            }
            
        except Exception as e:
            logger.error(f"Error processing camera capture: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _extract_camera_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize camera metadata
        """
        try:
            camera_info = {
                'device': metadata.get('device', 'unknown'),
                'orientation': metadata.get('orientation', 0),
                'flash_used': metadata.get('flash', False),
                'focus_mode': metadata.get('focus_mode', 'auto'),
                'exposure_time': metadata.get('exposure_time', 0),
                'iso': metadata.get('iso', 0),
                'aperture': metadata.get('aperture', 0),
                'focal_length': metadata.get('focal_length', 0),
                'white_balance': metadata.get('white_balance', 'auto'),
                'timestamp': metadata.get('timestamp', timezone.now().isoformat()),
                'location': metadata.get('location', {}),
                'quality': metadata.get('quality', 'medium')
            }
            
            # Normalize orientation
            if camera_info['orientation'] in [90, 270]:
                camera_info['needs_rotation'] = True
            else:
                camera_info['needs_rotation'] = False
            
            return camera_info
            
        except Exception as e:
            logger.error(f"Error extracting camera metadata: {str(e)}")
            return {}
    
    async def _process_camera_image(self, image_data: bytes, camera_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process camera image with optimizations
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Rotate if necessary
            if camera_info.get('needs_rotation'):
                if camera_info['orientation'] == 90:
                    image = image.rotate(-90, expand=True)
                elif camera_info['orientation'] == 270:
                    image = image.rotate(90, expand=True)
            
            # Generate different sizes
            sizes = {
                'thumbnail': (300, 300),
                'medium': (800, 600),
                'large': (1920, 1080)
            }
            
            processed_versions = {}
            
            for size_name, dimensions in sizes.items():
                # Resize image
                resized = image.copy()
                resized.thumbnail(dimensions, Image.Resampling.LANCZOS)
                
                # Convert to bytes
                buffer = io.BytesIO()
                resized.save(buffer, format='JPEG', quality=85, optimize=True)
                processed_versions[size_name] = {
                    'data': base64.b64encode(buffer.getvalue()).decode(),
                    'size': len(buffer.getvalue()),
                    'dimensions': resized.size
                }
            
            return processed_versions
            
        except Exception as e:
            logger.error(f"Error processing camera image: {str(e)}")
            return {}
    
    async def enable_offline_mode(self, user_id: int, moment_ids: List[str]) -> Dict[str, Any]:
        """
        Enable offline mode for specific moments
        """
        try:
            # Store moment data in cache for offline access
            offline_data = {
                'moments': [],
                'media': [],
                'users': [],
                'timestamp': timezone.now().isoformat(),
                'ttl': self.offline_cache_ttl
            }
            
            # This would typically fetch data from the database
            # For now, we'll create a placeholder structure
            for moment_id in moment_ids:
                moment_data = {
                    'id': moment_id,
                    'name': f'Moment {moment_id}',
                    'offline_available': True,
                    'last_sync': timezone.now().isoformat()
                }
                offline_data['moments'].append(moment_data)
            
            # Store in cache
            cache_key = f'offline_data_{user_id}'
            cache.set(cache_key, offline_data, timeout=self.offline_cache_ttl)
            
            return {
                'success': True,
                'offline_data': offline_data,
                'message': 'Offline mode enabled for selected moments'
            }
            
        except Exception as e:
            logger.error(f"Error enabling offline mode: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def sync_offline_data(self, user_id: int, offline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync offline data when connection is restored
        """
        try:
            # This would typically sync with the server
            # For now, we'll simulate the sync process
            
            sync_results = {
                'uploaded_media': 0,
                'updated_moments': 0,
                'conflicts': 0,
                'errors': []
            }
            
            # Process offline media
            for media_item in offline_data.get('media', []):
                try:
                    # Simulate upload
                    sync_results['uploaded_media'] += 1
                except Exception as e:
                    sync_results['errors'].append(f"Media upload failed: {str(e)}")
            
            # Process offline moment updates
            for moment in offline_data.get('moments', []):
                try:
                    # Simulate update
                    sync_results['updated_moments'] += 1
                except Exception as e:
                    sync_results['errors'].append(f"Moment update failed: {str(e)}")
            
            return {
                'success': True,
                'sync_results': sync_results,
                'message': 'Offline data synced successfully'
            }
            
        except Exception as e:
            logger.error(f"Error syncing offline data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def send_push_notification(self, user_id: int, title: str, body: str, 
                                   data: Dict[str, Any] = None, moment_id: str = None) -> Dict[str, Any]:
        """
        Send push notification to user
        """
        try:
            if not self.firebase_server_key:
                return {'success': False, 'error': 'Firebase not configured'}
            
            # Get user's FCM token
            fcm_token = cache.get(f'fcm_token_{user_id}')
            if not fcm_token:
                return {'success': False, 'error': 'User FCM token not found'}
            
            # Prepare notification payload
            payload = {
                'to': fcm_token,
                'notification': {
                    'title': title,
                    'body': body,
                    'icon': 'ic_notification',
                    'sound': 'default',
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK'
                },
                'data': {
                    'moment_id': moment_id or '',
                    'timestamp': timezone.now().isoformat(),
                    **(data or {})
                },
                'priority': 'high',
                'ttl': self.push_notification_ttl
            }
            
            # Send notification
            headers = {
                'Authorization': f'key={self.firebase_server_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.fcm_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'message_id': result.get('message_id'),
                            'message': 'Push notification sent successfully'
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f'FCM error: {response.status} - {error_text}'
                        }
            
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def register_fcm_token(self, user_id: int, fcm_token: str, device_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Register FCM token for push notifications
        """
        try:
            # Store FCM token in cache
            cache_key = f'fcm_token_{user_id}'
            cache.set(cache_key, fcm_token, timeout=None)  # Never expire
            
            # Store device info
            if device_info:
                device_cache_key = f'device_info_{user_id}'
                cache.set(device_cache_key, device_info, timeout=86400)  # 24 hours
            
            return {
                'success': True,
                'message': 'FCM token registered successfully'
            }
            
        except Exception as e:
            logger.error(f"Error registering FCM token: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def send_batch_notifications(self, notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send multiple push notifications efficiently
        """
        try:
            if not self.firebase_server_key:
                return {'success': False, 'error': 'Firebase not configured'}
            
            # Group notifications by FCM token
            token_groups = {}
            for notification in notifications:
                user_id = notification['user_id']
                fcm_token = cache.get(f'fcm_token_{user_id}')
                
                if fcm_token:
                    if fcm_token not in token_groups:
                        token_groups[fcm_token] = []
                    token_groups[fcm_token].append(notification)
            
            # Send notifications in batches
            results = []
            for fcm_token, user_notifications in token_groups.items():
                try:
                    # Create batch payload
                    payload = {
                        'to': fcm_token,
                        'notification': {
                            'title': f"{len(user_notifications)} new updates",
                            'body': f"You have {len(user_notifications)} new updates in your moments",
                            'icon': 'ic_notification',
                            'sound': 'default'
                        },
                        'data': {
                            'count': str(len(user_notifications)),
                            'timestamp': timezone.now().isoformat()
                        },
                        'priority': 'high'
                    }
                    
                    headers = {
                        'Authorization': f'key={self.firebase_server_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(self.fcm_url, headers=headers, json=payload) as response:
                            if response.status == 200:
                                result = await response.json()
                                results.append({
                                    'success': True,
                                    'fcm_token': fcm_token,
                                    'message_id': result.get('message_id')
                                })
                            else:
                                results.append({
                                    'success': False,
                                    'fcm_token': fcm_token,
                                    'error': f'FCM error: {response.status}'
                                })
                
                except Exception as e:
                    results.append({
                        'success': False,
                        'fcm_token': fcm_token,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'results': results,
                'total_sent': len([r for r in results if r['success']])
            }
            
        except Exception as e:
            logger.error(f"Error sending batch notifications: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_offline_data(self, user_id: int) -> Dict[str, Any]:
        """
        Get cached offline data for user
        """
        try:
            cache_key = f'offline_data_{user_id}'
            offline_data = cache.get(cache_key)
            
            if not offline_data:
                return {
                    'success': False,
                    'error': 'No offline data available'
                }
            
            return {
                'success': True,
                'offline_data': offline_data
            }
            
        except Exception as e:
            logger.error(f"Error getting offline data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def clear_offline_data(self, user_id: int) -> Dict[str, Any]:
        """
        Clear offline data for user
        """
        try:
            cache_key = f'offline_data_{user_id}'
            cache.delete(cache_key)
            
            return {
                'success': True,
                'message': 'Offline data cleared successfully'
            }
            
        except Exception as e:
            logger.error(f"Error clearing offline data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_camera_config(self) -> Dict[str, Any]:
        """
        Get camera configuration for mobile app
        """
        try:
            return {
                'success': True,
                'config': self.camera_config
            }
        except Exception as e:
            logger.error(f"Error getting camera config: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def validate_camera_permissions(self, user_id: int) -> Dict[str, Any]:
        """
        Validate camera permissions for user
        """
        try:
            # Check if user has camera permissions
            permissions = cache.get(f'camera_permissions_{user_id}', {})
            
            return {
                'success': True,
                'permissions': permissions,
                'camera_available': 'camera' in permissions and permissions['camera']
            }
            
        except Exception as e:
            logger.error(f"Error validating camera permissions: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def update_camera_permissions(self, user_id: int, permissions: Dict[str, bool]) -> Dict[str, Any]:
        """
        Update camera permissions for user
        """
        try:
            # Store permissions in cache
            cache_key = f'camera_permissions_{user_id}'
            cache.set(cache_key, permissions, timeout=86400)  # 24 hours
            
            return {
                'success': True,
                'message': 'Camera permissions updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error updating camera permissions: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_notification_history(self, user_id: int, limit: int = 50) -> Dict[str, Any]:
        """
        Get notification history for user
        """
        try:
            # Get notification history from cache
            history_key = f'notification_history_{user_id}'
            history = cache.get(history_key, [])
            
            # Return limited history
            limited_history = history[-limit:] if len(history) > limit else history
            
            return {
                'success': True,
                'notifications': limited_history,
                'total_count': len(history)
            }
            
        except Exception as e:
            logger.error(f"Error getting notification history: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def mark_notification_read(self, user_id: int, notification_id: str) -> Dict[str, Any]:
        """
        Mark notification as read
        """
        try:
            # Update notification status in cache
            history_key = f'notification_history_{user_id}'
            history = cache.get(history_key, [])
            
            for notification in history:
                if notification.get('id') == notification_id:
                    notification['read'] = True
                    notification['read_at'] = timezone.now().isoformat()
                    break
            
            cache.set(history_key, history, timeout=86400)
            
            return {
                'success': True,
                'message': 'Notification marked as read'
            }
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return {'success': False, 'error': str(e)}
