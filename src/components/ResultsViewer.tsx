import React, { useState, useMemo } from 'react';
import { AIResult, StreamInfo } from '../types';
import { 
  Filter, 
  Download, 
  Search, 
  AlertTriangle, 
  Info, 
  Clock,
  TrendingUp,
  Eye
} from 'lucide-react';

interface ResultsViewerProps {
  results: AIResult[];
  streams: StreamInfo[];
}

const ResultsViewer: React.FC<ResultsViewerProps> = ({ results, streams }) => {
  const [filters, setFilters] = useState({
    streamId: '',
    modelName: '',
    alertLevel: '',
    searchTerm: ''
  });
  const [sortBy, setSortBy] = useState<'timestamp' | 'confidence' | 'alert_level'>('timestamp');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedResult, setSelectedResult] = useState<AIResult | null>(null);

  // Filter and sort results
  const filteredResults = useMemo(() => {
    let filtered = results.filter(result => {
      if (filters.streamId && result.stream_id !== filters.streamId) return false;
      if (filters.modelName && result.model_name !== filters.modelName) return false;
      if (filters.alertLevel && result.alert_level !== filters.alertLevel) return false;
      if (filters.searchTerm) {
        const searchLower = filters.searchTerm.toLowerCase();
        const searchableText = `${result.stream_id} ${result.model_name} ${JSON.stringify(result.results)}`.toLowerCase();
        if (!searchableText.includes(searchLower)) return false;
      }
      return true;
    });

    // Sort results
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'timestamp':
          aValue = new Date(a.timestamp).getTime();
          bValue = new Date(b.timestamp).getTime();
          break;
        case 'confidence':
          aValue = a.confidence;
          bValue = b.confidence;
          break;
        case 'alert_level':
          const alertOrder = { 'info': 0, 'warning': 1, 'critical': 2 };
          aValue = alertOrder[a.alert_level as keyof typeof alertOrder];
          bValue = alertOrder[b.alert_level as keyof typeof alertOrder];
          break;
        default:
          return 0;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [results, filters, sortBy, sortOrder]);

  // Get unique values for filter dropdowns
  const uniqueStreamIds = [...new Set(results.map(r => r.stream_id))];
  const uniqueModelNames = [...new Set(results.map(r => r.model_name))];

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'critical': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default: return <Info className="h-4 w-4 text-blue-500" />;
    }
  };

  const getAlertColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const exportResults = () => {
    const dataStr = JSON.stringify(filteredResults, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `vms_results_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const ResultDetailModal: React.FC<{ result: AIResult; onClose: () => void }> = ({ result, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Result Details</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ×
          </button>
        </div>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-700">Stream ID</p>
              <p className="text-gray-900">{result.stream_id}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700">Model</p>
              <p className="text-gray-900">{result.model_name}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700">Timestamp</p>
              <p className="text-gray-900">{new Date(result.timestamp).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700">Confidence</p>
              <p className="text-gray-900">{(result.confidence * 100).toFixed(1)}%</p>
            </div>
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Alert Level</p>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getAlertColor(result.alert_level)}`}>
              {getAlertIcon(result.alert_level)}
              <span className="ml-1 capitalize">{result.alert_level}</span>
            </span>
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Results</p>
            <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto">
              {JSON.stringify(result.results, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">AI Results</h2>
        <div className="flex items-center space-x-3">
          <span className="text-sm text-gray-600">
            {filteredResults.length} of {results.length} results
          </span>
          <button
            onClick={exportResults}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            <Download className="h-4 w-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Filter className="h-5 w-5 text-gray-600" />
          <h3 className="font-medium text-gray-900">Filters</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={filters.searchTerm}
                onChange={(e) => setFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
                className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Search results..."
              />
            </div>
          </div>

          {/* Stream Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Stream</label>
            <select
              value={filters.streamId}
              onChange={(e) => setFilters(prev => ({ ...prev, streamId: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Streams</option>
              {uniqueStreamIds.map(id => (
                <option key={id} value={id}>{id}</option>
              ))}
            </select>
          </div>

          {/* Model Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
            <select
              value={filters.modelName}
              onChange={(e) => setFilters(prev => ({ ...prev, modelName: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Models</option>
              {uniqueModelNames.map(name => (
                <option key={name} value={name}>{name.replace('_', ' ')}</option>
              ))}
            </select>
          </div>

          {/* Alert Level Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Alert Level</label>
            <select
              value={filters.alertLevel}
              onChange={(e) => setFilters(prev => ({ ...prev, alertLevel: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Levels</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          {/* Sort */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
            <div className="flex space-x-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="timestamp">Time</option>
                <option value="confidence">Confidence</option>
                <option value="alert_level">Alert Level</option>
              </select>
              <button
                onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
                className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <TrendingUp className={`h-4 w-4 ${sortOrder === 'desc' ? 'rotate-180' : ''}`} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Stream
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Alert Level
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredResults.map((result, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <Clock className="h-4 w-4 text-gray-400 mr-2" />
                      {new Date(result.timestamp).toLocaleString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {result.stream_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {result.model_name.replace('_', ' ')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getAlertColor(result.alert_level)}`}>
                      {getAlertIcon(result.alert_level)}
                      <span className="ml-1 capitalize">{result.alert_level}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${result.confidence * 100}%` }}
                        />
                      </div>
                      {(result.confidence * 100).toFixed(1)}%
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => setSelectedResult(result)}
                      className="text-blue-600 hover:text-blue-900 flex items-center space-x-1"
                    >
                      <Eye className="h-4 w-4" />
                      <span>View</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Empty State */}
        {filteredResults.length === 0 && (
          <div className="text-center py-12">
            <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
            <p className="text-gray-600">
              {results.length === 0 
                ? 'No AI results available yet. Start some streams to see results here.'
                : 'Try adjusting your filters to see more results.'
              }
            </p>
          </div>
        )}
      </div>

      {/* Result Detail Modal */}
      {selectedResult && (
        <ResultDetailModal 
          result={selectedResult} 
          onClose={() => setSelectedResult(null)} 
        />
      )}
    </div>
  );
};

export default ResultsViewer;