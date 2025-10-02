import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Pause, Square, Download, Settings, RotateCcw, X } from 'lucide-react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useWebSocket } from '../contexts/WebSocketContext';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';

const VideoProcessor = ({ file, onProcessed, onError, isOpen = false, onClose }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [processingStep, setProcessingStep] = useState('');
  const [processedFiles, setProcessedFiles] = useState({});
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    quality: 'high',
    format: 'mp4',
    generateThumbnails: true,
    generateGif: true,
    extractAudio: false,
    compressionLevel: 7
  });
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const { sendMessage } = useWebSocket();

  useEffect(() => {
    if (file) {
      loadVideo();
    }
  }, [file]);

  const loadVideo = () => {
    if (videoRef.current) {
      const url = URL.createObjectURL(file);
      videoRef.current.src = url;
    }
  };

  const processVideo = async () => {
    if (!file) return;

    setIsProcessing(true);
    setProgress(0);
    setProcessedFiles({});

    try {
      // Step 1: Upload original file to backend for processing
      setProcessingStep('Uploading video for processing...');
      setProgress(10);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('settings', JSON.stringify(settings));

      const response = await authAPI.post('/media/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setProgress(30);
      setProcessingStep('Processing video with FFmpeg...');

      // Step 2: Process video with backend FFmpeg service
      const processResponse = await authAPI.post('/media/process/', {
        file_id: response.data.id,
        operations: [
          'compress',
          'generate_thumbnails',
          ...(settings.generateGif ? ['generate_gif'] : []),
          ...(settings.extractAudio ? ['extract_audio'] : [])
        ],
        quality: settings.quality,
        format: settings.format,
        compression_level: settings.compressionLevel
      });

      setProgress(60);
      setProcessingStep('Generating thumbnails...');

      // Step 3: Generate thumbnails
      const thumbnailsResponse = await authAPI.post(`/media/${response.data.id}/generate_thumbnails/`);
      
      setProgress(80);
      setProcessingStep('Finalizing...');

      // Step 4: Get processed files
      const processedResponse = await authAPI.get(`/media/${response.data.id}/processed_files/`);

      setProcessedFiles(processedResponse.data);
      setProgress(100);
      setProcessingStep('Processing complete!');

      toast.success('Video processed successfully!');
      onProcessed?.(processedResponse.data);

    } catch (error) {
      console.error('Video processing error:', error);
      onError?.(error);
      toast.error('Video processing failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const generateThumbnails = async () => {
    if (!videoRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    const thumbnails = [];
    const duration = video.duration;
    const timestamps = [0, duration * 0.25, duration * 0.5, duration * 0.75, duration - 1];

    for (let i = 0; i < timestamps.length; i++) {
      video.currentTime = timestamps[i];
      
      await new Promise(resolve => {
        video.addEventListener('seeked', resolve, { once: true });
      });

      canvas.width = 300;
      canvas.height = 200;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      const thumbnailDataUrl = canvas.toDataURL('image/jpeg', 0.8);
      thumbnails.push({
        timestamp: timestamps[i],
        dataUrl: thumbnailDataUrl,
        index: i
      });
    }

    setProcessedFiles(prev => ({
      ...prev,
      thumbnails
    }));
  };

  const generateCompressedVersions = async () => {
    // Simulate compression by creating different quality versions
    const qualities = ['mobile', 'desktop', 'original'];
    const compressed = {};

    for (const quality of qualities) {
      // In a real implementation, this would call the backend API
      compressed[quality] = {
        url: URL.createObjectURL(file),
        quality,
        size: Math.round(file.size * (quality === 'mobile' ? 0.3 : quality === 'desktop' ? 0.7 : 1))
      };
    }

    setProcessedFiles(prev => ({
      ...prev,
      compressed
    }));
  };

  const generateGifPreview = async () => {
    if (!videoRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Create GIF frames
    const frames = [];
    const duration = Math.min(video.duration, 3); // First 3 seconds
    const frameCount = 30; // 10 FPS for 3 seconds
    
    for (let i = 0; i < frameCount; i++) {
      const time = (i / frameCount) * duration;
      video.currentTime = time;
      
      await new Promise(resolve => {
        video.addEventListener('seeked', resolve, { once: true });
      });

      canvas.width = 320;
      canvas.height = 240;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      const frameDataUrl = canvas.toDataURL('image/jpeg', 0.7);
      frames.push(frameDataUrl);
    }

    setProcessedFiles(prev => ({
      ...prev,
      gif: {
        frames,
        duration: 3
      }
    }));
  };

  const downloadFile = (fileData, filename) => {
    const link = document.createElement('a');
    link.href = fileData;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const resetProcessing = () => {
    setIsProcessing(false);
    setProgress(0);
    setProcessingStep('');
    setProcessedFiles({});
  };

  if (!isOpen || !file) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.8, opacity: 0 }}
          className="relative bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <h2 className="text-xl font-semibold text-gray-900">Video Processor</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
      {/* Video Preview */}
      <div className="relative bg-black rounded-lg overflow-hidden">
        <video
          ref={videoRef}
          className="w-full h-auto max-h-96"
          controls
          preload="metadata"
        >
          Your browser does not support the video tag.
        </video>
        
        {/* Processing Overlay */}
        <AnimatePresence>
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/50 flex items-center justify-center"
            >
              <div className="text-center text-white">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                <p className="text-lg font-medium">{processingStep}</p>
                <div className="w-64 bg-gray-700 rounded-full h-2 mt-4">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <p className="text-sm mt-2">{progress}%</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={processVideo}
            disabled={isProcessing}
            className="btn btn-primary"
          >
            {isProcessing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Processing...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Process Video
              </>
            )}
          </button>

          <button
            onClick={resetProcessing}
            disabled={isProcessing}
            className="btn btn-outline"
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </button>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="btn btn-outline"
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </button>
        </div>

        <div className="text-sm text-muted-foreground">
          {file.size > 1024 * 1024
            ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
            : `${(file.size / 1024).toFixed(1)} KB`}
        </div>
      </div>

      {/* Settings Panel */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border rounded-lg p-4 space-y-4"
          >
            <h3 className="font-medium">Processing Settings</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Quality</label>
                <select
                  value={settings.quality}
                  onChange={(e) => setSettings(prev => ({ ...prev, quality: e.target.value }))}
                  className="input"
                >
                  <option value="low">Low (Mobile)</option>
                  <option value="medium">Medium (Desktop)</option>
                  <option value="high">High (Original)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Format</label>
                <select
                  value={settings.format}
                  onChange={(e) => setSettings(prev => ({ ...prev, format: e.target.value }))}
                  className="input"
                >
                  <option value="mp4">MP4</option>
                  <option value="webm">WebM</option>
                  <option value="avi">AVI</option>
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.generateThumbnails}
                  onChange={(e) => setSettings(prev => ({ ...prev, generateThumbnails: e.target.checked }))}
                  className="mr-2"
                />
                Generate thumbnails
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.generateGif}
                  onChange={(e) => setSettings(prev => ({ ...prev, generateGif: e.target.checked }))}
                  className="mr-2"
                />
                Generate GIF preview
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.extractAudio}
                  onChange={(e) => setSettings(prev => ({ ...prev, extractAudio: e.target.checked }))}
                  className="mr-2"
                />
                Extract audio
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Compression Level: {settings.compressionLevel}
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={settings.compressionLevel}
                onChange={(e) => setSettings(prev => ({ ...prev, compressionLevel: parseInt(e.target.value) }))}
                className="w-full"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Processed Files */}
      <AnimatePresence>
        {Object.keys(processedFiles).length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="space-y-4"
          >
            <h3 className="font-medium">Processed Files</h3>

            {/* Thumbnails */}
            {processedFiles.thumbnails && (
              <div>
                <h4 className="text-sm font-medium mb-2">Thumbnails</h4>
                <div className="grid grid-cols-5 gap-2">
                  {processedFiles.thumbnails.map((thumb, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={thumb.dataUrl}
                        alt={`Thumbnail ${index + 1}`}
                        className="w-full h-20 object-cover rounded"
                      />
                      <button
                        onClick={() => downloadFile(thumb.dataUrl, `thumbnail_${index + 1}.jpg`)}
                        className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white transition-opacity"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Compressed Versions */}
            {processedFiles.compressed && (
              <div>
                <h4 className="text-sm font-medium mb-2">Compressed Versions</h4>
                <div className="space-y-2">
                  {Object.entries(processedFiles.compressed).map(([quality, data]) => (
                    <div key={quality} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <span className="font-medium capitalize">{quality}</span>
                        <span className="text-sm text-muted-foreground ml-2">
                          {(data.size / (1024 * 1024)).toFixed(1)} MB
                        </span>
                      </div>
                      <button
                        onClick={() => downloadFile(data.url, `${quality}_version.${settings.format}`)}
                        className="btn btn-sm btn-outline"
                      >
                        <Download className="h-4 w-4 mr-1" />
                        Download
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* GIF Preview */}
            {processedFiles.gif && (
              <div>
                <h4 className="text-sm font-medium mb-2">GIF Preview</h4>
                <div className="flex items-center space-x-2">
                  <img
                    src={processedFiles.gif.frames[0]}
                    alt="GIF Preview"
                    className="w-32 h-24 object-cover rounded"
                  />
                  <div>
                    <p className="text-sm">3 second preview</p>
                    <p className="text-xs text-muted-foreground">
                      {processedFiles.gif.frames.length} frames
                    </p>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hidden canvas for processing */}
      <canvas ref={canvasRef} className="hidden" />
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default VideoProcessor;
