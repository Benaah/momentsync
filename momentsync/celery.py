import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'momentsync.settings')

app = Celery('momentsync')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery configuration
app.conf.update(
    # Task routing
    task_routes={
        'api.tasks.process_media_async': {'queue': 'media_processing'},
        'api.tasks.generate_video_thumbnails': {'queue': 'media_processing'},
        'api.tasks.compress_video_quality': {'queue': 'media_processing'},
        'api.tasks.convert_image_formats': {'queue': 'media_processing'},
        'api.tasks.generate_blur_placeholder': {'queue': 'media_processing'},
        'api.tasks.extract_audio_from_video': {'queue': 'media_processing'},
        'api.tasks.generate_gif_preview': {'queue': 'media_processing'},
        'api.tasks.cleanup_temp_files': {'queue': 'cleanup'},
        'api.tasks.send_processing_complete_notification': {'queue': 'notifications'},
        'api.tasks.send_processing_failed_notification': {'queue': 'notifications'},
    },
    
    # Task time limits
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Result backend
    result_backend=settings.CELERY_RESULT_BACKEND,
    
    # Task compression
    task_compression='gzip',
    result_compression='gzip',
    
    # Task retry configuration
    task_acks_late=True,
    worker_disable_rate_limits=False,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-temp-files': {
            'task': 'api.tasks.cleanup_temp_files',
            'schedule': 3600.0,  # Run every hour
            'args': ([])
        },
    },
)


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
