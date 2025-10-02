import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { useAuth } from './AuthContext';
import toast from 'react-hot-toast';

const WebSocketContext = createContext();

export const WebSocketProvider = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const maxReconnectAttempts = 5;
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    if (isAuthenticated && user) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [isAuthenticated, user]);

  const connectWebSocket = () => {
    if (socket?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/`;
    
    const newSocket = new WebSocket(wsUrl);
    
    newSocket.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setReconnectAttempts(0);
      
      // Send authentication
      newSocket.send(JSON.stringify({
        type: 'auth',
        token: localStorage.getItem('token'),
        user: user.username
      }));
    };

    newSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    newSocket.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      setIsConnected(false);
      
      if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
        scheduleReconnect();
      }
    };

    newSocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      toast.error('Connection error. Attempting to reconnect...');
    };

    setSocket(newSocket);
  };

  const scheduleReconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
    setReconnectAttempts(prev => prev + 1);

    reconnectTimeoutRef.current = setTimeout(() => {
      console.log(`Attempting to reconnect... (${reconnectAttempts + 1}/${maxReconnectAttempts})`);
      connectWebSocket();
    }, delay);
  };

  const disconnectWebSocket = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (socket) {
      socket.close(1000, 'User logout');
      setSocket(null);
    }
    setIsConnected(false);
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'notification':
        toast(data.body, {
          icon: '🔔',
          duration: 4000,
        });
        break;
      
      case 'media_added':
        toast.success(`New media added by ${data.uploader}`);
        break;
      
      case 'media_removed':
        toast.info(`Media removed by ${data.remover}`);
        break;
      
      case 'moment_invitation':
        toast.success(`You've been invited to ${data.moment_name}`, {
          duration: 6000,
          action: {
            label: 'View',
            onClick: () => window.location.href = `/moment/${data.moment_id}`
          }
        });
        break;
      
      case 'webrtc_offer':
        handleWebRTCOffer(data);
        break;
      
      case 'webrtc_answer':
        handleWebRTCAnswer(data);
        break;
      
      case 'webrtc_ice_candidate':
        handleWebRTCIceCandidate(data);
        break;
      
      case 'user_typing':
        handleUserTyping(data);
        break;
      
      case 'pong':
        // Handle ping/pong for connection health
        break;
      
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  };

  const handleWebRTCOffer = (data) => {
    // Emit custom event for WebRTC handling
    window.dispatchEvent(new CustomEvent('webrtc-offer', { detail: data }));
  };

  const handleWebRTCAnswer = (data) => {
    window.dispatchEvent(new CustomEvent('webrtc-answer', { detail: data }));
  };

  const handleWebRTCIceCandidate = (data) => {
    window.dispatchEvent(new CustomEvent('webrtc-ice-candidate', { detail: data }));
  };

  const handleUserTyping = (data) => {
    window.dispatchEvent(new CustomEvent('user-typing', { detail: data }));
  };

  const sendMessage = (message) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected');
      toast.error('Connection lost. Please refresh the page.');
    }
  };

  const joinMoment = (momentId) => {
    sendMessage({
      type: 'join_moment',
      moment_id: momentId
    });
  };

  const leaveMoment = (momentId) => {
    sendMessage({
      type: 'leave_moment',
      moment_id: momentId
    });
  };

  const sendTyping = (momentId, isTyping) => {
    sendMessage({
      type: 'typing',
      moment_id: momentId,
      is_typing: isTyping
    });
  };

  const ping = () => {
    sendMessage({ type: 'ping' });
  };

  // Send ping every 30 seconds to keep connection alive
  useEffect(() => {
    if (isConnected) {
      const pingInterval = setInterval(ping, 30000);
      return () => clearInterval(pingInterval);
    }
  }, [isConnected]);

  const value = {
    socket,
    isConnected,
    reconnectAttempts,
    sendMessage,
    joinMoment,
    leaveMoment,
    sendTyping,
    ping,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};
