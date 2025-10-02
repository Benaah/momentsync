import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  EyeIcon, 
  DownloadIcon, 
  TrashIcon, 
  HeartIcon,
  ChatBubbleLeftIcon,
  ShareIcon,
  PlayIcon,
  PauseIcon
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';

const MediaGrid = ({ 
  mediaItems = [], 
  onDelete, 
  onLike, 
  onComment, 
  onShare,
  onDownload,
  isOwner = false 
}) => {
  const [selectedMedia, setSelectedMedia] = useState(null);
  const [likedItems, setLikedItems] = useState(new Set());
  const [playingVideo, setPlayingVideo] = useState(null);

  const handleLike = async (mediaId) => {
    try {
      await onLike(mediaId);
      setLikedItems(prev => {
        const newSet = new Set(prev);
        if (newSet.has(mediaId)) {
          newSet.delete(mediaId);
        } else {
          newSet.add(mediaId);
        }
        return newSet;
      });
    } catch (error) {
      toast.error('Failed to like media');
    }
  };

  const handleVideoPlay = (mediaId) => {
    setPlayingVideo(playingVideo === mediaId ? null : mediaId);
  };

  const getMediaType = (url) => {
    if (url.includes('.mp4') || url.includes('.webm') || url.includes('.mov')) {
      return 'video';
    } else if (url.includes('.jpg') || url.includes('.jpeg') || url.includes('.png') || url.includes('.webp')) {
      return 'image';
    }
    return 'unknown';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (mediaItems.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-24 h-24 bg-gradient-to-r from-purple-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <EyeIcon className="h-12 w-12 text-purple-600" />
        </div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">No media yet</h3>
        <p className="text-gray-600">Upload some photos or videos to get started</p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {mediaItems.map((media, index) => {
          const mediaType = getMediaType(media.file_url || media.url);
          const isLiked = likedItems.has(media.id);
          const isPlaying = playingVideo === media.id;

          return (
            <motion.div
              key={media.id}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className="relative group bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200"
            >
              {/* Media Content */}
              <div className="aspect-square relative overflow-hidden">
                {mediaType === 'video' ? (
                  <div className="relative w-full h-full">
                    <video
                      className="w-full h-full object-cover"
                      src={media.file_url || media.url}
                      poster={media.thumbnail_url}
                      onPlay={() => setPlayingVideo(media.id)}
                      onPause={() => setPlayingVideo(null)}
                    />
                    <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center">
                      <button
                        onClick={() => handleVideoPlay(media.id)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-white bg-opacity-90 rounded-full p-3 hover:bg-opacity-100"
                      >
                        {isPlaying ? (
                          <PauseIcon className="h-6 w-6 text-gray-900" />
                        ) : (
                          <PlayIcon className="h-6 w-6 text-gray-900" />
                        )}
                      </button>
                    </div>
                  </div>
                ) : (
                  <img
                    src={media.file_url || media.url}
                    alt={media.caption || 'Media'}
                    className="w-full h-full object-cover cursor-pointer"
                    onClick={() => setSelectedMedia(media)}
                  />
                )}
              </div>

              {/* Overlay Actions */}
              <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all duration-200 flex items-center justify-center opacity-0 group-hover:opacity-100">
                <div className="flex space-x-2">
                  <button
                    onClick={() => setSelectedMedia(media)}
                    className="p-2 bg-white bg-opacity-90 rounded-full hover:bg-opacity-100 transition-all duration-200"
                    title="View"
                  >
                    <EyeIcon className="h-5 w-5 text-gray-900" />
                  </button>
                  
                  <button
                    onClick={() => handleLike(media.id)}
                    className={`p-2 rounded-full transition-all duration-200 ${
                      isLiked 
                        ? 'bg-red-500 text-white' 
                        : 'bg-white bg-opacity-90 text-gray-900 hover:bg-opacity-100'
                    }`}
                    title="Like"
                  >
                    {isLiked ? (
                      <HeartSolidIcon className="h-5 w-5" />
                    ) : (
                      <HeartIcon className="h-5 w-5" />
                    )}
                  </button>

                  <button
                    onClick={() => onShare(media.id)}
                    className="p-2 bg-white bg-opacity-90 rounded-full hover:bg-opacity-100 transition-all duration-200"
                    title="Share"
                  >
                    <ShareIcon className="h-5 w-5 text-gray-900" />
                  </button>

                  {onDownload && (
                    <button
                      onClick={() => onDownload(media.id)}
                      className="p-2 bg-white bg-opacity-90 rounded-full hover:bg-opacity-100 transition-all duration-200"
                      title="Download"
                    >
                      <DownloadIcon className="h-5 w-5 text-gray-900" />
                    </button>
                  )}

                  {isOwner && onDelete && (
                    <button
                      onClick={() => onDelete(media.id)}
                      className="p-2 bg-red-500 bg-opacity-90 rounded-full hover:bg-opacity-100 transition-all duration-200"
                      title="Delete"
                    >
                      <TrashIcon className="h-5 w-5 text-white" />
                    </button>
                  )}
                </div>
              </div>

              {/* Media Info */}
              <div className="p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">
                    {formatFileSize(media.file_size || 0)}
                  </span>
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <div className="flex items-center space-x-1">
                      <HeartIcon className="h-4 w-4" />
                      <span>{media.likes_count || 0}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <ChatBubbleLeftIcon className="h-4 w-4" />
                      <span>{media.comments_count || 0}</span>
                    </div>
                  </div>
                </div>
                
                {media.caption && (
                  <p className="text-sm text-gray-700 line-clamp-2">
                    {media.caption}
                  </p>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Media Modal */}
      <AnimatePresence>
        {selectedMedia && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
            onClick={() => setSelectedMedia(null)}
          >
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.8 }}
              className="relative max-w-4xl max-h-full bg-white rounded-lg overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setSelectedMedia(null)}
                className="absolute top-4 right-4 z-10 bg-black bg-opacity-50 text-white rounded-full p-2 hover:bg-opacity-75"
              >
                <EyeIcon className="h-6 w-6" />
              </button>

              {getMediaType(selectedMedia.file_url || selectedMedia.url) === 'video' ? (
                <video
                  className="w-full h-auto max-h-[80vh]"
                  src={selectedMedia.file_url || selectedMedia.url}
                  controls
                  autoPlay
                />
              ) : (
                <img
                  src={selectedMedia.file_url || selectedMedia.url}
                  alt={selectedMedia.caption || 'Media'}
                  className="w-full h-auto max-h-[80vh] object-contain"
                />
              )}

              <div className="p-4">
                <h3 className="text-lg font-semibold mb-2">
                  {selectedMedia.caption || 'Untitled'}
                </h3>
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span>{formatFileSize(selectedMedia.file_size || 0)}</span>
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={() => handleLike(selectedMedia.id)}
                      className={`flex items-center space-x-1 ${
                        likedItems.has(selectedMedia.id) ? 'text-red-500' : 'text-gray-600'
                      }`}
                    >
                      {likedItems.has(selectedMedia.id) ? (
                        <HeartSolidIcon className="h-5 w-5" />
                      ) : (
                        <HeartIcon className="h-5 w-5" />
                      )}
                      <span>{selectedMedia.likes_count || 0}</span>
                    </button>
                    <button
                      onClick={() => onComment(selectedMedia.id)}
                      className="flex items-center space-x-1 text-gray-600"
                    >
                      <ChatBubbleLeftIcon className="h-5 w-5" />
                      <span>{selectedMedia.comments_count || 0}</span>
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default MediaGrid;
