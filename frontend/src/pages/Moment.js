import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, Upload, Users, Video } from 'lucide-react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../services/api';
import MediaGrid from '../components/MediaGrid';
import CameraModal from '../components/CameraModal';
import WebRTCVideo from '../components/WebRTCVideo';
import InviteModal from '../components/InviteModal';
import VideoProcessor from '../components/VideoProcessor';
import toast from 'react-hot-toast';

const Moment = () => {
  const { momentId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { sendMessage, joinMoment, leaveMoment } = useWebSocket();
  const queryClient = useQueryClient();
  
  const [showCamera, setShowCamera] = useState(false);
  const [showInvite, setShowInvite] = useState(false);
  const [isWebRTCEnabled, setIsWebRTCEnabled] = useState(false);
  const [ setWebrtcConnections] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState([]);
  const [showVideoProcessor, setShowVideoProcessor] = useState(false);
  const [selectedVideoFile, setSelectedVideoFile] = useState(null);
  
  const fileInputRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // Fetch moment data
  const { data: moment, isLoading, error } = useQuery(
    ['moment', momentId],
    () => authAPI.get(`/moments/${momentId}/`),
    {
      enabled: !!momentId,
      onError: (error) => {
        if (error.response?.status === 404) {
          toast.error('Moment not found');
          navigate('/');
        }
      }
    }
  );

  // Upload media mutation
  const uploadMediaMutation = useMutation(
    (file) => {
      const formData = new FormData();
      formData.append('media', file);
      return authAPI.post(`/moments/${momentId}/add_media/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
    },
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['moment', momentId]);
        toast.success('Media uploaded successfully');
      },
      onError: (error) => {
        toast.error('Failed to upload media');
      }
    }
  );

  // Remove media mutation
  const removeMediaMutation = useMutation(
    (mediaId) => authAPI.delete(`/moments/${momentId}/remove_media/${mediaId}/`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['moment', momentId]);
        toast.success('Media removed');
      },
      onError: (error) => {
        toast.error('Failed to remove media');
      }
    }
  );

  // Join moment on mount
  useEffect(() => {
    if (momentId) {
      joinMoment(momentId);
    }
    
    return () => {
      if (momentId) {
        leaveMoment(momentId);
      }
    };
  }, [momentId]);

  // Handle WebSocket events
  useEffect(() => {
    const handleMediaAdded = (event) => {
      const { uploader } = event.detail;
      if (uploader !== user.username) {
        queryClient.invalidateQueries(['moment', momentId]);
        toast.success(`New media added by ${uploader}`);
      }
    };

    const handleMediaRemoved = (event) => {
      const { remover } = event.detail;
      if (remover !== user.username) {
        queryClient.invalidateQueries(['moment', momentId]);
        toast.info(`Media removed by ${remover}`);
      }
    };

    const handleWebRTCOffer = (event) => {
      const { offer, from_user, connection_id } = event.detail;
      // Handle WebRTC offer
      console.log('WebRTC offer received:', { offer, from_user, connection_id });
    };

    const handleUserTyping = (event) => {
      const { user: typingUser, is_typing } = event.detail;
      if (typingUser !== user.username) {
        setTypingUsers(prev => {
          if (is_typing) {
            return [...prev.filter(u => u !== typingUser), typingUser];
          } else {
            return prev.filter(u => u !== typingUser);
          }
        });
      }
    };

    window.addEventListener('media-added', handleMediaAdded);
    window.addEventListener('media-removed', handleMediaRemoved);
    window.addEventListener('webrtc-offer', handleWebRTCOffer);
    window.addEventListener('user-typing', handleUserTyping);

    return () => {
      window.removeEventListener('media-added', handleMediaAdded);
      window.removeEventListener('media-removed', handleMediaRemoved);
      window.removeEventListener('webrtc-offer', handleWebRTCOffer);
      window.removeEventListener('user-typing', handleUserTyping);
    };
  }, [momentId, user.username, queryClient]);

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    files.forEach(file => {
      // Check if it's a video file
      if (file.type.startsWith('video/')) {
        setSelectedVideoFile(file);
        setShowVideoProcessor(true);
      } else {
        uploadMediaMutation.mutate(file);
      }
    });
  };

  const handleVideoProcessed = (processedData) => {
    // Handle processed video data
    console.log('Video processed:', processedData);
    setShowVideoProcessor(false);
    setSelectedVideoFile(null);
    queryClient.invalidateQueries(['moment', momentId]);
    toast.success('Video processed and uploaded successfully!');
  };

  const handleVideoProcessingError = (error) => {
    console.error('Video processing error:', error);
    setShowVideoProcessor(false);
    setSelectedVideoFile(null);
    toast.error('Video processing failed');
  };

  const handleCameraCapture = (imageBlob) => {
    const file = new File([imageBlob], 'camera-capture.jpg', { type: 'image/jpeg' });
    uploadMediaMutation.mutate(file);
    setShowCamera(false);
  };

  const handleMediaRemove = (mediaId) => {
    if (window.confirm('Are you sure you want to remove this media?')) {
      removeMediaMutation.mutate(mediaId);
    }
  };

  const handleTyping = (event) => {
    if (!isTyping) {
      setIsTyping(true);
      sendMessage({
        type: 'typing',
        moment_id: momentId,
        is_typing: true
      });
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
      sendMessage({
        type: 'typing',
        moment_id: momentId,
        is_typing: false
      });
    }, 1000);
  };

  const toggleWebRTC = () => {
    setIsWebRTCEnabled(!isWebRTCEnabled);
    if (!isWebRTCEnabled) {
      // Initialize WebRTC
      sendMessage({
        type: 'webrtc_offer',
        moment_id: momentId,
        connection_id: `${user.username}_${momentId}`
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-destructive mb-4">Error Loading Moment</h2>
          <p className="text-muted-foreground mb-4">{error.message}</p>
          <button 
            onClick={() => navigate('/')}
            className="btn btn-primary"
          >
            Go Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">{moment?.name}</h1>
              <p className="text-muted-foreground">ID: {moment?.momentID}</p>
              {typingUsers.length > 0 && (
                <p className="text-sm text-muted-foreground">
                  {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
                </p>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowInvite(true)}
                className="btn btn-outline btn-sm"
                title="Invite Users"
              >
                <Users className="h-4 w-4" />
              </button>
              
              <button
                onClick={toggleWebRTC}
                className={`btn btn-sm ${isWebRTCEnabled ? 'btn-primary' : 'btn-outline'}`}
                title="Video Call"
              >
                <Video className="h-4 w-4" />
              </button>
              
              <button
                onClick={() => setShowCamera(true)}
                className="btn btn-primary btn-sm"
                title="Take Photo"
              >
                <Camera className="h-4 w-4" />
              </button>
              
              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn btn-outline btn-sm"
                title="Upload Media"
              >
                <Upload className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* WebRTC Video Section */}
      <AnimatePresence>
        {isWebRTCEnabled && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-muted/50 border-b"
          >
            <div className="container mx-auto px-4 py-4">
              <div className="webrtc-container">
                <WebRTCVideo
                  momentId={momentId}
                  isEnabled={isWebRTCEnabled}
                  onConnectionChange={setWebrtcConnections}
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        {/* Description */}
        <div className="mb-6">
          <p className="text-muted-foreground">{moment?.description}</p>
        </div>

        {/* Media Grid */}
        <MediaGrid
          media={moment?.imgIDs || []}
          onRemove={handleMediaRemove}
          onTyping={handleTyping}
        />

        {/* Upload Progress */}
        {uploadMediaMutation.isLoading && (
          <div className="fixed bottom-4 right-4 bg-card p-4 rounded-lg shadow-lg">
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              <span>Uploading...</span>
            </div>
          </div>
        )}
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*,video/*"
        onChange={handleFileUpload}
        className="hidden"
      />

      {/* Modals */}
      <CameraModal
        isOpen={showCamera}
        onClose={() => setShowCamera(false)}
        onCapture={handleCameraCapture}
      />

      <InviteModal
        isOpen={showInvite}
        onClose={() => setShowInvite(false)}
        momentId={momentId}
      />

      <VideoProcessor
        file={selectedVideoFile}
        onProcessed={handleVideoProcessed}
        onError={handleVideoProcessingError}
        isOpen={showVideoProcessor}
        onClose={() => {
          setShowVideoProcessor(false);
          setSelectedVideoFile(null);
        }}
      />
    </div>
  );
};

export default Moment;
