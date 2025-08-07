export interface StreamConfig {
  stream_id: string;
  source: 'webcam' | 'rtsp' | 'file';
  source_path: string;
  ai_models: string[];
  is_active: boolean;
}

export interface StreamInfo extends StreamConfig {
  is_running: boolean;
  last_update: string;
  frame_count: number;
}

export interface AIResult {
  stream_id: string;
  model_name: string;
  timestamp: string;
  results: any;
  confidence: number;
  alert_level: 'info' | 'warning' | 'critical';
}

export interface DashboardStats {
  active_streams: number;
  total_streams: number;
  recent_results: number;
  alerts: number;
  alert_breakdown: {
    critical: number;
    warning: number;
  };
  uptime: string;
  timestamp: string;
}

export interface AIModel {
  name: string;
  anthropic_enabled: boolean;
  description: string;
}