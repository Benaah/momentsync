import os
import tempfile
import asyncio
import subprocess
import logging
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import ffmpeg
import imageio
from PIL import Image
import cv2
import numpy as np
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class FFmpegService:
    """
    Comprehensive FFmpeg service for media processing
    """
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.environ.get('AWS_S3_BUCKET', 'momentsync-media')
        
        # FFmpeg configuration
        self.ffmpeg_path = os.environ.get('FFMPEG_PATH', 'ffmpeg')
        self.ffprobe_path = os.environ.get('FFPROBE_PATH', 'ffprobe')
        
        # Video processing presets
        self.video_presets = {
            'mobile': {
                'width': 720,
                'height': 1280,
                'bitrate': '1M',
                'crf': 28,
                'preset': 'fast'
            },
            'desktop': {
                'width': 1920,
                'height': 1080,
                'bitrate': '3M',
                'crf': 23,
                'preset': 'medium'
            },
            'thumbnail': {
                'width': 300,
                'height': 300,
                'bitrate': '500k',
                'crf': 30,
                'preset': 'ultrafast'
            }
        }
    
    async def process_media(self, file_path: str, file_type: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main media processing function that routes to appropriate handlers
        """
        try:
            if file_type.startswith('video/'):
                return await self.process_video(file_path, options or {})
            elif file_type.startswith('image/'):
                return await self.process_image(file_path, options or {})
            elif file_type.startswith('audio/'):
                return await self.process_audio(file_path, options or {})
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error processing media: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def process_video(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process video files with FFmpeg
        """
        try:
            # Get video metadata
            metadata = await self.get_video_metadata(file_path)
            
            # Generate different quality versions
            results = {}
            
            # Original quality (compressed)
            original_result = await self.compress_video(file_path, 'original', options)
            results['original'] = original_result
            
            # Mobile quality
            mobile_result = await self.compress_video(file_path, 'mobile', options)
            results['mobile'] = mobile_result
            
            # Desktop quality
            desktop_result = await self.compress_video(file_path, 'desktop', options)
            results['desktop'] = desktop_result
            
            # Generate thumbnails
            thumbnails = await self.generate_video_thumbnails(file_path, options)
            results['thumbnails'] = thumbnails
            
            # Extract audio if needed
            if options.get('extract_audio', False):
                audio_result = await self.extract_audio(file_path, options)
                results['audio'] = audio_result
            
            # Generate GIF preview
            if options.get('generate_gif', False):
                gif_result = await self.generate_gif_preview(file_path, options)
                results['gif'] = gif_result
            
            return {
                'success': True,
                'results': results,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def process_image(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process image files with FFmpeg and PIL
        """
        try:
            # Get image metadata
            metadata = await self.get_image_metadata(file_path)
            
            results = {}
            
            # Generate different sizes
            sizes = options.get('sizes', ['thumbnail', 'medium', 'large'])
            
            for size in sizes:
                size_result = await self.resize_image(file_path, size, options)
                results[size] = size_result
            
            # Convert to modern formats
            if options.get('convert_formats', True):
                webp_result = await self.convert_to_webp(file_path, options)
                results['webp'] = webp_result
                
                avif_result = await self.convert_to_avif(file_path, options)
                results['avif'] = avif_result
            
            # Generate blur placeholder
            if options.get('generate_blur', True):
                blur_result = await self.generate_blur_placeholder(file_path, options)
                results['blur'] = blur_result
            
            return {
                'success': True,
                'results': results,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def process_audio(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process audio files with FFmpeg
        """
        try:
            # Get audio metadata
            metadata = await self.get_audio_metadata(file_path)
            
            results = {}
            
            # Compress audio
            compressed_result = await self.compress_audio(file_path, options)
            results['compressed'] = compressed_result
            
            # Extract waveform data
            if options.get('extract_waveform', True):
                waveform_result = await self.extract_waveform(file_path, options)
                results['waveform'] = waveform_result
            
            return {
                'success': True,
                'results': results,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def compress_video(self, file_path: str, quality: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress video with FFmpeg
        """
        try:
            preset = self.video_presets.get(quality, self.video_presets['desktop'])
            
            # Create output filename
            input_path = Path(file_path)
            output_filename = f"{input_path.stem}_{quality}.mp4"
            output_path = tempfile.mktemp(suffix=f"_{output_filename}")
            
            # FFmpeg command
            stream = ffmpeg.input(file_path)
            
            # Apply filters
            if quality != 'original':
                stream = stream.filter('scale', preset['width'], preset['height'])
            
            # Set encoding parameters
            stream = ffmpeg.output(
                stream,
                output_path,
                vcodec='libx264',
                preset=preset['preset'],
                crf=preset['crf'],
                acodec='aac',
                audio_bitrate='128k',
                movflags='faststart'  # Optimize for web streaming
            )
            
            # Run FFmpeg
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            # Upload to S3
            s3_key = f"videos/{quality}/{output_filename}"
            upload_result = await self.upload_to_s3(output_path, s3_key)
            
            # Clean up temp file
            os.unlink(output_path)
            
            return {
                'success': True,
                'url': upload_result['url'],
                'file_size': upload_result['file_size'],
                'quality': quality
            }
            
        except Exception as e:
            logger.error(f"Error compressing video: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_video_thumbnails(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate video thumbnails at different timestamps
        """
        try:
            # Get video duration
            metadata = await self.get_video_metadata(file_path)
            duration = float(metadata.get('duration', 0))
            
            # Generate thumbnails at different timestamps
            timestamps = [0, duration * 0.25, duration * 0.5, duration * 0.75, duration - 1]
            thumbnails = []
            
            for i, timestamp in enumerate(timestamps):
                if timestamp < 0:
                    timestamp = 0
                
                # Create thumbnail filename
                input_path = Path(file_path)
                thumbnail_filename = f"{input_path.stem}_thumb_{i}.jpg"
                thumbnail_path = tempfile.mktemp(suffix=f"_{thumbnail_filename}")
                
                # Generate thumbnail
                stream = ffmpeg.input(file_path, ss=timestamp)
                stream = ffmpeg.output(
                    stream,
                    thumbnail_path,
                    vframes=1,
                    format='image2',
                    vcodec='mjpeg'
                )
                
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                
                # Upload to S3
                s3_key = f"thumbnails/{thumbnail_filename}"
                upload_result = await self.upload_to_s3(thumbnail_path, s3_key)
                
                thumbnails.append({
                    'timestamp': timestamp,
                    'url': upload_result['url'],
                    'index': i
                })
                
                # Clean up
                os.unlink(thumbnail_path)
            
            return {
                'success': True,
                'thumbnails': thumbnails
            }
            
        except Exception as e:
            logger.error(f"Error generating video thumbnails: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def resize_image(self, file_path: str, size: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resize image to different sizes
        """
        try:
            # Define size presets
            size_presets = {
                'thumbnail': (300, 300),
                'medium': (800, 600),
                'large': (1920, 1080),
                'original': None
            }
            
            dimensions = size_presets.get(size)
            if not dimensions:
                return {'success': False, 'error': f'Unknown size: {size}'}
            
            # Open image
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize image
                if dimensions:
                    img.thumbnail(dimensions, Image.Resampling.LANCZOS)
                
                # Create output filename
                input_path = Path(file_path)
                output_filename = f"{input_path.stem}_{size}.jpg"
                output_path = tempfile.mktemp(suffix=f"_{output_filename}")
                
                # Save image
                img.save(output_path, 'JPEG', quality=85, optimize=True)
                
                # Upload to S3
                s3_key = f"images/{size}/{output_filename}"
                upload_result = await self.upload_to_s3(output_path, s3_key)
                
                # Clean up
                os.unlink(output_path)
                
                return {
                    'success': True,
                    'url': upload_result['url'],
                    'file_size': upload_result['file_size'],
                    'dimensions': img.size,
                    'size': size
                }
                
        except Exception as e:
            logger.error(f"Error resizing image: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def convert_to_webp(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert image to WebP format
        """
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create output filename
                input_path = Path(file_path)
                output_filename = f"{input_path.stem}.webp"
                output_path = tempfile.mktemp(suffix=f"_{output_filename}")
                
                # Save as WebP
                img.save(output_path, 'WebP', quality=85, optimize=True)
                
                # Upload to S3
                s3_key = f"images/webp/{output_filename}"
                upload_result = await self.upload_to_s3(output_path, s3_key)
                
                # Clean up
                os.unlink(output_path)
                
                return {
                    'success': True,
                    'url': upload_result['url'],
                    'file_size': upload_result['file_size'],
                    'format': 'webp'
                }
                
        except Exception as e:
            logger.error(f"Error converting to WebP: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def convert_to_avif(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert image to AVIF format using FFmpeg
        """
        try:
            input_path = Path(file_path)
            output_filename = f"{input_path.stem}.avif"
            output_path = tempfile.mktemp(suffix=f"_{output_filename}")
            
            # Use FFmpeg to convert to AVIF
            stream = ffmpeg.input(file_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                vcodec='libaom-av1',
                crf=30,
                preset='medium'
            )
            
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            # Upload to S3
            s3_key = f"images/avif/{output_filename}"
            upload_result = await self.upload_to_s3(output_path, s3_key)
            
            # Clean up
            os.unlink(output_path)
            
            return {
                'success': True,
                'url': upload_result['url'],
                'file_size': upload_result['file_size'],
                'format': 'avif'
            }
            
        except Exception as e:
            logger.error(f"Error converting to AVIF: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_blur_placeholder(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate blur placeholder for lazy loading
        """
        try:
            with Image.open(file_path) as img:
                # Resize to small size
                img.thumbnail((20, 20), Image.Resampling.LANCZOS)
                
                # Apply blur
                img = img.filter(ImageFilter.GaussianBlur(radius=2))
                
                # Create output filename
                input_path = Path(file_path)
                output_filename = f"{input_path.stem}_blur.jpg"
                output_path = tempfile.mktemp(suffix=f"_{output_filename}")
                
                # Save image
                img.save(output_path, 'JPEG', quality=60)
                
                # Upload to S3
                s3_key = f"images/blur/{output_filename}"
                upload_result = await self.upload_to_s3(output_path, s3_key)
                
                # Clean up
                os.unlink(output_path)
                
                return {
                    'success': True,
                    'url': upload_result['url'],
                    'file_size': upload_result['file_size'],
                    'type': 'blur_placeholder'
                }
                
        except Exception as e:
            logger.error(f"Error generating blur placeholder: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def extract_audio(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract audio from video
        """
        try:
            input_path = Path(file_path)
            output_filename = f"{input_path.stem}.mp3"
            output_path = tempfile.mktemp(suffix=f"_{output_filename}")
            
            # Extract audio using FFmpeg
            stream = ffmpeg.input(file_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                acodec='mp3',
                audio_bitrate='128k'
            )
            
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            # Upload to S3
            s3_key = f"audio/{output_filename}"
            upload_result = await self.upload_to_s3(output_path, s3_key)
            
            # Clean up
            os.unlink(output_path)
            
            return {
                'success': True,
                'url': upload_result['url'],
                'file_size': upload_result['file_size'],
                'format': 'mp3'
            }
            
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def generate_gif_preview(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate GIF preview from video
        """
        try:
            input_path = Path(file_path)
            output_filename = f"{input_path.stem}.gif"
            output_path = tempfile.mktemp(suffix=f"_{output_filename}")
            
            # Generate GIF using FFmpeg
            stream = ffmpeg.input(file_path, ss=0, t=3)  # First 3 seconds
            stream = ffmpeg.output(
                stream,
                output_path,
                vf='fps=10,scale=320:-1:flags=lanczos',
                format='gif'
            )
            
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            # Upload to S3
            s3_key = f"gifs/{output_filename}"
            upload_result = await self.upload_to_s3(output_path, s3_key)
            
            # Clean up
            os.unlink(output_path)
            
            return {
                'success': True,
                'url': upload_result['url'],
                'file_size': upload_result['file_size'],
                'format': 'gif'
            }
            
        except Exception as e:
            logger.error(f"Error generating GIF: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get video metadata using FFprobe
        """
        try:
            probe = ffmpeg.probe(file_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            return {
                'duration': float(probe['format']['duration']),
                'size': int(probe['format']['size']),
                'bitrate': int(probe['format']['bit_rate']),
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'fps': eval(video_stream['r_frame_rate']),
                'codec': video_stream['codec_name'],
                'has_audio': audio_stream is not None
            }
        except Exception as e:
            logger.error(f"Error getting video metadata: {str(e)}")
            return {}
    
    async def get_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get image metadata using PIL
        """
        try:
            with Image.open(file_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'format': img.format,
                    'size': os.path.getsize(file_path)
                }
        except Exception as e:
            logger.error(f"Error getting image metadata: {str(e)}")
            return {}
    
    async def get_audio_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get audio metadata using FFprobe
        """
        try:
            probe = ffmpeg.probe(file_path)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            return {
                'duration': float(probe['format']['duration']),
                'size': int(probe['format']['size']),
                'bitrate': int(probe['format']['bit_rate']),
                'sample_rate': int(audio_stream['sample_rate']),
                'channels': int(audio_stream['channels']),
                'codec': audio_stream['codec_name']
            }
        except Exception as e:
            logger.error(f"Error getting audio metadata: {str(e)}")
            return {}
    
    async def upload_to_s3(self, file_path: str, s3_key: str) -> Dict[str, Any]:
        """
        Upload file to S3
        """
        try:
            file_size = os.path.getsize(file_path)
            
            with open(file_path, 'rb') as file:
                self.s3_client.upload_fileobj(
                    file,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={'ContentType': self._get_content_type(s3_key)}
                )
            
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            
            return {
                'success': True,
                'url': url,
                'file_size': file_size,
                's3_key': s3_key
            }
            
        except ClientError as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _get_content_type(self, s3_key: str) -> str:
        """
        Get content type based on file extension
        """
        ext = Path(s3_key).suffix.lower()
        content_types = {
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.avif': 'image/avif',
            '.gif': 'image/gif',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav'
        }
        return content_types.get(ext, 'application/octet-stream')
