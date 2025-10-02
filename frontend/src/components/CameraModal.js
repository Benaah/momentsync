import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  XMarkIcon, 
  CameraIcon, 
  VideoCameraIcon,
  PhotoIcon,
  ArrowPathIcon,
  CheckIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const CameraModal = ({ isOpen, onClose, onCapture, onVideoRecord }) => {
  const [mode, setMode] = useState('photo'); // 'photo' or 'video'
  const [isRecording, setIsRecording] = useState(false);
  const [capturedMedia, setCapturedMedia] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [stream, setStream] = useState(null);
  const [error, setError] = useState(null);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);

  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      stopCamera();
    }
    
    return () => {
      stopCamera();
    };
  }, [isOpen]);

  const startCamera = async () => {
    try {
      setError(null);
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { 
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        },
        audio: mode === 'video'
      });
      
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      console.error('Error accessing camera:', err);
      setError('Unable to access camera. Please check permissions.');
      toast.error('Camera access denied');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const context = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' });
        setCapturedMedia(file);
        toast.success('Photo captured!');
      }
    }, 'image/jpeg', 0.8);
  };

  const startVideoRecording = () => {
    if (!stream) return;

    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'video/webm;codecs=vp9'
    });

    recordedChunksRef.current = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        recordedChunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(recordedChunksRef.current, { type: 'video/webm' });
      const file = new File([blob], `video_${Date.now()}.webm`, { type: 'video/webm' });
      setCapturedMedia(file);
      toast.success('Video recorded!');
    };

    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start();
    setIsRecording(true);
  };

  const stopVideoRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleRetake = () => {
    setCapturedMedia(null);
    setIsProcessing(false);
  };

  const handleProcessAndSave = async () => {
    if (!capturedMedia) return;

    setIsProcessing(true);
    try {
      if (mode === 'photo') {
        await onCapture(capturedMedia);
      } else {
        await onVideoRecord(capturedMedia);
      }
      onClose();
    } catch (error) {
      console.error('Error processing media:', error);
      toast.error('Failed to process media');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClose = () => {
    setCapturedMedia(null);
    setIsProcessing(false);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
        onClick={handleClose}
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.8, opacity: 0 }}
          className="relative bg-white rounded-2xl overflow-hidden max-w-4xl w-full max-h-[90vh]"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <div className="flex items-center space-x-4">
              <h2 className="text-xl font-semibold">Camera</h2>
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setMode('photo')}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    mode === 'photo' 
                      ? 'bg-white text-gray-900 shadow-sm' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <PhotoIcon className="h-4 w-4 inline mr-1" />
                  Photo
                </button>
                <button
                  onClick={() => setMode('video')}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    mode === 'video' 
                      ? 'bg-white text-gray-900 shadow-sm' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <VideoCameraIcon className="h-4 w-4 inline mr-1" />
                  Video
                </button>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {error ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CameraIcon className="h-8 w-8 text-red-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Camera Error</h3>
                <p className="text-gray-600 mb-4">{error}</p>
                <button
                  onClick={startCamera}
                  className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
                >
                  Try Again
                </button>
              </div>
            ) : capturedMedia ? (
              <div className="space-y-4">
                <div className="text-center">
                  <h3 className="text-lg font-semibold mb-4">
                    {mode === 'photo' ? 'Photo Captured' : 'Video Recorded'}
                  </h3>
                  
                  {mode === 'photo' ? (
                    <img
                      src={URL.createObjectURL(capturedMedia)}
                      alt="Captured photo"
                      className="max-w-full max-h-96 mx-auto rounded-lg shadow-lg"
                    />
                  ) : (
                    <video
                      src={URL.createObjectURL(capturedMedia)}
                      controls
                      className="max-w-full max-h-96 mx-auto rounded-lg shadow-lg"
                    />
                  )}
                </div>

                <div className="flex justify-center space-x-4">
                  <button
                    onClick={handleRetake}
                    disabled={isProcessing}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                  >
                    <ArrowPathIcon className="h-4 w-4 inline mr-2" />
                    Retake
                  </button>
                  <button
                    onClick={handleProcessAndSave}
                    disabled={isProcessing}
                    className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center"
                  >
                    {isProcessing ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Processing...
                      </>
                    ) : (
                      <>
                        <CheckIcon className="h-4 w-4 inline mr-2" />
                        Save
                      </>
                    )}
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="relative bg-gray-900 rounded-lg overflow-hidden">
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-96 object-cover"
                  />
                  <canvas
                    ref={canvasRef}
                    className="hidden"
                  />
                  
                  {/* Recording indicator */}
                  {isRecording && (
                    <div className="absolute top-4 left-4 flex items-center space-x-2 bg-red-600 text-white px-3 py-1 rounded-full">
                      <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                      <span className="text-sm font-medium">Recording</span>
                    </div>
                  )}
                </div>

                <div className="flex justify-center space-x-4">
                  {mode === 'photo' ? (
                    <button
                      onClick={capturePhoto}
                      className="px-8 py-3 bg-purple-600 text-white rounded-full hover:bg-purple-700 transition-colors flex items-center space-x-2"
                    >
                      <CameraIcon className="h-6 w-6" />
                      <span>Capture Photo</span>
                    </button>
                  ) : (
                    <button
                      onClick={isRecording ? stopVideoRecording : startVideoRecording}
                      className={`px-8 py-3 rounded-full transition-colors flex items-center space-x-2 ${
                        isRecording
                          ? 'bg-red-600 text-white hover:bg-red-700'
                          : 'bg-purple-600 text-white hover:bg-purple-700'
                      }`}
                    >
                      <VideoCameraIcon className="h-6 w-6" />
                      <span>{isRecording ? 'Stop Recording' : 'Start Recording'}</span>
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default CameraModal;
