import cv2
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def check_video_sources() -> Dict[str, any]:
    """
    Comprehensive check of available video sources
    Returns dict with available sources and their details
    """
    sources = {
        "webcam": None,
        "sample_video": None,
        "available_cameras": [],
        "supported_formats": [],
        "system_info": get_system_info()
    }
    
    # Check webcam availability
    sources["webcam"] = check_webcam_availability()
    sources["available_cameras"] = get_available_cameras()
    
    # Check for sample video files
    sources["sample_video"] = find_sample_video()
    
    # Get supported video formats
    sources["supported_formats"] = get_supported_formats()
    
    # Log results
    logger.info(f"Video sources check complete: {sources}")
    
    return sources

def check_webcam_availability() -> bool:
    """
    Check if webcam is available and accessible
    """
    try:
        # Try to open default camera
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            # Try to read a frame to ensure it's working
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                logger.info("Webcam is available and working")
                return True
            else:
                logger.warning("Webcam detected but failed to capture frame")
                return False
        else:
            logger.warning("No webcam detected")
            return False
    except Exception as e:
        logger.error(f"Error checking webcam: {e}")
        return False

def get_available_cameras() -> List[Dict[str, any]]:
    """
    Get list of available cameras with their details
    """
    cameras = []
    
    # Check first 10 camera indices
    for i in range(10):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Get camera properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                # Try to capture a frame to verify it works
                ret, frame = cap.read()
                cap.release()
                
                if ret and frame is not None:
                    camera_info = {
                        "index": i,
                        "width": width,
                        "height": height,
                        "fps": fps,
                        "working": True
                    }
                    cameras.append(camera_info)
                    logger.info(f"Found working camera {i}: {width}x{height} @ {fps}fps")
                else:
                    logger.warning(f"Camera {i} detected but not working properly")
            else:
                cap.release()
        except Exception as e:
            logger.debug(f"Error checking camera {i}: {e}")
            continue
    
    return cameras

def find_sample_video() -> Optional[str]:
    """
    Find sample video files for testing
    """
    # Common sample video locations
    search_paths = [
        "sample_videos/",
        "test_videos/",
        "uploads/",
        "./",
        "../samples/",
        Path.home() / "Videos",
    ]
    
    # Common video extensions
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    
    for search_path in search_paths:
        try:
            path = Path(search_path)
            if path.exists() and path.is_dir():
                for ext in video_extensions:
                    video_files = list(path.glob(f"*{ext}"))
                    if video_files:
                        sample_video = str(video_files[0])
                        if validate_video_file(sample_video):
                            logger.info(f"Found sample video: {sample_video}")
                            return sample_video
        except Exception as e:
            logger.debug(f"Error searching in {search_path}: {e}")
    
    # Try to create a simple test video
    test_video = create_test_video()
    if test_video:
        return test_video
    
    logger.warning("No sample video found")
    return None

