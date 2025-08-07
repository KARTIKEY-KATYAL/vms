import os
from pathlib import Path
from typing import List, Tuple

class Config:
    """Enhanced configu            elif len(cls.ANTHROPIC_API_KEY) < 10:
                return {
                    "valid": False,
                    "message": "Invalid Anthropic API key format",
                    "warnings": ["Check ANTHROPIC_API_KEY format"]
                }
            else:
                return {
                    "valid": True,
                    "message": "Anthropic AI configured and ready"
                }ings for VMS with validation and defaults"""
    
    # API Configuration
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')
    
    # Server Configuration
    HOST = os.getenv('BACKEND_HOST', '0.0.0.0')
    PORT = int(os.getenv('BACKEND_PORT', 8000))
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # File Storage Configuration
    UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', 'uploads'))
    OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', 'outputs'))
    LOGS_DIR = Path(os.getenv('LOGS_DIR', 'logs'))
    MAX_FILE_SIZE = os.getenv('MAX_FILE_SIZE', '100MB')
    
    # Processing Configuration
    FRAME_SKIP = max(1, int(os.getenv('FRAME_SKIP', 30)))  # Process every Nth frame
    MAX_RESULTS = max(100, int(os.getenv('MAX_RESULTS', 1000)))  # Max results to keep in memory
    MAX_CONCURRENT_STREAMS = int(os.getenv('MAX_CONCURRENT_STREAMS', 10))
    
    # AI Configuration
    AI_CONFIDENCE_THRESHOLD = max(0.0, min(1.0, float(os.getenv('AI_CONFIDENCE_THRESHOLD', 0.5))))
    ENABLE_ANTHROPIC = os.getenv('ENABLE_ANTHROPIC', 'true').lower() == 'true'
    AI_PROCESSING_TIMEOUT = int(os.getenv('AI_PROCESSING_TIMEOUT', 30))  # seconds
    
    # Video Configuration
    DEFAULT_FPS = max(1, int(os.getenv('DEFAULT_FPS', 30)))
    VIDEO_RESOLUTION = tuple(map(int, os.getenv('VIDEO_RESOLUTION', '640,480').split(',')))
    WEBCAM_TIMEOUT = int(os.getenv('WEBCAM_TIMEOUT', 5))  # seconds
    RTSP_TIMEOUT = int(os.getenv('RTSP_TIMEOUT', 10))  # seconds
    
    # CORS Configuration
    CORS_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ORIGINS', '*').split(',')]
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ENABLE_FILE_LOGGING = os.getenv('ENABLE_FILE_LOGGING', 'true').lower() == 'true'
    
    # Performance Configuration
    THREAD_POOL_SIZE = int(os.getenv('THREAD_POOL_SIZE', 4))
    MEMORY_LIMIT_MB = int(os.getenv('MEMORY_LIMIT_MB', 2048))
    
    # Security Configuration
    ENABLE_RATE_LIMITING = os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true'
    MAX_REQUESTS_PER_MINUTE = int(os.getenv('MAX_REQUESTS_PER_MINUTE', 60))
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories with proper permissions"""
        directories = [cls.UPLOAD_DIR, cls.OUTPUT_DIR, cls.LOGS_DIR]
        
        for directory in directories:
            try:
                directory.mkdir(exist_ok=True, parents=True)
                print(f"✓ Created directory: {directory}")
            except Exception as e:
                print(f"✗ Failed to create directory {directory}: {e}")
                raise
    
    @classmethod
    def validate_config(cls):
        """Validate configuration and show warnings"""
        validation_results = {
            "anthropic": cls._validate_anthropic(),
            "clerk": cls._validate_clerk(),
            "video": cls._validate_video_config(),
            "directories": cls._validate_directories(),
            "performance": cls._validate_performance()
        }
        
        # Print validation summary
        print("\n=== VMS Configuration Validation ===")
        for component, result in validation_results.items():
            status = "✓" if result["valid"] else "✗"
            print(f"{status} {component.title()}: {result['message']}")
            
            if result.get("warnings"):
                for warning in result["warnings"]:
                    print(f"  ⚠️  {warning}")
        
        print("=" * 37)
        
        # Check if any critical validations failed
        critical_failures = [comp for comp, result in validation_results.items() 
                           if not result["valid"] and result.get("critical", False)]
        
        if critical_failures:
            raise ValueError(f"Critical configuration errors in: {', '.join(critical_failures)}")
        
        return all(result["valid"] for result in validation_results.values())
    
    @classmethod
    def _validate_anthropic(cls):
        """Validate Anthropic AI configuration"""
        if cls.ENABLE_ANTHROPIC:
            if not cls.ANTHROPIC_API_KEY:
                return {
                    "valid": False,
                    "message": "Anthropic enabled but API key missing",
                    "warnings": ["Add ANTHROPIC_API_KEY to environment variables"]
                }
            elif len(cls.ANTHROPIC_API_KEY) < 10:
                return {
                    "valid": False,
                    "message": "Anthropic API key appears invalid",
                    "warnings": ["Check ANTHROPIC_API_KEY format"]
                }
            else:
                return {
                    "valid": True,
                    "message": "Anthropic AI configured"
                }
        else:
            return {
                "valid": True,
                "message": "Anthropic AI disabled (using mock data)"
            }
    
    @classmethod
    def _validate_clerk(cls):
        """Validate Clerk authentication configuration"""
        if cls.CLERK_SECRET_KEY:
            return {
                "valid": True,
                "message": "Clerk authentication configured"
            }
        else:
            return {
                "valid": True,
                "message": "Clerk authentication not configured",
                "warnings": ["Authentication features may not work"]
            }
    
    @classmethod
    def _validate_video_config(cls):
        """Validate video processing configuration"""
        warnings = []
        
        if cls.FRAME_SKIP < 10:
            warnings.append("Low FRAME_SKIP may cause high CPU usage")
        elif cls.FRAME_SKIP > 100:
            warnings.append("High FRAME_SKIP may miss important events")
        
        if cls.DEFAULT_FPS > 60:
            warnings.append("High FPS may impact performance")
        
        if cls.VIDEO_RESOLUTION[0] * cls.VIDEO_RESOLUTION[1] > 1920 * 1080:
            warnings.append("High resolution may impact performance")
        
        return {
            "valid": True,
            "message": f"Video config: {cls.VIDEO_RESOLUTION}, {cls.DEFAULT_FPS}fps",
            "warnings": warnings
        }
    
    @classmethod
    def _validate_directories(cls):
        """Validate directory configuration"""
        try:
            # Check if directories exist and are writable
            for directory in [cls.UPLOAD_DIR, cls.OUTPUT_DIR, cls.LOGS_DIR]:
                if not directory.exists():
                    return {
                        "valid": False,
                        "message": f"Directory missing: {directory}",
                        "critical": True
                    }
                
                # Test write access
                test_file = directory / ".write_test"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                except Exception:
                    return {
                        "valid": False,
                        "message": f"No write access to: {directory}",
                        "critical": True
                    }
            
            return {
                "valid": True,
                "message": "All directories accessible"
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"Directory validation error: {e}",
                "critical": True
            }
    
    @classmethod
    def _validate_performance(cls):
        """Validate performance configuration"""
        warnings = []
        
        if cls.MAX_RESULTS > 10000:
            warnings.append("High MAX_RESULTS may consume excessive memory")
        
        if cls.MAX_CONCURRENT_STREAMS > 20:
            warnings.append("High concurrent streams may impact performance")
        
        if cls.THREAD_POOL_SIZE > 10:
            warnings.append("Large thread pool may cause resource contention")
        
        if cls.MEMORY_LIMIT_MB < 512:
            warnings.append("Low memory limit may cause performance issues")
        
        return {
            "valid": True,
            "message": f"Performance limits: {cls.MAX_CONCURRENT_STREAMS} streams, {cls.MEMORY_LIMIT_MB}MB",
            "warnings": warnings
        }
    
    @classmethod
    def get_opencv_config(cls):
        """Get OpenCV-specific configuration"""
        return {
            "resolution": cls.VIDEO_RESOLUTION,
            "fps": cls.DEFAULT_FPS,
            "buffer_size": 1,
            "timeout": cls.WEBCAM_TIMEOUT,
            "codec": "MJPG"  # Default codec
        }
    
    @classmethod
    def get_ai_config(cls):
        """Get AI processing configuration"""
        return {
            "confidence_threshold": cls.AI_CONFIDENCE_THRESHOLD,
            "enable_anthropic": cls.ENABLE_ANTHROPIC,
            "processing_timeout": cls.AI_PROCESSING_TIMEOUT,
            "frame_skip": cls.FRAME_SKIP
        }
    
    @classmethod
    def get_server_config(cls):
        """Get server configuration"""
        return {
            "host": cls.HOST,
            "port": cls.PORT,
            "debug": cls.DEBUG,
            "cors_origins": cls.CORS_ORIGINS,
            "log_level": cls.LOG_LEVEL
        }
    
    @classmethod
    def print_config_summary(cls):
        """Print a summary of current configuration"""
        print("\n=== VMS Configuration Summary ===")
        print(f"Server: {cls.HOST}:{cls.PORT}")
        print(f"Anthropic AI: {'Enabled' if cls.ENABLE_ANTHROPIC else 'Disabled'}")
        print(f"Max Streams: {cls.MAX_CONCURRENT_STREAMS}")
        print(f"Frame Skip: {cls.FRAME_SKIP}")
        print(f"Max Results: {cls.MAX_RESULTS}")
        print(f"Video Resolution: {cls.VIDEO_RESOLUTION[0]}x{cls.VIDEO_RESOLUTION[1]}")
        print(f"Upload Dir: {cls.UPLOAD_DIR}")
        print(f"Output Dir: {cls.OUTPUT_DIR}")
        print("=" * 33)

# Create and validate configuration instance
config = Config()
config.create_directories()

# Only validate if this module is run directly
if __name__ == "__main__":
    config.validate_config()
    config.print_config_summary()