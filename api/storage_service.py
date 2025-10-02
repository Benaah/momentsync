import os
import boto3
import hashlib
import mimetypes
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.files.storage import default_storage
from botocore.exceptions import ClientError
import logging
from PIL import Image
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class CloudStorageService:
    """
    Enhanced cloud storage service with modern image formats and CDN optimization
    """
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.environ.get('AWS_S3_BUCKET', 'momentsync-media')
        self.cdn_url = os.environ.get('CDN_URL', f'https://{self.bucket_name}.s3.amazonaws.com')
        
        # CloudFront distribution for global CDN
        self.cloudfront_distribution = os.environ.get('CLOUDFRONT_DISTRIBUTION')
        if self.cloudfront_distribution:
            self.cdn_url = f'https://{self.cloudfront_distribution}.cloudfront.net'
    
    async def upload_media(self, file_data: bytes, file_name: str, 
                          content_type: str, folder: str = 'media') -> Dict[str, Any]:
        """
        Upload media file with optimized storage and multiple format generation
        """
        try:
            # Generate unique file ID
            file_id = hashlib.md5(file_data).hexdigest()
            
            # Determine file type
            file_type = content_type.split('/')[0]
            
            # Upload original file
            original_key = f"{folder}/{file_type}s/{file_id}_{file_name}"
            original_url = await self._upload_to_s3(file_data, original_key, content_type)
            
            result = {
                'success': True,
                'file_id': file_id,
                'original_url': original_url,
                'cdn_url': f"{self.cdn_url}/{original_key}",
                'file_size': len(file_data),
                'content_type': content_type
            }
            
            # Generate optimized versions based on file type
            if file_type == 'image':
                optimized_versions = await self._generate_image_versions(file_data, file_id, file_name)
                result.update(optimized_versions)
            elif file_type == 'video':
                # For videos, we'll rely on FFmpeg processing
                result['processing_required'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error uploading media: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _upload_to_s3(self, file_data: bytes, key: str, content_type: str) -> str:
        """
        Upload file to S3 with optimized settings
        """
        try:
            # S3 upload parameters for optimization
            extra_args = {
                'ContentType': content_type,
                'CacheControl': 'max-age=31536000',  # 1 year cache
                'Metadata': {
                    'uploaded-by': 'momentsync',
                    'version': '2.0'
                }
            }
            
            # Add compression for text-based files
            if content_type.startswith('text/') or content_type in ['application/json', 'application/javascript']:
                extra_args['ContentEncoding'] = 'gzip'
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_data,
                **extra_args
            )
            
            return f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
            
        except ClientError as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise
    
    async def _generate_image_versions(self, file_data: bytes, file_id: str, 
                                     file_name: str) -> Dict[str, Any]:
        """
        Generate multiple optimized image versions
        """
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(file_data))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            versions = {}
            
            # Generate different sizes
            sizes = {
                'thumbnail': (300, 300),
                'medium': (800, 600),
                'large': (1920, 1080),
                'mobile': (720, 1280)
            }
            
            for size_name, dimensions in sizes.items():
                # Resize image
                resized = image.copy()
                resized.thumbnail(dimensions, Image.Resampling.LANCZOS)
                
                # Generate JPEG version
                jpeg_data = await self._image_to_bytes(resized, 'JPEG', quality=85)
                jpeg_key = f"images/{size_name}/{file_id}_{file_name}.jpg"
                jpeg_url = await self._upload_to_s3(jpeg_data, jpeg_key, 'image/jpeg')
                
                # Generate WebP version
                webp_data = await self._image_to_bytes(resized, 'WebP', quality=85)
                webp_key = f"images/{size_name}/webp/{file_id}_{file_name}.webp"
                webp_url = await self._upload_to_s3(webp_data, webp_key, 'image/webp')
                
                # Generate AVIF version (if supported)
                try:
                    avif_data = await self._image_to_bytes(resized, 'AVIF', quality=85)
                    avif_key = f"images/{size_name}/avif/{file_id}_{file_name}.avif"
                    avif_url = await self._upload_to_s3(avif_data, avif_key, 'image/avif')
                except Exception:
                    avif_url = None
                
                versions[size_name] = {
                    'jpeg': {
                        'url': jpeg_url,
                        'cdn_url': f"{self.cdn_url}/{jpeg_key}",
                        'size': len(jpeg_data)
                    },
                    'webp': {
                        'url': webp_url,
                        'cdn_url': f"{self.cdn_url}/{webp_key}",
                        'size': len(webp_data)
                    }
                }
                
                if avif_url:
                    versions[size_name]['avif'] = {
                        'url': avif_url,
                        'cdn_url': f"{self.cdn_url}/{avif_key}",
                        'size': len(avif_data)
                    }
            
            # Generate blur placeholder
            blur_data = await self._generate_blur_placeholder(image)
            blur_key = f"images/blur/{file_id}_{file_name}.jpg"
            blur_url = await self._upload_to_s3(blur_data, blur_key, 'image/jpeg')
            
            versions['blur'] = {
                'url': blur_url,
                'cdn_url': f"{self.cdn_url}/{blur_key}",
                'size': len(blur_data)
            }
            
            return versions
            
        except Exception as e:
            logger.error(f"Error generating image versions: {str(e)}")
            return {}
    
    async def _image_to_bytes(self, image: Image.Image, format: str, **kwargs) -> bytes:
        """
        Convert PIL Image to bytes with specified format
        """
        buffer = io.BytesIO()
        image.save(buffer, format=format, **kwargs)
        return buffer.getvalue()
    
    async def _generate_blur_placeholder(self, image: Image.Image) -> bytes:
        """
        Generate low-quality blur placeholder for lazy loading
        """
        # Resize to very small size
        small = image.copy()
        small.thumbnail((20, 20), Image.Resampling.LANCZOS)
        
        # Apply blur
        from PIL import ImageFilter
        blurred = small.filter(ImageFilter.GaussianBlur(radius=2))
        
        # Convert to bytes
        return await self._image_to_bytes(blurred, 'JPEG', quality=60)
    
    async def delete_media(self, file_id: str, file_type: str) -> bool:
        """
        Delete media file and all its versions
        """
        try:
            # List all objects with the file_id prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"images/{file_id}"
            )
            
            # Delete all versions
            if 'Contents' in response:
                objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting media: {str(e)}")
            return False
    
    async def get_media_info(self, file_id: str) -> Dict[str, Any]:
        """
        Get information about stored media
        """
        try:
            # List all objects with the file_id prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"images/{file_id}"
            )
            
            if 'Contents' not in response:
                return {'error': 'Media not found'}
            
            info = {
                'file_id': file_id,
                'versions': {},
                'total_size': 0,
                'total_files': len(response['Contents'])
            }
            
            for obj in response['Contents']:
                key = obj['Key']
                size = obj['Size']
                last_modified = obj['LastModified']
                
                # Parse version from key
                parts = key.split('/')
                if len(parts) >= 3:
                    version = parts[1]  # thumbnail, medium, large, etc.
                    format_type = parts[2] if len(parts) > 2 else 'original'
                    
                    if version not in info['versions']:
                        info['versions'][version] = {}
                    
                    info['versions'][version][format_type] = {
                        'key': key,
                        'size': size,
                        'last_modified': last_modified,
                        'url': f"https://{self.bucket_name}.s3.amazonaws.com/{key}",
                        'cdn_url': f"{self.cdn_url}/{key}"
                    }
                    
                    info['total_size'] += size
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting media info: {str(e)}")
            return {'error': str(e)}
    
    async def generate_signed_url(self, key: str, expiration: int = 3600) -> str:
        """
        Generate a signed URL for private access
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Error generating signed URL: {str(e)}")
            return None
    
    async def setup_cdn_invalidation(self, keys: List[str]) -> bool:
        """
        Invalidate CDN cache for specific files
        """
        if not self.cloudfront_distribution:
            return False
        
        try:
            cloudfront = boto3.client('cloudfront')
            
            # Create invalidation paths
            paths = [f"/{key}" for key in keys]
            
            response = cloudfront.create_invalidation(
                DistributionId=self.cloudfront_distribution,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': f"momentsync-{hashlib.md5(str(keys).encode()).hexdigest()}"
                }
            )
            
            logger.info(f"CDN invalidation created: {response['Invalidation']['Id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating CDN invalidation: {str(e)}")
            return False
    
    async def optimize_storage(self) -> Dict[str, Any]:
        """
        Optimize storage by cleaning up old files and compressing existing ones
        """
        try:
            # List all objects in the bucket
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                return {'message': 'No files to optimize'}
            
            optimization_stats = {
                'total_files': len(response['Contents']),
                'total_size': sum(obj['Size'] for obj in response['Contents']),
                'optimized_files': 0,
                'space_saved': 0
            }
            
            # Group files by file_id
            files_by_id = {}
            for obj in response['Contents']:
                key = obj['Key']
                parts = key.split('/')
                if len(parts) >= 3:
                    file_id = parts[2].split('_')[0]  # Extract file_id from filename
                    if file_id not in files_by_id:
                        files_by_id[file_id] = []
                    files_by_id[file_id].append(obj)
            
            # Optimize each file group
            for file_id, objects in files_by_id.items():
                # Find the original file
                original_obj = None
                for obj in objects:
                    if not any(size in obj['Key'] for size in ['thumbnail', 'medium', 'large', 'blur']):
                        original_obj = obj
                        break
                
                if original_obj:
                    # Download and re-optimize original
                    try:
                        response = self.s3_client.get_object(
                            Bucket=self.bucket_name,
                            Key=original_obj['Key']
                        )
                        file_data = response['Body'].read()
                        
                        # Re-upload with better compression
                        optimized_data = await self._optimize_file_data(file_data, original_obj['Key'])
                        
                        if len(optimized_data) < len(file_data):
                            # Upload optimized version
                            await self._upload_to_s3(
                                optimized_data, 
                                original_obj['Key'], 
                                response['ContentType']
                            )
                            
                            optimization_stats['optimized_files'] += 1
                            optimization_stats['space_saved'] += len(file_data) - len(optimized_data)
                            
                    except Exception as e:
                        logger.error(f"Error optimizing file {file_id}: {str(e)}")
            
            return optimization_stats
            
        except Exception as e:
            logger.error(f"Error optimizing storage: {str(e)}")
            return {'error': str(e)}
    
    async def _optimize_file_data(self, file_data: bytes, key: str) -> bytes:
        """
        Optimize file data based on file type
        """
        try:
            if key.endswith(('.jpg', '.jpeg')):
                # Optimize JPEG
                image = Image.open(io.BytesIO(file_data))
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=85, optimize=True)
                return buffer.getvalue()
            
            elif key.endswith('.png'):
                # Optimize PNG
                image = Image.open(io.BytesIO(file_data))
                buffer = io.BytesIO()
                image.save(buffer, format='PNG', optimize=True)
                return buffer.getvalue()
            
            else:
                # Return original data for other formats
                return file_data
                
        except Exception as e:
            logger.error(f"Error optimizing file data: {str(e)}")
            return file_data


class CDNOptimizer:
    """
    CDN optimization service for better performance
    """
    
    def __init__(self):
        self.cloudfront = boto3.client('cloudfront')
        self.distribution_id = os.environ.get('CLOUDFRONT_DISTRIBUTION')
    
    async def create_optimized_distribution(self) -> Dict[str, Any]:
        """
        Create an optimized CloudFront distribution
        """
        try:
            distribution_config = {
                'CallerReference': f'momentsync-{hashlib.md5(str(os.urandom(16)).encode()).hexdigest()}',
                'Comment': 'MomentSync Media Distribution',
                'DefaultCacheBehavior': {
                    'TargetOriginId': 'S3-momentsync-media',
                    'ViewerProtocolPolicy': 'redirect-to-https',
                    'TrustedSigners': {
                        'Enabled': False,
                        'Quantity': 0
                    },
                    'ForwardedValues': {
                        'QueryString': False,
                        'Cookies': {'Forward': 'none'}
                    },
                    'MinTTL': 0,
                    'DefaultTTL': 86400,  # 1 day
                    'MaxTTL': 31536000,   # 1 year
                    'Compress': True
                },
                'Origins': {
                    'Quantity': 1,
                    'Items': [{
                        'Id': 'S3-momentsync-media',
                        'DomainName': f'{os.environ.get("AWS_S3_BUCKET")}.s3.amazonaws.com',
                        'S3OriginConfig': {
                            'OriginAccessIdentity': ''
                        }
                    }]
                },
                'Enabled': True,
                'PriceClass': 'PriceClass_100'  # Use only North America and Europe
            }
            
            response = self.cloudfront.create_distribution(
                DistributionConfig=distribution_config
            )
            
            return {
                'success': True,
                'distribution_id': response['Distribution']['Id'],
                'domain_name': response['Distribution']['DomainName']
            }
            
        except Exception as e:
            logger.error(f"Error creating CloudFront distribution: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def update_cache_behavior(self, path_pattern: str, ttl: int) -> bool:
        """
        Update cache behavior for specific path patterns
        """
        try:
            if not self.distribution_id:
                return False
            
            # Get current distribution config
            response = self.cloudfront.get_distribution_config(Id=self.distribution_id)
            config = response['DistributionConfig']
            
            # Add new cache behavior
            new_behavior = {
                'PathPattern': path_pattern,
                'TargetOriginId': 'S3-momentsync-media',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                },
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'}
                },
                'MinTTL': 0,
                'DefaultTTL': ttl,
                'MaxTTL': ttl,
                'Compress': True
            }
            
            # Add to existing behaviors
            if 'CacheBehaviors' not in config:
                config['CacheBehaviors'] = {'Quantity': 0, 'Items': []}
            
            config['CacheBehaviors']['Items'].append(new_behavior)
            config['CacheBehaviors']['Quantity'] += 1
            
            # Update distribution
            self.cloudfront.update_distribution(
                Id=self.distribution_id,
                DistributionConfig=config,
                IfMatch=response['ETag']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating cache behavior: {str(e)}")
            return False
