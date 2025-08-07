import React, { useState, useEffect } from 'react';
import { StreamInfo, AIModel } from '../types';
import { api } from '../services/api';
import { 
  Plus, 
  Play, 
  Square, 
  Trash2, 
  Camera, 
  Monitor, 
  FileVideo,
  Settings,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

interface StreamManagerProps {
  streams: StreamInfo[];
  onStreamUpdate: () => void;
}

const StreamManager: React.FC<StreamManagerProps> = ({ streams, onStreamUpdate }) => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [availableModels, setAvailableModels] = useState<Record<string, AIModel>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchAvailableModels();
  }, []);

  const fetchAvailableModels = async () => {
    try {
      const response = await api.getAIModels();
      setAvailableModels(response.models);
    } catch (error) {
      console.error('Error fetching AI models:', error);
    }
  };

  const handleStartStream = async (streamId: string) => {
    setLoading(prev => ({ ...prev, [streamId]: true }));
    try {
      await api.startStream(streamId);
      onStreamUpdate();
    } catch (error) {
      console.error('Error starting stream:', error);
      alert('Failed to start stream');
    } finally {
      setLoading(prev => ({ ...prev, [streamId]: false }));
    }
  };

  const handleStopStream = async (streamId: string) => {
    setLoading(prev => ({ ...prev, [streamId]: true }));
    try {
      await api.stopStream(streamId);
      onStreamUpdate();
    } catch (error) {
      console.error('Error stopping stream:', error);
      alert('Failed to stop stream');
    } finally {
      setLoading(prev => ({ ...prev, [streamId]: false }));
    }
  };

  const handleDeleteStream = async (streamId: string) => {
    if (!confirm('Are you sure you want to delete this stream?')) return;
    
    setLoading(prev => ({ ...prev, [streamId]: true }));
    try {
      await api.deleteStream(streamId);
      onStreamUpdate();
    } catch (error) {
      console.error('Error deleting stream:', error);
      alert('Failed to delete stream');
    } finally {
      setLoading(prev => ({ ...prev, [streamId]: false }));
    }
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'webcam': return Camera;
      case 'rtsp': return Monitor;
      case 'file': return FileVideo;
      default: return Monitor;
    }
  };

  const CreateStreamForm: React.FC<{ onClose: () => void }> = ({ onClose }) => {
    const [formData, setFormData] = useState({
      stream_id: '',
      source: 'webcam' as 'webcam' | 'rtsp' | 'file',
      source_path: '0',
      ai_models: [] as string[]
    });
    const [creating, setCreating] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!formData.stream_id || !formData.source_path || formData.ai_models.length === 0) {
        alert('Please fill in all required fields');
        return;
      }

      setCreating(true);
      try {
        await api.createStream(formData);
        onStreamUpdate();
        onClose();
      } catch (error) {
        console.error('Error creating stream:', error);
        alert('Failed to create stream');
      } finally {
        setCreating(false);
      }
    };

    const handleModelToggle = (modelName: string) => {
      setFormData(prev => ({
        ...prev,
        ai_models: prev.ai_models.includes(modelName)
          ? prev.ai_models.filter(m => m !== modelName)
          : [...prev.ai_models, modelName]
      }));
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Stream</h3>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Stream ID *
              </label>
              <input
                type="text"
                value={formData.stream_id}
                onChange={(e) => setFormData(prev => ({ ...prev, stream_id: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., camera_01"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source Type *
              </label>
              <select
                value={formData.source}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  source: e.target.value as any,
                  source_path: e.target.value === 'webcam' ? '0' : ''
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="webcam">Webcam</option>
                <option value="rtsp">RTSP Stream</option>
                <option value="file">Video File</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source Path *
              </label>
              <input
                type="text"
                value={formData.source_path}
                onChange={(e) => setFormData(prev => ({ ...prev, source_path: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={
                  formData.source === 'webcam' ? '0 (camera index)' :
                  formData.source === 'rtsp' ? 'rtsp://example.com/stream' :
                  '/path/to/video.mp4'
                }
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                AI Models * (select at least one)
              </label>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {Object.entries(availableModels).map(([modelName, model]) => (
                  <label key={modelName} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.ai_models.includes(modelName)}
                      onChange={() => handleModelToggle(modelName)}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">
                      {model.description}
                      {model.anthropic_enabled && (
                        <span className="ml-1 text-xs text-green-600">(AI Enabled)</span>
                      )}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
                disabled={creating}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={creating}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {creating ? 'Creating...' : 'Create Stream'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Stream Manager</h2>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Add Stream</span>
        </button>
      </div>

      {/* Streams Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {streams.map((stream) => {
          const SourceIcon = getSourceIcon(stream.source);
          const isLoading = loading[stream.stream_id];
          
          return (
            <div key={stream.stream_id} className="bg-white rounded-lg shadow-md overflow-hidden">
              {/* Header */}
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <SourceIcon className="h-5 w-5 text-gray-600" />
                    <h3 className="font-semibold text-gray-900">{stream.stream_id}</h3>
                  </div>
                  <div className="flex items-center space-x-1">
                    {stream.is_running ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-gray-400" />
                    )}
                    <span className={`text-xs font-medium ${
                      stream.is_running ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      {stream.is_running ? 'Running' : 'Stopped'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-4">
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-gray-600">Source</p>
                    <p className="font-medium text-gray-900">{stream.source_path}</p>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-600">AI Models</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {stream.ai_models.map((model) => (
                        <span
                          key={model}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {model.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Frames</p>
                      <p className="font-medium">{stream.frame_count.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Last Update</p>
                      <p className="font-medium">
                        {new Date(stream.last_update).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="p-4 bg-gray-50 border-t border-gray-200">
                <div className="flex justify-between items-center">
                  <div className="flex space-x-2">
                    {stream.is_running ? (
                      <button
                        onClick={() => handleStopStream(stream.stream_id)}
                        disabled={isLoading}
                        className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition-colors disabled:opacity-50"
                      >
                        <Square className="h-3 w-3" />
                        <span>{isLoading ? 'Stopping...' : 'Stop'}</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleStartStream(stream.stream_id)}
                        disabled={isLoading}
                        className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors disabled:opacity-50"
                      >
                        <Play className="h-3 w-3" />
                        <span>{isLoading ? 'Starting...' : 'Start'}</span>
                      </button>
                    )}
                  </div>
                  
                  <button
                    onClick={() => handleDeleteStream(stream.stream_id)}
                    disabled={isLoading}
                    className="flex items-center space-x-1 px-3 py-1 text-red-600 hover:bg-red-50 rounded text-sm transition-colors disabled:opacity-50"
                  >
                    <Trash2 className="h-3 w-3" />
                    <span>Delete</span>
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty State */}
      {streams.length === 0 && (
        <div className="text-center py-12">
          <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No streams configured</h3>
          <p className="text-gray-600 mb-4">Get started by creating your first video stream</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Create Stream</span>
          </button>
        </div>
      )}

      {/* Create Stream Modal */}
      {showCreateForm && (
        <CreateStreamForm onClose={() => setShowCreateForm(false)} />
      )}
    </div>
  );
};

export default StreamManager;