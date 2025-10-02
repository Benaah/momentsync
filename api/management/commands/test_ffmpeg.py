from django.core.management.base import BaseCommand
from api.ffmpeg_service import FFmpegService
import asyncio
import tempfile
import os


class Command(BaseCommand):
    help = 'Test FFmpeg functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to test media file',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['video', 'image', 'audio'],
            default='video',
            help='Type of media file to test',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting FFmpeg test...')
        )

        # Test FFmpeg installation
        self.test_ffmpeg_installation()

        # Test with provided file or create test file
        if options['file']:
            file_path = options['file']
            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.ERROR(f'File not found: {file_path}')
                )
                return
        else:
            file_path = self.create_test_file(options['type'])

        # Test media processing
        asyncio.run(self.test_media_processing(file_path, options['type']))

    def test_ffmpeg_installation(self):
        """Test if FFmpeg is properly installed"""
        import subprocess
        
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS('✓ FFmpeg is installed and working')
                )
                # Extract version info
                version_line = result.stdout.split('\n')[0]
                self.stdout.write(f'  Version: {version_line}')
            else:
                self.stdout.write(
                    self.style.ERROR('✗ FFmpeg installation test failed')
                )
                self.stdout.write(f'  Error: {result.stderr}')
                
        except subprocess.TimeoutExpired:
            self.stdout.write(
                self.style.ERROR('✗ FFmpeg command timed out')
            )
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR('✗ FFmpeg not found in PATH')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error testing FFmpeg: {str(e)}')
            )

    def create_test_file(self, file_type):
        """Create a test file for processing"""
        if file_type == 'video':
            return self.create_test_video()
        elif file_type == 'image':
            return self.create_test_image()
        elif file_type == 'audio':
            return self.create_test_audio()
        else:
            raise ValueError(f'Unknown file type: {file_type}')

    def create_test_video(self):
        """Create a test video file using FFmpeg"""
        import subprocess
        
        output_path = tempfile.mktemp(suffix='_test_video.mp4')
        
        try:
            # Create a 5-second test video with color bars
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', 'testsrc=duration=5:size=640x480:rate=30',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created test video: {output_path}')
                )
                return output_path
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Failed to create test video')
                )
                self.stdout.write(f'  Error: {result.stderr}')
                return None
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error creating test video: {str(e)}')
            )
            return None

    def create_test_image(self):
        """Create a test image file using FFmpeg"""
        import subprocess
        
        output_path = tempfile.mktemp(suffix='_test_image.jpg')
        
        try:
            # Create a test image with color bars
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', 'testsrc=duration=1:size=640x480:rate=1',
                '-frames:v', '1',
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created test image: {output_path}')
                )
                return output_path
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Failed to create test image')
                )
                self.stdout.write(f'  Error: {result.stderr}')
                return None
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error creating test image: {str(e)}')
            )
            return None

    def create_test_audio(self):
        """Create a test audio file using FFmpeg"""
        import subprocess
        
        output_path = tempfile.mktemp(suffix='_test_audio.mp3')
        
        try:
            # Create a 3-second test audio tone
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', 'sine=frequency=440:duration=3',
                '-c:a', 'mp3',
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created test audio: {output_path}')
                )
                return output_path
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Failed to create test audio')
                )
                self.stdout.write(f'  Error: {result.stderr}')
                return None
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error creating test audio: {str(e)}')
            )
            return None

    async def test_media_processing(self, file_path, file_type):
        """Test media processing with FFmpeg service"""
        if not file_path or not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR('No valid file to process')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Testing media processing for: {file_path}')
        )

        try:
            ffmpeg_service = FFmpegService()
            
            # Test metadata extraction
            if file_type == 'video':
                metadata = await ffmpeg_service.get_video_metadata(file_path)
                self.stdout.write(f'  Video metadata: {metadata}')
            elif file_type == 'image':
                metadata = await ffmpeg_service.get_image_metadata(file_path)
                self.stdout.write(f'  Image metadata: {metadata}')
            elif file_type == 'audio':
                metadata = await ffmpeg_service.get_audio_metadata(file_path)
                self.stdout.write(f'  Audio metadata: {metadata}')

            # Test processing options
            options = {
                'generate_thumbnails': file_type == 'video',
                'convert_formats': file_type == 'image',
                'generate_gif': file_type == 'video',
                'extract_audio': file_type == 'video',
                'generate_blur': file_type == 'image'
            }

            # Process media
            result = await ffmpeg_service.process_media(file_path, f'{file_type}/*', options)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS('✓ Media processing completed successfully')
                )
                
                # Display results
                if 'results' in result:
                    for key, value in result['results'].items():
                        if isinstance(value, dict) and value.get('success'):
                            self.stdout.write(f'  {key}: {value.get("url", "Generated")}')
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Media processing failed')
                )
                self.stdout.write(f'  Error: {result.get("error", "Unknown error")}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error during media processing: {str(e)}')
            )
        finally:
            # Clean up test file if we created it
            if file_path and file_path.startswith('/tmp'):
                try:
                    os.unlink(file_path)
                    self.stdout.write(f'  Cleaned up test file: {file_path}')
                except:
                    pass

        self.stdout.write(
            self.style.SUCCESS('FFmpeg test completed!')
        )
