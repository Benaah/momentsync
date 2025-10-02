FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        libgthread-2.0-0 \
        libgtk-3-0 \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libxvidcore-dev \
        libx264-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libatlas-base-dev \
        python3-dev \
        python3-numpy \
        ffmpeg \
        libavcodec-extra \
        libavformat-dev \
        libavutil-dev \
        libswscale-dev \
        libavresample-dev \
        libavfilter-dev \
        libavdevice-dev \
        libpostproc-dev \
        libswresample-dev \
        libfdk-aac-dev \
        libmp3lame-dev \
        libopus-dev \
        libvorbis-dev \
        libx264-dev \
        libx265-dev \
        libvpx-dev \
        libaom-dev \
        libdav1d-dev \
        libsvtav1-dev \
        libxavs2-dev \
        libuavs3d-dev \
        libkvazaar-dev \
        libxvid-dev \
        libtheora-dev \
        libschroedinger-dev \
        libspeex-dev \
        libwavpack-dev \
        libtwolame-dev \
        libgsm1-dev \
        libopencore-amrnb-dev \
        libopencore-amrwb-dev \
        libvo-amrwbenc-dev \
        libcodec2-dev \
        libgme-dev \
        libbs2b-dev \
        libchromaprint-dev \
        libflite1-dev \
        libgme-dev \
        libmodplug-dev \
        libmpg123-dev \
        libopenmpt-dev \
        libopus-dev \
        libshine-dev \
        libsnappy-dev \
        libsoxr-dev \
        libssh-dev \
        libtesseract-dev \
        libtwolame-dev \
        libvorbis-dev \
        libwavpack-dev \
        libwebp-dev \
        libx265-dev \
        libxavs-dev \
        libxvid-dev \
        libzmq-dev \
        libzvbi-dev \
        libass-dev \
        libbluray-dev \
        libcaca-dev \
        libcdio-paranoia-dev \
        libdc1394-dev \
        libdrm-dev \
        libfontconfig1-dev \
        libfreetype6-dev \
        libfribidi-dev \
        libgmp-dev \
        libgnutls28-dev \
        libgsm1-dev \
        libiec61883-dev \
        libjack-jackd2-dev \
        libkate-dev \
        liblilv-dev \
        liblivemedia-dev \
        libmfx-dev \
        libmodplug-dev \
        libmp3lame-dev \
        libnettle-dev \
        libomxil-bellagio-dev \
        libopenal-dev \
        libopencv-dev \
        libopenexr-dev \
        libopenjpeg-dev \
        libopenmpt-dev \
        libopus-dev \
        libpulse-dev \
        librabbitmq-dev \
        librsvg2-dev \
        librtmp-dev \
        librubberband-dev \
        libsctp-dev \
        libsdl2-dev \
        libsndfile1-dev \
        libsndio-dev \
        libsnappy-dev \
        libsoxr-dev \
        libspeex-dev \
        libsrt-dev \
        libssh-dev \
        libtesseract-dev \
        libtheora-dev \
        libtwolame-dev \
        libva-dev \
        libvdpau-dev \
        libvorbis-dev \
        libvpx-dev \
        libwavpack-dev \
        libwebp-dev \
        libx11-dev \
        libx264-dev \
        libx265-dev \
        libxau-dev \
        libxcb1-dev \
        libxcb-shm0-dev \
        libxcb-xfixes0-dev \
        libxcb-xv0-dev \
        libxdmcp-dev \
        libxext-dev \
        libxfixes-dev \
        libxrender-dev \
        libxss-dev \
        libxv-dev \
        libxxf86vm-dev \
        libzmq-dev \
        libzvbi-dev \
        libzimg-dev \
        libzstd-dev \
        pkg-config \
        yasm \
        nasm \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create directories for static and media files
RUN mkdir -p /app/static /app/media

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "momentsync.wsgi:application"]
