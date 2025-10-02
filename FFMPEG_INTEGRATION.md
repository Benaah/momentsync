# FFmpeg Integration for MomentSync

## Overview

This document describes the comprehensive FFmpeg integration in MomentSync 2.0, which provides advanced media processing capabilities including video compression, thumbnail generation, format conversion, and more.

## Features

### Video Processing
- **Multi-quality compression**: Generate mobile, desktop, and original quality versions
- **Thumbnail generation**: Create multiple thumbnails at different timestamps
- **GIF preview**: Generate animated GIF previews for videos
- **Audio extraction**: Extract audio tracks from video files
- **Format conversion**: Convert between various video formats (MP4, WebM, AVI, etc.)

### Image Processing
- **Format conversion**: Convert to modern formats (WebP, AVIF)
- **Multiple sizes**: Generate thumbnail, medium, and large versions
- **Blur placeholders**: Create low-quality blur images for lazy loading
- **Smart compression**: Optimize file sizes while maintaining quality

### Audio Processing
- **Compression**: Optimize audio files for web delivery
- **Format conversion**: Convert between audio formats
- **Waveform extraction**: Generate waveform data for visualization

## Architecture

### Backend Components

#### 1. FFmpegService (`api/ffmpeg_service.py`)
The core service that handles all FFmpeg operations:

```python
class FFmpegService:
    async def process_media(self, file_path, file_type, options)
    async def process_video(self, file_path, options)
    async def process_image(self, file_path, options)
    async def process_audio(self, file_path, options)
    async def compress_video(self, file_path, quality, options)
    async def generate_video_thumbnails(self, file_path, options)
    async def convert_to_webp(self, file_path, options)
    async def convert_to_avif(self, file_path, options)
```

#### 2. Celery Tasks (`api/tasks.py`)
Background tasks for async processing:

```python
@shared_task
def process_media_async(media_id, file_path, file_type, options)

@shared_task
def generate_video_thumbnails(media_id, file_path)

@shared_task
def compress_video_quality(media_id, file_path, quality)

@shared_task
def convert_image_formats(media_id, file_path)
```

#### 3. API Integration (`api/views.py`)
REST API endpoints for media processing:

```python
@action(detail=True, methods=['post'])
def add_media(self, request, pk=None):
    # Handles file upload and starts async processing
```

### Frontend Components

#### 1. VideoProcessor (`frontend/src/components/VideoProcessor.js`)
React component for client-side video processing:

```jsx
<VideoProcessor
  file={selectedFile}
  onProcessed={handleProcessed}
  onError={handleError}
/>
```

## Installation

### Prerequisites
- Python 3.11+
- FFmpeg installed on the system
- Redis server running
- PostgreSQL database

### Quick Setup

