#!/usr/bin/env python3
"""
FFmpeg Setup Script for MomentSync
This script helps set up FFmpeg and related dependencies for the MomentSync project.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f" {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f" {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f" {description} failed: {e.stderr}")
        return False


def check_ffmpeg_installation():
    """Check if FFmpeg is already installed"""
    print(" Checking FFmpeg installation...")
    
    # Check if ffmpeg is in PATH
    if shutil.which('ffmpeg'):
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f" FFmpeg is already installed: {version_line}")
                return True
        except:
            pass
    
    print(" FFmpeg not found in PATH")
    return False


def install_ffmpeg_windows():
    """Install FFmpeg on Windows"""
    print(" Installing FFmpeg on Windows...")
    
    # Check if chocolatey is available
    if shutil.which('choco'):
        return run_command('choco install ffmpeg -y', "Installing FFmpeg via Chocolatey")
    
    # Check if winget is available
    if shutil.which('winget'):
        return run_command('winget install ffmpeg', "Installing FFmpeg via Winget")
    
    # Check if scoop is available
    if shutil.which('scoop'):
        return run_command('scoop install ffmpeg', "Installing FFmpeg via Scoop")
    
    print(" No package manager found. Please install FFmpeg manually:")
    print("   1. Download from https://ffmpeg.org/download.html")
    print("   2. Extract to a folder (e.g., C:\\ffmpeg)")
    print("   3. Add the bin folder to your PATH environment variable")
    return False


def install_ffmpeg_linux():
    """Install FFmpeg on Linux"""
    print(" Installing FFmpeg on Linux...")
    
    # Try different package managers
    package_managers = [
        ('apt-get', 'sudo apt-get update && sudo apt-get install -y ffmpeg'),
        ('yum', 'sudo yum install -y ffmpeg'),
        ('dnf', 'sudo dnf install -y ffmpeg'),
        ('pacman', 'sudo pacman -S ffmpeg'),
        ('zypper', 'sudo zypper install ffmpeg'),
    ]
    
    for pm, command in package_managers:
        if shutil.which(pm):
            return run_command(command, f"Installing FFmpeg via {pm}")
    
    print(" No supported package manager found")
    return False


def install_ffmpeg_macos():
    """Install FFmpeg on macOS"""
    print(" Installing FFmpeg on macOS...")
    
    # Try Homebrew first
    if shutil.which('brew'):
        return run_command('brew install ffmpeg', "Installing FFmpeg via Homebrew")
    
    # Try MacPorts
    if shutil.which('port'):
        return run_command('sudo port install ffmpeg', "Installing FFmpeg via MacPorts")
    
    print(" No package manager found. Please install FFmpeg manually:")
    print("   1. Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
    print("   2. Run: brew install ffmpeg")
    return False


def install_ffmpeg():
    """Install FFmpeg based on the operating system"""
    system = platform.system().lower()
    
    if system == 'windows':
        return install_ffmpeg_windows()
    elif system == 'linux':
        return install_ffmpeg_linux()
    elif system == 'darwin':
        return install_ffmpeg_macos()
    else:
        print(f" Unsupported operating system: {system}")
        return False


def install_python_dependencies():
    """Install Python dependencies for FFmpeg processing"""
    print("🐍 Installing Python dependencies...")
    
    requirements = [
        'ffmpeg-python>=0.2.0',
        'pydub>=0.25.1',
        'moviepy>=1.0.3',
        'Pillow>=10.0.0',
        'celery>=5.3.0',
        'django-celery-beat>=2.5.0',
        'django-celery-results>=2.5.0',
        'imageio>=2.31.0',
        'imageio-ffmpeg>=0.4.8',
        'opencv-python>=4.8.0',
        'numpy>=1.24.0',
        'boto3>=1.28.0',
    ]
    
    for package in requirements:
        if not run_command(f'pip install {package}', f"Installing {package}"):
            print(f"  Warning: Failed to install {package}")
    
    return True


def create_environment_file():
    """Create environment configuration file"""
    print(" Creating environment configuration...")
    
    env_content = """# FFmpeg Configuration
FFMPEG_PATH=ffmpeg
FFPROBE_PATH=ffprobe

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# AWS S3 Configuration (optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# Media Processing Configuration
MAX_FILE_SIZE=104857600  # 100MB
ALLOWED_VIDEO_FORMATS=mp4,avi,mov,mkv,webm,flv
ALLOWED_IMAGE_FORMATS=jpg,jpeg,png,gif,bmp,tiff,webp
ALLOWED_AUDIO_FORMATS=mp3,wav,aac,flac,ogg
"""
    
    env_file = Path('.env')
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(" Created .env file with FFmpeg configuration")
    else:
        print(" .env file already exists, skipping creation")


def test_ffmpeg_functionality():
    """Test FFmpeg functionality"""
    print(" Testing FFmpeg functionality...")
    
    try:
        # Test basic FFmpeg command
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(" FFmpeg basic functionality test passed")
            
            # Test FFprobe
            result = subprocess.run(['ffprobe', '-version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(" FFprobe functionality test passed")
                return True
            else:
                print(" FFprobe test failed")
                return False
        else:
            print(" FFmpeg basic functionality test failed")
            return False
    except subprocess.TimeoutExpired:
        print(" FFmpeg test timed out")
        return False
    except Exception as e:
        print(f" FFmpeg test error: {str(e)}")
        return False


def main():
    """Main setup function"""
    print(" MomentSync FFmpeg Setup")
    print("=" * 50)
    
    # Check if FFmpeg is already installed
    if check_ffmpeg_installation():
        print(" FFmpeg is already installed and working")
    else:
        print(" Installing FFmpeg...")
        if not install_ffmpeg():
            print(" Failed to install FFmpeg. Please install it manually.")
            sys.exit(1)
    
    # Install Python dependencies
    print("\n Installing Python dependencies...")
    install_python_dependencies()
    
    # Create environment file
    print("\n Setting up configuration...")
    create_environment_file()
    
    # Test functionality
    print("\n Testing setup...")
    if test_ffmpeg_functionality():
        print("\n FFmpeg setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure your .env file with your AWS credentials")
        print("2. Run: python manage.py migrate")
        print("3. Run: python manage.py test_ffmpeg")
        print("4. Start the development server: python manage.py runserver")
    else:
        print("\n FFmpeg setup completed with errors")
        print("Please check the installation and try again")
        sys.exit(1)


if __name__ == '__main__':
    main()
