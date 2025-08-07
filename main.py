from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import cv2
import numpy as np
from typing import Dict, List, Optional
import json
from datetime import datetime
import uuid
import threading
import base64
from pydantic import BaseModel
import os
from pathlib import Path
from dotenv import load_dotenv
import time
import logging
import uvicorn
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import local modules with error handling
try:
    from ai_processor import AnthropicAIProcessor
except ImportError:
    logger.warning("ai_processor module not found, using mock AI processor")
    AnthropicAIProcessor = None

try:
    from video_utils import check_video_sources
except ImportError:
    logger.warning("video_utils module not found, using basic video source checking")
    def check_video_sources():
        return {
            "webcam": True,  # Assume webcam is available
            "sample_video": None
        }

try:
    from config import Config
except ImportError:
    logger.warning("config module not found, using default configuration")
    class Config:
        CORS_ORIGINS = ["*"]
        HOST = "0.0.0.0"
        PORT = 8000
        FRAME_SKIP = 30
        MAX_RESULTS = 1000
        ENABLE_ANTHROPIC = False
        ANTHROPIC_API_KEY = None
        
        @classmethod
        def create_directories(cls):
            os.makedirs("uploads", exist_ok=True)
            os.makedirs("outputs", exist_ok=True)
        
        @classmethod
        def validate_config(cls):
            return True

# Initialize config
config = Config()
config.create_directories()
config.validate_config()

