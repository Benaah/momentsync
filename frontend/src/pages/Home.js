import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';
import { PlusIcon, ShareIcon, HeartIcon, ChatBubbleLeftIcon, TrashIcon, PencilIcon } from '@heroicons/react/24/outline';

const Home = () => {
  const { user } = useAuth();
  const { socket } = useWebSocket();
  const navigate = useNavigate();
  const [moments, setMoments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState(null);

  useEffect(() => {
    // Fetch user's moments
    fetchMoments();
  }, []);

  const fetchMoments = async () => {
    try {
      const response = await authAPI.get('/moments/');
      setMoments(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching moments:', error);
      toast.error('Failed to load moments');
    } finally {
      setLoading(false);
    }
  };

  const createMoment = async () => {
    setCreating(true);
    try {
      const momentName = prompt('Enter moment name:');
      if (!momentName) return;

      const response = await authAPI.post('/moments/', {
        name: momentName,
        description: `A new moment created by ${user?.username}`,
      });
      
      setMoments([response.data, ...moments]);
      toast.success('Moment created successfully');
      navigate(`/moment/${response.data.momentID}`);
    } catch (error) {
      console.error('Error creating moment:', error);
      toast.error('Failed to create moment');
    } finally {
      setCreating(false);
    }
  };

  const deleteMoment = async (momentId) => {
    if (!window.confirm('Are you sure you want to delete this moment? This action cannot be undone.')) {
      return;
    }

    setDeleting(momentId);
    try {
      await authAPI.delete(`/moments/${momentId}/`);
      setMoments(moments.filter(moment => moment.momentID !== momentId));
      toast.success('Moment deleted successfully');
    } catch (error) {
      console.error('Error deleting moment:', error);
      toast.error('Failed to delete moment');
    } finally {
      setDeleting(null);
    }
  };

  const shareMoment = async (momentId) => {
    try {
      const shareUrl = `${window.location.origin}/moment/${momentId}`;
      await navigator.clipboard.writeText(shareUrl);
      toast.success('Share link copied to clipboard');
    } catch (error) {
      console.error('Error sharing moment:', error);
      toast.error('Failed to copy share link');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Welcome back, {user?.username || 'User'}!
            </h1>
            <p className="text-gray-600">Share and sync your precious moments</p>
          </div>
          <button
            onClick={createMoment}
            disabled={creating}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all duration-200 flex items-center gap-2 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {creating ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              <PlusIcon className="h-5 w-5" />
            )}
            {creating ? 'Creating...' : 'Create Moment'}
          </button>
        </div>

        {/* Moments Grid */}
        {moments.length === 0 ? (
          <div className="text-center py-12">
            <div className="bg-white rounded-2xl p-12 shadow-lg">
              <div className="w-24 h-24 bg-gradient-to-r from-purple-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <PlusIcon className="h-12 w-12 text-purple-600" />
              </div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                No moments yet
              </h3>
              <p className="text-gray-600 mb-8">
                Start creating and sharing your memories with friends and family
              </p>
              <button
                onClick={createMoment}
                className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-3 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all duration-200"
              >
                Create Your First Moment
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {moments.map((moment) => (
              <div key={moment.id} className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-200">
                <div className="aspect-video bg-gradient-to-br from-purple-100 to-blue-100 flex items-center justify-center">
                  {moment.media_items && moment.media_items.length > 0 ? (
                    <img
                      src={moment.media_items[0].file_url}
                      alt={moment.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-center">
                      <div className="w-16 h-16 bg-gradient-to-r from-purple-200 to-blue-200 rounded-full flex items-center justify-center mx-auto mb-4">
                        <ShareIcon className="h-8 w-8 text-purple-600" />
                      </div>
                      <p className="text-gray-600">No media</p>
                    </div>
                  )}
                </div>
                <div className="p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {moment.title || 'Untitled Moment'}
                  </h3>
                  <p className="text-gray-600 mb-4 line-clamp-2">
                    {moment.description || 'No description available'}
                  </p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <HeartIcon className="h-4 w-4" />
                        <span>{moment.likes_count || 0}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <ChatBubbleLeftIcon className="h-4 w-4" />
                        <span>{moment.comments_count || 0}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => shareMoment(moment.momentID || moment.id)}
                        className="p-2 text-gray-400 hover:text-purple-600 transition-colors"
                        title="Share"
                      >
                        <ShareIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => deleteMoment(moment.momentID || moment.id)}
                        disabled={deleting === (moment.momentID || moment.id)}
                        className="p-2 text-gray-400 hover:text-red-600 transition-colors disabled:opacity-50"
                        title="Delete"
                      >
                        {deleting === (moment.momentID || moment.id) ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                        ) : (
                          <TrashIcon className="h-4 w-4" />
                        )}
                      </button>
                      <Link
                        to={`/moment/${moment.momentID || moment.id}`}
                        className="text-purple-600 hover:text-purple-700 font-medium"
                      >
                        View →
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
