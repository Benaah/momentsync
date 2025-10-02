import os
import json
import base64
import requests
import logging
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
import asyncio
import aiohttp
from PIL import Image
import io
import numpy as np
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class AIService:
    """
    AI-powered features service for MomentSync
    Includes automatic image tagging, content moderation, and smart compression
    """
    
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.google_vision_api_key = os.environ.get('GOOGLE_VISION_API_KEY')
        self.aws_rekognition_region = os.environ.get('AWS_REKOGNITION_REGION', 'us-east-1')
        self.aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        # Initialize AWS Rekognition client
        if self.aws_access_key_id and self.aws_secret_access_key:
            import boto3
            self.rekognition = boto3.client(
                'rekognition',
                region_name=self.aws_rekognition_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
        else:
            self.rekognition = None
    
    async def analyze_image(self, image_data: bytes, image_path: str = None) -> Dict[str, Any]:
        """
        Comprehensive image analysis using multiple AI services
        """
        try:
            # Run multiple analysis tasks in parallel
            tasks = [
                self._detect_objects(image_data),
                self._detect_faces(image_data),
                self._detect_text(image_data),
                self._moderate_content(image_data),
                self._generate_description(image_data),
                self._extract_colors(image_data),
                self._detect_scene(image_data)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            analysis = {
                'success': True,
                'objects': results[0] if not isinstance(results[0], Exception) else [],
                'faces': results[1] if not isinstance(results[1], Exception) else [],
                'text': results[2] if not isinstance(results[2], Exception) else [],
                'moderation': results[3] if not isinstance(results[3], Exception) else {},
                'description': results[4] if not isinstance(results[4], Exception) else '',
                'colors': results[5] if not isinstance(results[5], Exception) else [],
                'scene': results[6] if not isinstance(results[6], Exception) else '',
                'metadata': await self._extract_metadata(image_data)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _detect_objects(self, image_data: bytes) -> List[Dict[str, Any]]:
        """
        Detect objects in image using AWS Rekognition
        """
        try:
            if not self.rekognition:
                return []
            
            response = self.rekognition.detect_labels(
                Image={'Bytes': image_data},
                MaxLabels=20,
                MinConfidence=70.0
            )
            
            objects = []
            for label in response['Labels']:
                objects.append({
                    'name': label['Name'],
                    'confidence': label['Confidence'],
                    'instances': len(label.get('Instances', [])),
                    'parents': [parent['Name'] for parent in label.get('Parents', [])]
                })
            
            return objects
            
        except Exception as e:
            logger.error(f"Error detecting objects: {str(e)}")
            return []
    
    async def _detect_faces(self, image_data: bytes) -> List[Dict[str, Any]]:
        """
        Detect faces in image using AWS Rekognition
        """
        try:
            if not self.rekognition:
                return []
            
            response = self.rekognition.detect_faces(
                Image={'Bytes': image_data},
                Attributes=['ALL']
            )
            
            faces = []
            for face in response['FaceDetails']:
                faces.append({
                    'confidence': face['Confidence'],
                    'emotions': [emotion['Type'] for emotion in face['Emotions'] if emotion['Confidence'] > 50],
                    'age_range': {
                        'low': face['AgeRange']['Low'],
                        'high': face['AgeRange']['High']
                    },
                    'gender': face['Gender']['Value'] if face['Gender']['Confidence'] > 70 else 'Unknown',
                    'smile': face['Smile']['Value'] if face['Smile']['Confidence'] > 70 else False,
                    'eyes_open': face['EyesOpen']['Value'] if face['EyesOpen']['Confidence'] > 70 else False,
                    'mouth_open': face['MouthOpen']['Value'] if face['MouthOpen']['Confidence'] > 70 else False,
                    'bounding_box': face['BoundingBox']
                })
            
            return faces
            
        except Exception as e:
            logger.error(f"Error detecting faces: {str(e)}")
            return []
    
    async def _detect_text(self, image_data: bytes) -> List[Dict[str, Any]]:
        """
        Detect text in image using AWS Rekognition
        """
        try:
            if not self.rekognition:
                return []
            
            response = self.rekognition.detect_text(
                Image={'Bytes': image_data}
            )
            
            text_objects = []
            for text in response['TextDetections']:
                if text['Type'] == 'LINE':
                    text_objects.append({
                        'text': text['DetectedText'],
                        'confidence': text['Confidence'],
                        'bounding_box': text['Geometry']['BoundingBox']
                    })
            
            return text_objects
            
        except Exception as e:
            logger.error(f"Error detecting text: {str(e)}")
            return []
    
    async def _moderate_content(self, image_data: bytes) -> Dict[str, Any]:
        """
        Moderate content for inappropriate material
        """
        try:
            if not self.rekognition:
                return {'safe': True, 'confidence': 100}
            
            response = self.rekognition.detect_moderation_labels(
                Image={'Bytes': image_data},
                MinConfidence=50.0
            )
            
            moderation = {
                'safe': len(response['ModerationLabels']) == 0,
                'confidence': 100,
                'labels': []
            }
            
            if response['ModerationLabels']:
                moderation['confidence'] = min(label['Confidence'] for label in response['ModerationLabels'])
                moderation['labels'] = [
                    {
                        'name': label['Name'],
                        'confidence': label['Confidence'],
                        'parent_name': label.get('ParentName', '')
                    }
                    for label in response['ModerationLabels']
                ]
            
            return moderation
            
        except Exception as e:
            logger.error(f"Error moderating content: {str(e)}")
            return {'safe': True, 'confidence': 100}
    
    async def _generate_description(self, image_data: bytes) -> str:
        """
        Generate natural language description of the image
        """
        try:
            if not self.openai_api_key:
                return ''
            
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-4-vision-preview',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': 'Describe this image in detail, including objects, people, activities, and setting. Be concise but informative.'
                            },
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/jpeg;base64,{image_base64}'
                                }
                            }
                        ]
                    }
                ],
                'max_tokens': 300
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        logger.error(f"OpenAI API error: {response.status}")
                        return ''
            
        except Exception as e:
            logger.error(f"Error generating description: {str(e)}")
            return ''
    
    async def _extract_colors(self, image_data: bytes) -> List[Dict[str, Any]]:
        """
        Extract dominant colors from image
        """
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))
            
            # Resize for faster processing
            image.thumbnail((150, 150))
            
            # Convert to RGB
            image = image.convert('RGB')
            
            # Get color data
            colors = image.getcolors(maxcolors=256*256*256)
            
            if not colors:
                return []
            
            # Sort by frequency
            colors.sort(key=lambda x: x[0], reverse=True)
            
            # Extract top 10 colors
            dominant_colors = []
            for count, color in colors[:10]:
                # Convert RGB to hex
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                
                # Calculate percentage
                percentage = (count / (image.width * image.height)) * 100
                
                dominant_colors.append({
                    'hex': hex_color,
                    'rgb': color,
                    'percentage': round(percentage, 2)
                })
            
            return dominant_colors
            
        except Exception as e:
            logger.error(f"Error extracting colors: {str(e)}")
            return []
    
    async def _detect_scene(self, image_data: bytes) -> str:
        """
        Detect scene type (indoor/outdoor, day/night, etc.)
        """
        try:
            if not self.openai_api_key:
                return ''
            
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-4-vision-preview',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': 'Analyze this image and determine the scene type. Respond with one of: indoor, outdoor, urban, nature, beach, mountain, city, home, office, restaurant, park, or other. Also indicate if it\'s day or night.'
                            },
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/jpeg;base64,{image_base64}'
                                }
                            }
                        ]
                    }
                ],
                'max_tokens': 50
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        logger.error(f"OpenAI API error: {response.status}")
                        return ''
            
        except Exception as e:
            logger.error(f"Error detecting scene: {str(e)}")
            return ''
    
    async def _extract_metadata(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract technical metadata from image
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            metadata = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height,
                'has_transparency': image.mode in ('RGBA', 'LA', 'P'),
                'file_size': len(image_data)
            }
            
            # Extract EXIF data if available
            if hasattr(image, '_getexif') and image._getexif():
                exif = image._getexif()
                metadata['exif'] = {
                    'camera_make': exif.get(271, ''),
                    'camera_model': exif.get(272, ''),
                    'date_taken': exif.get(306, ''),
                    'orientation': exif.get(274, 1)
                }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {}
    
    async def smart_compress(self, image_data: bytes, target_size: int = 500000) -> bytes:
        """
        Intelligently compress image while maintaining quality
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Calculate current size
            current_size = len(image_data)
            
            if current_size <= target_size:
                return image_data
            
            # Calculate compression ratio
            compression_ratio = target_size / current_size
            
            # Determine quality based on compression ratio
            if compression_ratio > 0.8:
                quality = 85
            elif compression_ratio > 0.6:
                quality = 75
            elif compression_ratio > 0.4:
                quality = 65
            else:
                quality = 55
            
            # Compress image
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            compressed_data = buffer.getvalue()
            
            # If still too large, resize image
            if len(compressed_data) > target_size:
                # Calculate new dimensions
                resize_factor = (target_size / len(compressed_data)) ** 0.5
                new_width = int(image.width * resize_factor)
                new_height = int(image.height * resize_factor)
                
                # Resize image
                resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Compress again
                buffer = io.BytesIO()
                resized.save(buffer, format='JPEG', quality=quality, optimize=True)
                compressed_data = buffer.getvalue()
            
            return compressed_data
            
        except Exception as e:
            logger.error(f"Error compressing image: {str(e)}")
            return image_data
    
    async def generate_tags(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate relevant tags from image analysis
        """
        try:
            tags = []
            
            # Add object tags
            for obj in analysis.get('objects', []):
                if obj['confidence'] > 80:
                    tags.append(obj['name'].lower())
            
            # Add emotion tags
            for face in analysis.get('faces', []):
                for emotion in face.get('emotions', []):
                    tags.append(f"emotion_{emotion.lower()}")
            
            # Add scene tags
            scene = analysis.get('scene', '').lower()
            if scene:
                tags.append(f"scene_{scene}")
            
            # Add color tags
            colors = analysis.get('colors', [])
            if colors:
                dominant_color = colors[0]['hex']
                tags.append(f"color_{dominant_color}")
            
            # Add technical tags
            metadata = analysis.get('metadata', {})
            if metadata.get('has_transparency'):
                tags.append('transparent')
            
            # Remove duplicates and return
            return list(set(tags))
            
        except Exception as e:
            logger.error(f"Error generating tags: {str(e)}")
            return []
    
    async def moderate_text(self, text: str) -> Dict[str, Any]:
        """
        Moderate text content for inappropriate material
        """
        try:
            if not self.openai_api_key:
                return {'safe': True, 'confidence': 100}
            
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a content moderator. Analyze the following text for inappropriate content, hate speech, or harmful material. Respond with a JSON object containing "safe" (boolean) and "confidence" (0-100) and "reason" (string).'
                    },
                    {
                        'role': 'user',
                        'content': text
                    }
                ],
                'max_tokens': 100
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            return {'safe': True, 'confidence': 100, 'reason': 'Unable to parse moderation result'}
                    else:
                        logger.error(f"OpenAI API error: {response.status}")
                        return {'safe': True, 'confidence': 100}
            
        except Exception as e:
            logger.error(f"Error moderating text: {str(e)}")
            return {'safe': True, 'confidence': 100}
    
    async def generate_alt_text(self, analysis: Dict[str, Any]) -> str:
        """
        Generate accessible alt text for images
        """
        try:
            description = analysis.get('description', '')
            objects = analysis.get('objects', [])
            faces = analysis.get('faces', [])
            scene = analysis.get('scene', '')
            
            # Build alt text
            alt_parts = []
            
            if faces:
                face_count = len(faces)
                if face_count == 1:
                    alt_parts.append("A person")
                else:
                    alt_parts.append(f"{face_count} people")
            
            if objects:
                top_objects = [obj['name'] for obj in objects[:3] if obj['confidence'] > 80]
                if top_objects:
                    alt_parts.append(f"featuring {', '.join(top_objects)}")
            
            if scene:
                alt_parts.append(f"in a {scene} setting")
            
            if description and not alt_parts:
                alt_parts.append(description)
            
            alt_text = '. '.join(alt_parts) if alt_parts else "An image"
            
            # Ensure alt text is not too long
            if len(alt_text) > 125:
                alt_text = alt_text[:122] + "..."
            
            return alt_text
            
        except Exception as e:
            logger.error(f"Error generating alt text: {str(e)}")
            return "An image"
