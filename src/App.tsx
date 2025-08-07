import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import StreamManager from './components/StreamManager';
import ResultsViewer from './components/ResultsViewer';
import { StreamConfig, AIResult, DashboardStats } from './types';
import { api } from './services/api';
import { Monitor, Settings, BarChart3, AlertTriangle } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'streams' | 'results'>('dashboard');
  const [streams, setStreams] = useState<StreamConfig[]>([]);
  const [results, setResults] = useState<AIResult[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Fetch initial data
  useEffect(() => {
    fetchStreams();
    fetchResults();
    fetchStats();
    
    // Set up periodic updates
    const interval = setInterval(() => {
      fetchStats();
      fetchResults();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'ai_result') {
          setResults(prev => [...prev.slice(-99), message.data]);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  const fetchStreams = async () => {
    try {
      const response = await api.getStreams();
      setStreams(response.streams);
    } catch (error) {
      console.error('Error fetching streams:', error);
    }
  };

  const fetchResults = async () => {
    try {
      const response = await api.getResults({ limit: 100 });
      setResults(response.results);
    } catch (error) {
      console.error('Error fetching results:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.getDashboardStats();
      setStats(response);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleStreamUpdate = () => {
    fetchStreams();
    fetchStats();
  };

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Monitor },
    { id: 'streams', label: 'Stream Manager', icon: Settings },
    { id: 'results', label: 'Results', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Monitor className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-xl font-semibold text-gray-900">
                Video Management System
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              {/* Alert Indicator */}
              {stats && stats.alerts > 0 && (
                <div className="flex items-center space-x-1 text-red-600">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm font-medium">{stats.alerts} alerts</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <Dashboard 
            stats={stats} 
            streams={streams} 
            recentResults={results.slice(-10)} 
          />
        )}
        {activeTab === 'streams' && (
          <StreamManager 
            streams={streams} 
            onStreamUpdate={handleStreamUpdate} 
          />
        )}
        {activeTab === 'results' && (
          <ResultsViewer 
            results={results} 
            streams={streams} 
          />
        )}
      </main>
    </div>
  );
}

export default App;