app = FastAPI(title="Video Management System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class StreamConfig(BaseModel):
    stream_id: str
    source: str  # 'webcam', 'rtsp', 'file'
    source_path: str
    ai_models: List[str]
    is_active: bool = False

class AIResult(BaseModel):
    stream_id: str
    model_name: str
    timestamp: datetime
    results: dict
    confidence: float
    alert_level: str  # 'info', 'warning', 'critical'

# Global variables with thread locks
streams: Dict[str, dict] = {}
ai_results: List[AIResult] = []
connected_clients: List[WebSocket] = []
results_lock = threading.Lock()
clients_lock = threading.Lock()

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# AI Models
class AIModel:
    def __init__(self, name: str):
        self.name = name
        self.anthropic_processor = None
        
        # Initialize Anthropic processor if available
        if AnthropicAIProcessor and config.ENABLE_ANTHROPIC and config.ANTHROPIC_API_KEY:
            try:
                self.anthropic_processor = AnthropicAIProcessor()
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic processor: {e}")
                self.anthropic_processor = None
    
    def process_frame(self, frame: np.ndarray) -> dict:
        """AI processing using Anthropic Claude Vision or mock data"""
        try:
            height, width = frame.shape[:2]
            
            # Use Anthropic AI if available
            if self.anthropic_processor:
                try:
                    analysis_type = {
                        "object_detection": "object_detection",
                        "defect_analysis": "defect_analysis", 
                        "asset_tracking": "asset_tracking"
                    }.get(self.name, "general")
                    
                    return self.anthropic_processor.analyze_frame(frame, analysis_type)
                except Exception as e:
                    logger.error(f"Anthropic API error, falling back to mock data: {e}")
            
            # Mock AI processing as fallback
            return self._get_mock_result(width, height)
        except Exception as e:
            logger.error(f"Error in AI processing: {e}")
            return {"error": str(e), "processed": False}
    
    def _get_mock_result(self, width: int, height: int) -> dict:
        """Generate mock AI results based on model type"""
        if self.name == "object_detection":
            return {
                "objects": [
                    {"class": "person", "confidence": 0.85, "bbox": [100, 100, 200, 300], "location": "center"},
                    {"class": "car", "confidence": 0.72, "bbox": [300, 150, 500, 400], "location": "right"}
                ],
                "count": 2,
                "frame_size": f"{width}x{height}",
                "analysis_type": "object_detection"
            }
        elif self.name == "defect_analysis":
            return {
                "defects": [
                    {"type": "scratch", "severity": "minor", "location": [150, 200], "confidence": 0.78}
                ],
                "defect_count": 1,
                "quality_score": 0.88,
                "frame_size": f"{width}x{height}",
                "analysis_type": "defect_analysis"
            }
        elif self.name == "asset_tracking":
            return {
                "assets": [
                    {"id": "asset_001", "type": "equipment", "status": "operational", "location": "zone_a"}
                ],
                "total_assets": 1,
                "frame_size": f"{width}x{height}",
                "analysis_type": "asset_tracking"
            }
        else:
            return {
                "processed": True, 
                "frame_size": f"{width}x{height}",
                "analysis_type": "general",
                "timestamp": datetime.now().isoformat()
            }

# Available AI models
available_models = {
    "object_detection": AIModel("object_detection"),
    "defect_analysis": AIModel("defect_analysis"),
    "asset_tracking": AIModel("asset_tracking")
}

class VideoProcessor:
    def __init__(self, stream_id: str, stream_config: StreamConfig):
        self.stream_id = stream_id
        self.config = stream_config
        self.cap = None
        self.is_running = False
        self.thread = None
        self.frame_count = 0
        self.last_process_time = 0
        
    def start(self):
        """Start video processing"""
        if self.is_running:
            logger.info(f"Stream {self.stream_id} is already running")
            return False
            
        self.is_running = True
        self.thread = threading.Thread(target=self._process_video, daemon=True)
        self.thread.start()
        logger.info(f"Started stream {self.stream_id}")
        return True
        
    def stop(self):
        """Stop video processing"""
        if not self.is_running:
            return
            
        logger.info(f"Stopping stream {self.stream_id}")
        self.is_running = False
        
        if self.cap:
            self.cap.release()
            
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
            
    def _process_video(self):
        """Process video frames in separate thread"""
        try:
            # Initialize video capture with error handling
            if not self._initialize_capture():
                logger.error(f"Failed to initialize capture for stream {self.stream_id}")
                return
                
            logger.info(f"Processing video for stream {self.stream_id}")
            
            while self.is_running:
                try:
                    ret, frame = self.cap.read()
                    if not ret:
                        if self.config.source == "file":
                            # Restart file playback
                            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                        else:
                            logger.warning(f"Failed to read frame from stream {self.stream_id}")
                            break
                    
                    # Process every Nth frame to reduce load
                    if self.frame_count % config.FRAME_SKIP == 0:
                        self._process_frame_async(frame)
                        
                    self.frame_count += 1
                    
                    # Limit FPS to prevent overwhelming the system
                    time.sleep(0.033)  # ~30 FPS
                    
                except Exception as e:
                    logger.error(f"Error processing frame in stream {self.stream_id}: {e}")
                    time.sleep(1)  # Wait before retrying
                    
        except Exception as e:
            logger.error(f"Fatal error in video processing for stream {self.stream_id}: {e}")
        finally:
            self._cleanup()
            
    def _initialize_capture(self) -> bool:
        """Initialize video capture based on source type"""
        try:
            if self.config.source == "webcam":
                self.cap = cv2.VideoCapture(int(self.config.source_path))
            elif self.config.source == "rtsp":
                self.cap = cv2.VideoCapture(self.config.source_path)
            elif self.config.source == "file":
                if not os.path.exists(self.config.source_path):
                    logger.error(f"Video file not found: {self.config.source_path}")
                    return False
                self.cap = cv2.VideoCapture(self.config.source_path)
            else:
                logger.error(f"Unknown source type: {self.config.source}")
                return False
                
            if not self.cap or not self.cap.isOpened():
                logger.error(f"Failed to open video source: {self.config.source_path}")
                return False
                
            # Set capture properties for better performance
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return True
            
        except Exception as e:
            logger.error(f"Exception initializing capture: {e}")
            return False
            
    def _cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info(f"Cleaned up resources for stream {self.stream_id}")
            
    def _process_frame_async(self, frame: np.ndarray):
        """Process frame with AI models"""
        # Limit processing frequency
        current_time = time.time()
        if current_time - self.last_process_time < 1.0:  # Process at most once per second
            return
        self.last_process_time = current_time
        
        for model_name in self.config.ai_models:
            if model_name in available_models:
                try:
                    model = available_models[model_name]
                    results = model.process_frame(frame)
                    
                    # Create AI result
                    ai_result = AIResult(
                        stream_id=self.stream_id,
                        model_name=model_name,
                        timestamp=datetime.now(),
                        results=results,
                        confidence=results.get('confidence', random.uniform(0.7, 0.95)),
                        alert_level=self._determine_alert_level(results)
                    )
                    
                    # Store result with thread safety
                    with results_lock:
                        ai_results.append(ai_result)
                        # Keep only configured number of results
                        if len(ai_results) > config.MAX_RESULTS:
                            ai_results.pop(0)
                    
                    # Schedule broadcast in the event loop
                    asyncio.run_coroutine_threadsafe(
                        self._broadcast_result(ai_result),
                        asyncio.get_event_loop()
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing frame with {model_name}: {e}")
                    
    def _determine_alert_level(self, results: dict) -> str:
        """Determine alert level based on results"""
        try:
            if "error" in results:
                return "critical"
            
            # Check for defects
            if "defects" in results:
                defects = results["defects"]
                if isinstance(defects, list) and len(defects) > 0:
                    severe_defects = [d for d in defects if d.get("severity") == "severe"]
                    if severe_defects:
                        return "critical"
                    moderate_defects = [d for d in defects if d.get("severity") == "moderate"]
                    if moderate_defects:
                        return "warning"
                    return "warning"
            
            # Check for high object count
            if "objects" in results:
                objects = results["objects"]
                if isinstance(objects, list):
                    if len(objects) > 10:
                        return "warning"
                    elif len(objects) > 5:
                        return "info"
            
            # Check for asset issues
            if "assets" in results:
                assets = results["assets"]
                if isinstance(assets, list):
                    for asset in assets:
                        if asset.get("status") in ["maintenance", "inactive", "error"]:
                            return "warning"
            
            # Check confidence levels
            confidence = results.get("confidence", 1.0)
            if confidence < 0.5:
                return "warning"
            
            return "info"
        except Exception as e:
            logger.error(f"Error determining alert level: {e}")
            return "info"
            
    async def _broadcast_result(self, result: AIResult):
        """Broadcast result to connected WebSocket clients"""
        if not connected_clients:
            return
            
        message = {
            "type": "ai_result",
            "data": {
                "stream_id": result.stream_id,
                "model_name": result.model_name,
                "timestamp": result.timestamp.isoformat(),
                "results": result.results,
                "confidence": result.confidence,
                "alert_level": result.alert_level
            }
        }
        
        with clients_lock:
            clients_to_remove = []
            for client in connected_clients:
                try:
                    await client.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send message to client: {e}")
                    clients_to_remove.append(client)
            
            # Remove disconnected clients
            for client in clients_to_remove:
                connected_clients.remove(client)

# API Routes
@app.get("/")
async def root():
    return {"message": "Video Management System API", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/streams")
async def get_streams():
    """Get all streams with their current status"""
    stream_list = []
    for stream_id, data in streams.items():
        try:
            stream_info = {
                "stream_id": stream_id,
                "config": {
                    "source": data["config"].source,
                    "source_path": data["config"].source_path,
                    "ai_models": data["config"].ai_models,
                    "is_active": data["config"].is_active
                },
                "is_running": data["processor"].is_running if data["processor"] else False,
                "last_update": data.get("last_update", "Never"),
                "frame_count": data["processor"].frame_count if data["processor"] else 0
            }
            stream_list.append(stream_info)
        except Exception as e:
            logger.error(f"Error getting stream info for {stream_id}: {e}")
            
    return {"streams": stream_list, "total": len(stream_list)}

@app.post("/streams")
async def create_stream(config: StreamConfig):
    """Create a new stream"""
    try:
        if not config.stream_id:
            config.stream_id = str(uuid.uuid4())
            
        if config.stream_id in streams:
            raise HTTPException(status_code=400, detail="Stream already exists")
        
        # Validate AI models
        invalid_models = [model for model in config.ai_models if model not in available_models]
        if invalid_models:
            raise HTTPException(status_code=400, detail=f"Invalid AI models: {invalid_models}")
            
        # Create processor
        processor = VideoProcessor(config.stream_id, config)
        
        streams[config.stream_id] = {
            "config": config,
            "processor": processor,
            "last_update": datetime.now().isoformat()
        }
        
        logger.info(f"Created stream: {config.stream_id}")
        return {"message": "Stream created", "stream_id": config.stream_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/streams/{stream_id}/start")
async def start_stream(stream_id: str):
    """Start a stream"""
    if stream_id not in streams:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    try:
        processor = streams[stream_id]["processor"]
        if processor.start():
            streams[stream_id]["config"].is_active = True
            streams[stream_id]["last_update"] = datetime.now().isoformat()
            return {"message": "Stream started", "stream_id": stream_id}
        else:
            raise HTTPException(status_code=400, detail="Stream is already running")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting stream {stream_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/streams/{stream_id}/stop")
async def stop_stream(stream_id: str):
    """Stop a stream"""
    if stream_id not in streams:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    try:
        processor = streams[stream_id]["processor"]
        processor.stop()
        streams[stream_id]["config"].is_active = False
        streams[stream_id]["last_update"] = datetime.now().isoformat()
        
        logger.info(f"Stopped stream: {stream_id}")
        return {"message": "Stream stopped", "stream_id": stream_id}
    except Exception as e:
        logger.error(f"Error stopping stream {stream_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/streams/{stream_id}")
async def delete_stream(stream_id: str):
    """Delete a stream"""
    if stream_id not in streams:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    try:
        processor = streams[stream_id]["processor"]
        processor.stop()
        del streams[stream_id]
        
        logger.info(f"Deleted stream: {stream_id}")
        return {"message": "Stream deleted", "stream_id": stream_id}
    except Exception as e:
        logger.error(f"Error deleting stream {stream_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai-models")
async def get_ai_models():
    """Get available AI models"""
    models_info = {}
    for name, model in available_models.items():
        models_info[name] = {
            "name": name,
            "anthropic_enabled": model.anthropic_processor is not None,
            "description": f"AI model for {name.replace('_', ' ')}"
        }
    
    return {"models": models_info, "total": len(available_models)}

@app.get("/results")
async def get_results(stream_id: Optional[str] = None, limit: int = 100, alert_level: Optional[str] = None):
    """Get AI results with filtering options"""
    try:
        with results_lock:
            filtered_results = ai_results.copy()
        
        # Filter by stream_id
        if stream_id:
            filtered_results = [r for r in filtered_results if r.stream_id == stream_id]
        
        # Filter by alert level
        if alert_level:
            filtered_results = [r for r in filtered_results if r.alert_level == alert_level]
            
        # Convert to dict for JSON serialization
        results_data = []
        for result in filtered_results[-limit:]:
            results_data.append({
                "stream_id": result.stream_id,
                "model_name": result.model_name,
                "timestamp": result.timestamp.isoformat(),
                "results": result.results,
                "confidence": result.confidence,
                "alert_level": result.alert_level
            })
            
        return {
            "results": results_data,
            "total": len(results_data),
            "filters": {
                "stream_id": stream_id,
                "alert_level": alert_level,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        active_streams = len([s for s in streams.values() if s["processor"].is_running])
        total_streams = len(streams)
        
        with results_lock:
            # Results in the last minute
            recent_results = len([r for r in ai_results if (datetime.now() - r.timestamp).seconds < 60])
            # Alerts in the last 5 minutes
            recent_alerts = [r for r in ai_results if 
                           r.alert_level in ["warning", "critical"] and 
                           (datetime.now() - r.timestamp).seconds < 300]
            alerts = len(recent_alerts)
            
            # Alert breakdown
            alert_breakdown = {
                "critical": len([r for r in recent_alerts if r.alert_level == "critical"]),
                "warning": len([r for r in recent_alerts if r.alert_level == "warning"])
            }
        
        return {
            "active_streams": active_streams,
            "total_streams": total_streams,
            "recent_results": recent_results,
            "alerts": alerts,
            "alert_breakdown": alert_breakdown,
            "uptime": "Running",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    
    with clients_lock:
        connected_clients.append(websocket)
    
    logger.info(f"New WebSocket connection. Total clients: {len(connected_clients)}")
    
    try:
        while True:
            # Keep connection alive and handle ping messages
            try:
                data = await websocket.receive_text()
                # Echo back ping messages
                if data == "ping":
                    await websocket.send_text("pong")
            except Exception as e:
                logger.info(f"WebSocket receive error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    finally:
        with clients_lock:
            if websocket in connected_clients:
                connected_clients.remove(websocket)
        logger.info(f"WebSocket connection closed. Remaining clients: {len(connected_clients)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Create sample streams on startup"""
    logger.info("Starting Video Management System...")
    
    try:
        # Check video sources
        sources = check_video_sources()
        logger.info(f"Video sources: {sources}")
        
        # Create sample streams
        sample_configs = []
        
        # Add webcam if available
        if sources.get("webcam"):
            sample_configs.append(
                StreamConfig(
                    stream_id="demo_webcam",
                    source="webcam",
                    source_path="0",
                    ai_models=["object_detection", "asset_tracking"]
                )
            )
        
        # Add sample video if available
        if sources.get("sample_video"):
            sample_configs.append(
                StreamConfig(
                    stream_id="demo_file",
                    source="file",
                    source_path=sources["sample_video"],
                    ai_models=["defect_analysis", "object_detection"]
                )
            )
        
        # Add RTSP example (won't work without actual RTSP stream)
        sample_configs.append(
            StreamConfig(
                stream_id="demo_rtsp",
                source="rtsp",
                source_path="rtsp://example.com/stream",
                ai_models=["asset_tracking"]
            )
        )
        
        # Create sample streams
        for stream_config in sample_configs:
            if stream_config.stream_id not in streams:
                processor = VideoProcessor(stream_config.stream_id, stream_config)
                streams[stream_config.stream_id] = {
                    "config": stream_config,
                    "processor": processor,
                    "last_update": datetime.now().isoformat()
                }
                logger.info(f"Created sample stream: {stream_config.stream_id}")
        
        logger.info(f"VMS startup complete. Created {len(sample_configs)} sample streams.")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger.info("Shutting down Video Management System...")
    
    # Stop all streams
    for stream_id, data in streams.items():
        try:
            processor = data["processor"]
            processor.stop()
            logger.info(f"Stopped stream: {stream_id}")
        except Exception as e:
            logger.error(f"Error stopping stream {stream_id}: {e}")
    
    logger.info("VMS shutdown complete.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")