def validate_video_file(video_path: str) -> bool:
    """
    Validate that a video file can be opened and read
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            return ret and frame is not None
        return False
    except Exception as e:
        logger.error(f"Error validating video {video_path}: {e}")
        return False

def create_test_video(duration: int = 10) -> Optional[str]:
    """
    Create a simple test video if no sample videos are found
    """
    try:
        import numpy as np
        
        output_path = "test_video.mp4"
        width, height = 640, 480
        fps = 30
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            logger.error("Failed to create test video writer")
            return None
        
        # Generate frames
        total_frames = duration * fps
        for frame_num in range(total_frames):
            # Create a simple animated frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add moving circle
            center_x = int(width * (0.5 + 0.3 * np.sin(2 * np.pi * frame_num / fps)))
            center_y = height // 2
            cv2.circle(frame, (center_x, center_y), 30, (0, 255, 255), -1)
            
            # Add frame counter
            cv2.putText(frame, f"Frame {frame_num}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Add timestamp
            timestamp = f"Time: {frame_num/fps:.1f}s"
            cv2.putText(frame, timestamp, (10, height - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            out.write(frame)
        
        out.release()
        
        # Verify the created video
        if validate_video_file(output_path):
            logger.info(f"Created test video: {output_path}")
            return output_path
        else:
            logger.error("Failed to create valid test video")
            return None
            
    except Exception as e:
        logger.error(f"Error creating test video: {e}")
        return None

def get_supported_formats() -> List[str]:
    """
    Get list of supported video formats
    """
    # Common formats that OpenCV typically supports
    common_formats = [
        'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 
        'mpg', 'mpeg', '3gp', 'ogv', 'm4v'
    ]
    
    supported = []
    
    # Test each format by trying to create a VideoWriter
    for fmt in common_formats:
        try:
            fourcc_codes = {
                'mp4': 'mp4v',
                'avi': 'XVID',
                'mov': 'mp4v',
                'mkv': 'XVID',
                'wmv': 'WMV2',
                'flv': 'FLV1',
                'webm': 'VP80'
            }
            
            fourcc = fourcc_codes.get(fmt, 'XVID')
            test_writer = cv2.VideoWriter(
                f"test.{fmt}", 
                cv2.VideoWriter_fourcc(*fourcc), 
                30, 
                (640, 480)
            )
            
            if test_writer.isOpened():
                supported.append(fmt)
                test_writer.release()
                # Clean up test file
                try:
                    os.remove(f"test.{fmt}")
                except:
                    pass
        except Exception as e:
            logger.debug(f"Format {fmt} not supported: {e}")
    
    logger.info(f"Supported video formats: {supported}")
    return supported

def get_system_info() -> Dict[str, str]:
    """
    Get system information relevant to video processing
    """
    info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "opencv_version": cv2.__version__ if hasattr(cv2, '__version__') else "Unknown",
        "python_version": platform.python_version()
    }
    
    # Add GPU information if available
    try:
        if platform.system() == "Windows":
            # Try to get GPU info on Windows
            result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_info = result.stdout.strip().split('\n')[1:]
                info["gpu"] = [gpu.strip() for gpu in gpu_info if gpu.strip()]
        elif platform.system() == "Linux":
            # Try to get GPU info on Linux
            result = subprocess.run(['lspci', '-nn'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_lines = [line for line in result.stdout.split('\n') if 'VGA' in line or 'Display' in line]
                info["gpu"] = gpu_lines
    except Exception as e:
        logger.debug(f"Could not get GPU info: {e}")
        info["gpu"] = "Unknown"
    
    return info

def test_rtsp_connection(rtsp_url: str, timeout: int = 10) -> Dict[str, any]:
    """
    Test RTSP connection and get stream information
    """
    result = {
        "url": rtsp_url,
        "accessible": False,
        "error": None,
        "stream_info": {}
    }
    
    try:
        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Set timeout for opening
        start_time = cv2.getTickCount()
        
        if cap.isOpened():
            # Try to read a frame
            ret, frame = cap.read()
            
            if ret and frame is not None:
                result["accessible"] = True
                result["stream_info"] = {
                    "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    "fps": cap.get(cv2.CAP_PROP_FPS),
                    "frame_count": cap.get(cv2.CAP_PROP_FRAME_COUNT)
                }
                logger.info(f"RTSP stream accessible: {rtsp_url}")
            else:
                result["error"] = "Failed to read frame from RTSP stream"
                logger.warning(f"RTSP stream not readable: {rtsp_url}")
        else:
            result["error"] = "Failed to open RTSP stream"
            logger.warning(f"RTSP stream not accessible: {rtsp_url}")
        
        cap.release()
        
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error testing RTSP connection {rtsp_url}: {e}")
    
    return result

def optimize_capture_settings(cap: cv2.VideoCapture, source_type: str = "webcam") -> bool:
    """
    Optimize capture settings for better performance
    """
    try:
        if source_type == "webcam":
            # Webcam optimizations
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to avoid lag
            cap.set(cv2.CAP_PROP_FPS, 30)  # Set desired FPS
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set resolution
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        elif source_type == "rtsp":
            # RTSP optimizations
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer
            cap.set(cv2.CAP_PROP_TIMEOUT, 20000)  # 20 second timeout
        elif source_type == "file":
            # File optimizations
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Slightly larger buffer for files
        
        logger.info(f"Optimized capture settings for {source_type}")
        return True
        
    except Exception as e:
        logger.error(f"Error optimizing capture settings: {e}")
        return False

def get_video_info(video_path: str) -> Dict[str, any]:
    """
    Get detailed information about a video file
    """
    info = {
        "path": video_path,
        "exists": False,
        "accessible": False,
        "properties": {}
    }
    
    try:
        if os.path.exists(video_path):
            info["exists"] = True
            info["file_size"] = os.path.getsize(video_path)
            
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                info["accessible"] = True
                info["properties"] = {
                    "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    "fps": cap.get(cv2.CAP_PROP_FPS),
                    "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                    "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0,
                    "fourcc": int(cap.get(cv2.CAP_PROP_FOURCC))
                }
                cap.release()
            else:
                info["error"] = "Cannot open video file"
        else:
            info["error"] = "Video file does not exist"
            
    except Exception as e:
        info["error"] = str(e)
        logger.error(f"Error getting video info for {video_path}: {e}")
    
    return info

# Main function for testing
if __name__ == "__main__":
    print("=== Video Utils Test ===")
    sources = check_video_sources()
    
    for key, value in sources.items():
        print(f"{key}: {value}")
    
    print("\n=== System Info ===")
    sys_info = get_system_info()
    for key, value in sys_info.items():
        print(f"{key}: {value}")