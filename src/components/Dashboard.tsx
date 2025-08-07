import React from 'react';
import { DashboardStats, StreamInfo, AIResult } from '../types';
import { 
  Monitor, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  TrendingUp,
  Camera,
  Zap
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface DashboardProps {
  stats: DashboardStats | null;
  streams: StreamInfo[];
  recentResults: AIResult[];
}

const Dashboard: React.FC<DashboardProps> = ({ stats, streams, recentResults }) => {
  // Generate chart data from recent results
  const chartData = React.useMemo(() => {
    const last24Hours = recentResults
      .filter(result => {
        const resultTime = new Date(result.timestamp);
        const now = new Date();
        return (now.getTime() - resultTime.getTime()) < 24 * 60 * 60 * 1000;
      })
      .reduce((acc, result) => {
        const hour = new Date(result.timestamp).getHours();
        const key = `${hour}:00`;
        if (!acc[key]) {
          acc[key] = { time: key, results: 0, alerts: 0 };
        }
        acc[key].results++;
        if (result.alert_level === 'warning' || result.alert_level === 'critical') {
          acc[key].alerts++;
        }
        return acc;
      }, {} as Record<string, any>);

    return Object.values(chartData).slice(-12);
  }, [recentResults]);

  // Model performance data
  const modelData = React.useMemo(() => {
    const modelStats = recentResults.reduce((acc, result) => {
      if (!acc[result.model_name]) {
        acc[result.model_name] = { name: result.model_name, count: 0, avgConfidence: 0, totalConfidence: 0 };
      }
      acc[result.model_name].count++;
      acc[result.model_name].totalConfidence += result.confidence;
      acc[result.model_name].avgConfidence = acc[result.model_name].totalConfidence / acc[result.model_name].count;
      return acc;
    }, {} as Record<string, any>);

    return Object.values(modelStats);
  }, [recentResults]);

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ElementType;
    color: string;
    trend?: string;
  }> = ({ title, value, icon: Icon, color, trend }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`flex-shrink-0 p-3 rounded-lg ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="flex items-center">
            <p className="text-2xl font-semibold text-gray-900">{value}</p>
            {trend && (
              <span className="ml-2 text-sm text-green-600 flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" />
                {trend}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Dashboard Overview</h2>
        <div className="text-sm text-gray-500">
          Last updated: {stats?.timestamp ? new Date(stats.timestamp).toLocaleTimeString() : 'Never'}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Active Streams"
          value={stats?.active_streams || 0}
          icon={Monitor}
          color="bg-blue-500"
          trend={stats?.active_streams ? `${stats.active_streams}/${stats.total_streams}` : undefined}
        />
        <StatCard
          title="Recent Results"
          value={stats?.recent_results || 0}
          icon={Activity}
          color="bg-green-500"
          trend="last minute"
        />
        <StatCard
          title="Active Alerts"
          value={stats?.alerts || 0}
          icon={AlertTriangle}
          color="bg-red-500"
        />
        <StatCard
          title="System Status"
          value="Online"
          icon={CheckCircle}
          color="bg-emerald-500"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Activity Over Time</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="results" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  name="Results"
                />
                <Line 
                  type="monotone" 
                  dataKey="alerts" 
                  stroke="#ef4444" 
                  strokeWidth={2}
                  name="Alerts"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Model Performance */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Performance</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={modelData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" name="Results Count" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Stream Status and Recent Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stream Status */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Camera className="h-5 w-5 mr-2" />
              Stream Status
            </h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {streams.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No streams configured</p>
              ) : (
                streams.map((stream) => (
                  <div key={stream.stream_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${
                        stream.is_running ? 'bg-green-500' : 'bg-gray-400'
                      }`} />
                      <div>
                        <p className="font-medium text-gray-900">{stream.stream_id}</p>
                        <p className="text-sm text-gray-500">{stream.source} • {stream.ai_models.length} models</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {stream.frame_count.toLocaleString()} frames
                      </p>
                      <p className="text-xs text-gray-500">
                        {stream.is_running ? 'Running' : 'Stopped'}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              Recent Alerts
            </h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {recentResults
                .filter(result => result.alert_level === 'warning' || result.alert_level === 'critical')
                .slice(-5)
                .map((result, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                    <div className={`w-2 h-2 rounded-full mt-2 ${
                      result.alert_level === 'critical' ? 'bg-red-500' : 'bg-yellow-500'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        {result.model_name} - {result.stream_id}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(result.timestamp).toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        Confidence: {(result.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      result.alert_level === 'critical' 
                        ? 'bg-red-100 text-red-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {result.alert_level}
                    </span>
                  </div>
                ))}
              {recentResults.filter(r => r.alert_level === 'warning' || r.alert_level === 'critical').length === 0 && (
                <p className="text-gray-500 text-center py-4">No recent alerts</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* System Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Zap className="h-5 w-5 mr-2" />
          System Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{stats?.total_streams || 0}</p>
            <p className="text-sm text-gray-600">Total Streams</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{recentResults.length}</p>
            <p className="text-sm text-gray-600">Total Results</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">
              {stats?.uptime || 'Running'}
            </p>
            <p className="text-sm text-gray-600">System Status</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;