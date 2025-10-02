import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  VideoCameraIcon, 
  PhoneIcon, 
  MicrophoneIcon, 
  MicrophoneSlashIcon,
  VideoCameraSlashIcon,
  XMarkIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const WebRTCVideo = ({ 
  momentId, 
  onJoin, 
  onLeave, 
  isConnected = false,
  participants = [],
  onToggleAudio,
  onToggleVideo
}) => {
  const [localStream, setLocalStream] = useState(null);
  const [remoteStreams, setRemoteStreams] = useState(new Map());
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);
  
  const localVideoRef = useRef(null);
  const remoteVideoRefs = useRef(new Map());
  const peerConnections = useRef(new Map());
  const dataChannel = useRef(null);

  useEffect(() => {
    if (isConnected) {
      initializeWebRTC();
    } else {
      cleanup();
    }

    return () => {
      cleanup();
    };
  }, [isConnected]);

  const initializeWebRTC = async () => {
    try {
      setIsConnecting(true);
      setError(null);

      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: true
      });

      setLocalStream(stream);
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      // Initialize peer connections for each participant
      for (const participant of participants) {
        await createPeerConnection(participant.id);
      }

      setIsConnecting(false);
    } catch (err) {
      console.error('Error initializing WebRTC:', err);
      setError('Failed to initialize video call');
      toast.error('Camera/microphone access denied');
      setIsConnecting(false);
    }
  };

  const createPeerConnection = async (participantId) => {
    const configuration = {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
      ]
    };

    const peerConnection = new RTCPeerConnection(configuration);
    peerConnections.current.set(participantId, peerConnection);

    // Add local stream to peer connection
    if (localStream) {
      localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
      });
    }

    // Handle remote stream
    peerConnection.ontrack = (event) => {
      const [remoteStream] = event.streams;
      setRemoteStreams(prev => new Map(prev.set(participantId, remoteStream)));
    };

    // Handle ICE candidates
    peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        // Send ICE candidate to other participants
        sendSignalingMessage({
          type: 'ice-candidate',
          candidate: event.candidate,
          target: participantId
        });
      }
    };

    // Handle connection state changes
    peerConnection.onconnectionstatechange = () => {
      console.log(`Connection state with ${participantId}:`, peerConnection.connectionState);
    };

    return peerConnection;
  };

  const sendSignalingMessage = (message) => {
    // This would typically send the message through WebSocket
    // For now, we'll just log it
    console.log('Signaling message:', message);
  };

  const handleToggleAudio = () => {
    if (localStream) {
      const audioTrack = localStream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !isAudioEnabled;
        setIsAudioEnabled(!isAudioEnabled);
        onToggleAudio?.(!isAudioEnabled);
      }
    }
  };

  const handleToggleVideo = () => {
    if (localStream) {
      const videoTrack = localStream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !isVideoEnabled;
        setIsVideoEnabled(!isVideoEnabled);
        onToggleVideo?.(!isVideoEnabled);
      }
    }
  };

  const handleJoin = async () => {
    try {
      await onJoin(momentId);
    } catch (error) {
      console.error('Error joining video call:', error);
      toast.error('Failed to join video call');
    }
  };

  const handleLeave = async () => {
    try {
      await onLeave(momentId);
      cleanup();
    } catch (error) {
      console.error('Error leaving video call:', error);
      toast.error('Failed to leave video call');
    }
  };

  const cleanup = () => {
    // Stop local stream
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
      setLocalStream(null);
    }

    // Close peer connections
    peerConnections.current.forEach(pc => pc.close());
    peerConnections.current.clear();

    // Clear remote streams
    setRemoteStreams(new Map());
  };

  if (!isConnected) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-purple-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <VideoCameraIcon className="h-8 w-8 text-purple-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Video Call
          </h3>
          <p className="text-gray-600 mb-4">
            Start a video call with other participants in this moment
          </p>
          <button
            onClick={handleJoin}
            disabled={isConnecting}
            className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center space-x-2 mx-auto"
          >
            {isConnecting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Connecting...</span>
              </>
            ) : (
              <>
                <PhoneIcon className="h-5 w-5" />
                <span>Join Video Call</span>
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center space-x-2">
          <UserGroupIcon className="h-5 w-5 text-gray-600" />
          <span className="text-sm font-medium text-gray-600">
            {participants.length + 1} participants
          </span>
        </div>
        <button
          onClick={handleLeave}
          className="p-2 text-red-600 hover:bg-red-50 rounded-full transition-colors"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Video Grid */}
      <div className="p-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {/* Local Video */}
          <div className="relative bg-gray-900 rounded-lg overflow-hidden">
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-48 object-cover"
            />
            <div className="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm">
              You
            </div>
            {!isVideoEnabled && (
              <div className="absolute inset-0 bg-gray-800 flex items-center justify-center">
                <VideoCameraSlashIcon className="h-12 w-12 text-gray-400" />
              </div>
            )}
          </div>

          {/* Remote Videos */}
          {Array.from(remoteStreams.entries()).map(([participantId, stream]) => (
            <div key={participantId} className="relative bg-gray-900 rounded-lg overflow-hidden">
              <video
                ref={el => {
                  if (el) {
                    el.srcObject = stream;
                    remoteVideoRefs.current.set(participantId, el);
                  }
                }}
                autoPlay
                playsInline
                className="w-full h-48 object-cover"
              />
              <div className="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm">
                Participant {participantId}
              </div>
            </div>
          ))}
        </div>

        {/* Controls */}
        <div className="flex justify-center space-x-4">
          <button
            onClick={handleToggleAudio}
            className={`p-3 rounded-full transition-colors ${
              isAudioEnabled
                ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                : 'bg-red-500 text-white hover:bg-red-600'
            }`}
            title={isAudioEnabled ? 'Mute microphone' : 'Unmute microphone'}
          >
            {isAudioEnabled ? (
              <MicrophoneIcon className="h-5 w-5" />
            ) : (
              <MicrophoneSlashIcon className="h-5 w-5" />
            )}
          </button>

          <button
            onClick={handleToggleVideo}
            className={`p-3 rounded-full transition-colors ${
              isVideoEnabled
                ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                : 'bg-red-500 text-white hover:bg-red-600'
            }`}
            title={isVideoEnabled ? 'Turn off camera' : 'Turn on camera'}
          >
            {isVideoEnabled ? (
              <VideoCameraIcon className="h-5 w-5" />
            ) : (
              <VideoCameraSlashIcon className="h-5 w-5" />
            )}
          </button>

          <button
            onClick={handleLeave}
            className="p-3 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
            title="Leave call"
          >
            <PhoneIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default WebRTCVideo;