1. **Run the setup script**:
   ```bash
   python setup_ffmpeg.py
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp config.env.example .env
   # Edit .env with your configuration
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Start services**:
   ```bash
   # Start Redis
   redis-server

   # Start Celery worker
   celery -A momentsync worker --loglevel=info

   # Start Celery beat (for periodic tasks)
   celery -A momentsync beat --loglevel=info

   # Start Django server
   python manage.py runserver
   ```

### Docker Setup

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

## Configuration

### Environment Variables

```env
# FFmpeg Configuration
FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# Media Processing
MAX_FILE_SIZE=104857600  # 100MB
ALLOWED_VIDEO_FORMATS=mp4,avi,mov,mkv,webm,flv
ALLOWED_IMAGE_FORMATS=jpg,jpeg,png,gif,bmp,tiff,webp
ALLOWED_AUDIO_FORMATS=mp3,wav,aac,flac,ogg
```

### Video Quality Presets

```python
video_presets = {
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
```

## Usage

### Backend API

#### Upload and Process Media

```python
# POST /api/moments/{moment_id}/add_media/
{
    "media": <file>,
    "settings": {
        "generate_thumbnails": true,
        "convert_formats": true,
        "generate_gif": true,
        "extract_audio": false,
        "compression_level": 7
    }
}
```

#### Response

```json
{
    "success": true,
    "media_id": "abc123...",
    "task_id": "celery-task-id",
    "message": "Media uploaded and processing started"
}
```

### Frontend Usage

#### Basic Video Processing

```jsx
import VideoProcessor from './components/VideoProcessor';

function MediaUpload() {
  const [selectedFile, setSelectedFile] = useState(null);

  const handleProcessed = (processedFiles) => {
    console.log('Processing completed:', processedFiles);
  };

  const handleError = (error) => {
    console.error('Processing failed:', error);
  };

  return (
    <VideoProcessor
      file={selectedFile}
      onProcessed={handleProcessed}
      onError={handleError}
    />
  );
}
```

#### Advanced Configuration

```jsx
const settings = {
  quality: 'high',           // 'low', 'medium', 'high'
  format: 'mp4',            // 'mp4', 'webm', 'avi'
  generateThumbnails: true,
  generateGif: true,
  extractAudio: false,
  compressionLevel: 7       // 1-10
};
```

## API Reference

### FFmpegService Methods

#### `process_media(file_path, file_type, options)`
Main processing method that routes to appropriate handlers.

**Parameters:**
- `file_path` (str): Path to the media file
- `file_type` (str): MIME type of the file
- `options` (dict): Processing options

**Returns:**
```python
{
    'success': True,
    'results': {
        'original': {...},
        'mobile': {...},
        'desktop': {...},
        'thumbnails': [...],
        'webp': {...},
        'avif': {...}
    },
    'metadata': {...}
}
```

#### `compress_video(file_path, quality, options)`
Compress video to specific quality.

**Parameters:**
- `file_path` (str): Path to video file
- `quality` (str): Quality preset ('mobile', 'desktop', 'original')
- `options` (dict): Compression options

#### `generate_video_thumbnails(file_path, options)`
Generate thumbnails at different timestamps.

**Returns:**
```python
{
    'success': True,
    'thumbnails': [
        {
            'timestamp': 0.0,
            'url': 'https://...',
            'index': 0
        },
        ...
    ]
}
```

### Celery Tasks

#### `process_media_async(media_id, file_path, file_type, options)`
Main async processing task.

#### `generate_video_thumbnails(media_id, file_path)`
Generate video thumbnails in background.

#### `compress_video_quality(media_id, file_path, quality)`
Compress video to specific quality in background.

## Testing

### Test FFmpeg Installation

```bash
python manage.py test_ffmpeg
```

### Test with Specific File

```bash
python manage.py test_ffmpeg --file /path/to/video.mp4 --type video
```

### Test Different Media Types

```bash
# Test video processing
python manage.py test_ffmpeg --type video

# Test image processing
python manage.py test_ffmpeg --type image

# Test audio processing
python manage.py test_ffmpeg --type audio
```

## Performance Considerations

### Optimization Tips

1. **Use appropriate quality presets** for different use cases
2. **Enable hardware acceleration** when available
3. **Process files in background** using Celery
4. **Use CDN** for serving processed media
5. **Implement caching** for frequently accessed media

### Resource Management

- **Memory usage**: Large files are processed in chunks
- **Disk space**: Temporary files are cleaned up automatically
- **CPU usage**: Processing is distributed across Celery workers
- **Network**: Files are uploaded to S3 for storage

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   ```bash
   # Check installation
   ffmpeg -version
   
   # Install if missing
   python setup_ffmpeg.py
   ```

2. **Permission errors**
   ```bash
   # Check file permissions
   chmod 755 /path/to/media/files
   ```

3. **Memory errors**
   ```bash
   # Increase worker memory
   celery -A momentsync worker --loglevel=info --concurrency=1
   ```

4. **Redis connection errors**
   ```bash
   # Check Redis status
   redis-cli ping
   
   # Start Redis if needed
   redis-server
   ```

### Debug Mode

Enable debug logging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'api.ffmpeg_service': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## Security Considerations

1. **File validation**: Check file types and sizes before processing
2. **Path sanitization**: Prevent directory traversal attacks
3. **Resource limits**: Set appropriate timeouts and memory limits
4. **Access control**: Ensure users can only process their own media
5. **Cleanup**: Remove temporary files after processing

## Monitoring

### Health Checks

```python
# Check FFmpeg availability
python manage.py test_ffmpeg

# Check Celery workers
celery -A momentsync inspect active

# Check Redis connection
redis-cli ping
```

### Metrics

- Processing queue length
- Average processing time
- Success/failure rates
- Resource usage (CPU, memory, disk)

## Contributing

When contributing to the FFmpeg integration:

1. **Test thoroughly** with different media types
2. **Update documentation** for new features
3. **Add error handling** for edge cases
4. **Consider performance** impact
5. **Follow coding standards** and best practices

## License

This FFmpeg integration is part of MomentSync and follows the same license terms.
