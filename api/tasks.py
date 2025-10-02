from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from .ffmpeg_service import FFmpegService
from .services import MediaProcessingService, NotificationService
from moments.models import MediaItem, Moment, Notification
import asyncio
import os

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def process_media_async(self, media_id, file_path, file_type, options=None):
    """
    Process media file asynchronously with FFmpeg
    """
    try:
        logger.info(f"Starting media processing for {media_id}")
        
        # Initialize FFmpeg service
        ffmpeg_service = FFmpegService()
        
        # Process media
        result = asyncio.run(ffmpeg_service.process_media(file_path, file_type, options or {}))
        
        if result['success']:
            # Update MediaItem with processing results
            update_media_item(media_id, result)
            
            # Send notification
            send_processing_complete_notification(media_id)
            
            logger.info(f"Media processing completed for {media_id}")
            return result
        else:
            logger.error(f"Media processing failed for {media_id}: {result.get('error')}")
            raise Exception(result.get('error', 'Unknown error'))
            
    except Exception as exc:
        logger.error(f"Media processing error for {media_id}: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)
            logger.info(f"Retrying media processing for {media_id} in {retry_delay} seconds")
            raise self.retry(countdown=retry_delay, exc=exc)
        else:
            # Mark as failed
            mark_media_processing_failed(media_id, str(exc))
            send_processing_failed_notification(media_id, str(exc))
            raise exc


@shared_task
def generate_video_thumbnails(media_id, file_path):
    """
    Generate video thumbnails asynchronously
    """
    try:
        logger.info(f"Generating thumbnails for {media_id}")
        
        ffmpeg_service = FFmpegService()
        result = asyncio.run(ffmpeg_service.generate_video_thumbnails(file_path, {}))
        
        if result['success']:
            # Update MediaItem with thumbnail URLs
            update_media_thumbnails(media_id, result['thumbnails'])
            logger.info(f"Thumbnails generated for {media_id}")
        else:
            logger.error(f"Thumbnail generation failed for {media_id}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error generating thumbnails for {media_id}: {str(e)}")


@shared_task
def compress_video_quality(media_id, file_path, quality):
    """
    Compress video to specific quality asynchronously
    """
    try:
        logger.info(f"Compressing video {media_id} to {quality} quality")
        
        ffmpeg_service = FFmpegService()
        result = asyncio.run(ffmpeg_service.compress_video(file_path, quality, {}))
        
        if result['success']:
            # Update MediaItem with compressed video URL
            update_media_compressed_url(media_id, quality, result['url'])
            logger.info(f"Video compressed to {quality} quality for {media_id}")
        else:
            logger.error(f"Video compression failed for {media_id}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error compressing video {media_id}: {str(e)}")


@shared_task
def convert_image_formats(media_id, file_path):
    """
    Convert image to modern formats (WebP, AVIF) asynchronously
    """
    try:
        logger.info(f"Converting image formats for {media_id}")
        
        ffmpeg_service = FFmpegService()
        
        # Convert to WebP
        webp_result = asyncio.run(ffmpeg_service.convert_to_webp(file_path, {}))
        if webp_result['success']:
            update_media_format_url(media_id, 'webp', webp_result['url'])
        
        # Convert to AVIF
        avif_result = asyncio.run(ffmpeg_service.convert_to_avif(file_path, {}))
        if avif_result['success']:
            update_media_format_url(media_id, 'avif', avif_result['url'])
        
        logger.info(f"Image format conversion completed for {media_id}")
        
    except Exception as e:
        logger.error(f"Error converting image formats for {media_id}: {str(e)}")


@shared_task
def generate_blur_placeholder(media_id, file_path):
    """
    Generate blur placeholder for lazy loading
    """
    try:
        logger.info(f"Generating blur placeholder for {media_id}")
        
        ffmpeg_service = FFmpegService()
        result = asyncio.run(ffmpeg_service.generate_blur_placeholder(file_path, {}))
        
        if result['success']:
            update_media_blur_url(media_id, result['url'])
            logger.info(f"Blur placeholder generated for {media_id}")
        else:
            logger.error(f"Blur placeholder generation failed for {media_id}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error generating blur placeholder for {media_id}: {str(e)}")


@shared_task
def extract_audio_from_video(media_id, file_path):
    """
    Extract audio from video file
    """
    try:
        logger.info(f"Extracting audio from video {media_id}")
        
        ffmpeg_service = FFmpegService()
        result = asyncio.run(ffmpeg_service.extract_audio(file_path, {}))
        
        if result['success']:
            update_media_audio_url(media_id, result['url'])
            logger.info(f"Audio extracted from video {media_id}")
        else:
            logger.error(f"Audio extraction failed for {media_id}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error extracting audio from video {media_id}: {str(e)}")


@shared_task
def generate_gif_preview(media_id, file_path):
    """
    Generate GIF preview from video
    """
    try:
        logger.info(f"Generating GIF preview for {media_id}")
        
        ffmpeg_service = FFmpegService()
        result = asyncio.run(ffmpeg_service.generate_gif_preview(file_path, {}))
        
        if result['success']:
            update_media_gif_url(media_id, result['url'])
            logger.info(f"GIF preview generated for {media_id}")
        else:
            logger.error(f"GIF preview generation failed for {media_id}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error generating GIF preview for {media_id}: {str(e)}")


@shared_task
def cleanup_temp_files(file_paths):
    """
    Clean up temporary files
    """
    try:
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temp file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {str(e)}")


@shared_task
def send_processing_complete_notification(media_id):
    """
    Send notification when media processing is complete
    """
    try:
        media_item = MediaItem.objects.get(id=media_id)
        moment = media_item.moment
        
        # Create notification for all moment members
        for username in moment.allowed_usernames:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(username=username)
                
                Notification.objects.create(
                    user=user,
                    title="Media Processing Complete",
                    message=f"Your media '{media_item.file_name}' has been processed successfully.",
                    notification_type='media_upload',
                    moment=moment,
                    media_item=media_item
                )
            except User.DoesNotExist:
                continue
                
    except MediaItem.DoesNotExist:
        logger.error(f"MediaItem {media_id} not found")
    except Exception as e:
        logger.error(f"Error sending processing complete notification: {str(e)}")


@shared_task
def send_processing_failed_notification(media_id, error_message):
    """
    Send notification when media processing fails
    """
    try:
        media_item = MediaItem.objects.get(id=media_id)
        moment = media_item.moment
        
        # Create notification for the uploader
        Notification.objects.create(
            user=media_item.uploader,
            title="Media Processing Failed",
            message=f"Failed to process media '{media_item.file_name}': {error_message}",
            notification_type='system',
            moment=moment,
            media_item=media_item
        )
        
    except MediaItem.DoesNotExist:
        logger.error(f"MediaItem {media_id} not found")
    except Exception as e:
        logger.error(f"Error sending processing failed notification: {str(e)}")


# Helper functions for updating MediaItem
def update_media_item(media_id, processing_result):
    """Update MediaItem with processing results"""
    try:
        media_item = MediaItem.objects.get(id=media_id)
        
        # Update processing status
        media_item.is_processed = True
        media_item.processed_at = timezone.now()
        
        # Update with processing results
        if 'results' in processing_result:
            results = processing_result['results']
            
            # Update thumbnail URL
            if 'thumbnails' in results and results['thumbnails']['success']:
                thumbnails = results['thumbnails']['thumbnails']
                if thumbnails:
                    media_item.thumbnail_url = thumbnails[0]['url']
            
            # Update compressed URLs
            for quality in ['mobile', 'desktop', 'original']:
                if quality in results and results[quality]['success']:
                    if quality == 'original':
                        media_item.compressed_url = results[quality]['url']
                    # Store other qualities in a JSON field if needed
        
        # Update metadata
        if 'metadata' in processing_result:
            metadata = processing_result['metadata']
            if 'width' in metadata:
                media_item.width = metadata['width']
            if 'height' in metadata:
                media_item.height = metadata['height']
            if 'duration' in metadata:
                media_item.duration = metadata['duration']
        
        media_item.save()
        
    except MediaItem.DoesNotExist:
        logger.error(f"MediaItem {media_id} not found")
    except Exception as e:
        logger.error(f"Error updating MediaItem {media_id}: {str(e)}")


def update_media_thumbnails(media_id, thumbnails):
    """Update MediaItem with thumbnail URLs"""
    try:
        media_item = MediaItem.objects.get(id=media_id)
        if thumbnails:
            media_item.thumbnail_url = thumbnails[0]['url']
            media_item.save()
    except MediaItem.DoesNotExist:
        logger.error(f"MediaItem {media_id} not found")


def update_media_compressed_url(media_id, quality, url):
    """Update MediaItem with compressed video URL"""
    try:
        media_item = MediaItem.objects.get(id=media_id)
        if quality == 'original':
            media_item.compressed_url = url
            media_item.save()
    except MediaItem.DoesNotExist:
        logger.error(f"MediaItem {media_id} not found")


def update_media_format_url(media_id, format_type, url):
    """Update MediaItem with format-specific URL"""
    try:
        media_item = MediaItem.objects.get(id=media_id)
        # Store in camera_info JSON field
        if not media_item.camera_info:
            media_item.camera_info = {}
        
        media_item.camera_info[f'{format_type}_url'] = url
        media_item.save()
    except MediaItem.DoesNotExist:
        logger.error(f"MediaItem {media_id} not found")


def update_media_blur_url(media_id, url):
    """Update MediaItem with blur placeholder URL"""
    try:
        media_item = MediaItem.objects.get(id=media_id)
        if not media_item.camera_info:
            media_item.camera_info = {}
        
        media_item.camera_info['blur_url'] = url
        media_item.save()
    except MediaItem.DoesNotExist:
        logger.error(f"MediaItem {media_id} not found")


def update_media_audio_url(media_id, url):
    """Update MediaItem with audio URL"""
    try:
        media_item = MediaItem.objects.get(id=media_id)
        if not media_item.camera_info:
            media_item.camera_info = {}
        
        media_item.camera_info['audio_url'] = url
        media_item.save()
    except MediaItem.DoesNotExist:
        logger.error(f"MediaItem {media_id} not found")


def update_media_gif_url(media_id, url):
    """Update MediaItem with GIF preview URL"""
    try:
        media_item = MediaItem.objects.get(id=media_id)
        if not media_item.camera_info:
            media_item.camera_info = {}
        
        media_item.camera_info['gif_url'] = url
        media_item.save()
    except MediaItem.DoesNotExist:
        logger.error(f"MediaItem {media_id} not found")


def mark_media_processing_failed(media_id, error_message):
    """Mark MediaItem as processing failed"""
    try:
        media_item = MediaItem.objects.get(id=media_id)
        media_item.is_processed = False
        if not media_item.camera_info:
            media_item.camera_info = {}
        
        media_item.camera_info['processing_error'] = error_message
        media_item.save()
    except MediaItem.DoesNotExist:
        logger.error(f"MediaItem {media_id} not found")
