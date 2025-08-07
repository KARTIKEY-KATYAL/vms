#!/usr/bin/env python3
"""
Simple test script to check if the main components work
"""

import sys
import traceback

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        from fastapi import FastAPI, WebSocket, HTTPException
        print("✓ FastAPI imports successful")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
        return False
    
    try:
        import cv2
        print(f"✓ OpenCV imported successfully (version: {cv2.__version__})")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✓ NumPy imported successfully (version: {np.__version__})")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✓ Uvicorn imported successfully")
    except ImportError as e:
        print(f"✗ Uvicorn import failed: {e}")
        return False
        
    return True

def test_local_modules():
    """Test local module imports"""
    print("\nTesting local modules...")
    
    try:
        from config import Config
        print("✓ Config module imported successfully")
        config = Config()
        print(f"✓ Config initialized: HOST={config.HOST}, PORT={config.PORT}")
    except ImportError as e:
        print(f"✗ Config import failed: {e}")
    except Exception as e:
        print(f"✗ Config initialization failed: {e}")
    
    try:
        from video_utils import check_video_sources
        print("✓ Video utils imported successfully")
        sources = check_video_sources()
        print(f"✓ Video sources check: {sources}")
    except ImportError as e:
        print(f"✗ Video utils import failed: {e}")
    except Exception as e:
        print(f"✗ Video utils execution failed: {e}")
    
    try:
        from ai_processor import AnthropicAIProcessor
        print("✓ AI processor imported successfully")
    except ImportError as e:
        print(f"✗ AI processor import failed: {e}")

def test_basic_app():
    """Test basic FastAPI app creation"""
    print("\nTesting FastAPI app creation...")
    
    try:
        from fastapi import FastAPI
        app = FastAPI(title="Test VMS", version="1.0.0")
        print("✓ FastAPI app created successfully")
        
        @app.get("/")
        async def root():
            return {"message": "Test API working"}
            
        print("✓ Basic route added successfully")
        return True
        
    except Exception as e:
        print(f"✗ FastAPI app creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    print("=== VMS Component Test ===")
    
    # Test imports
    if not test_imports():
        print("\n❌ Critical imports failed. Cannot proceed.")
        sys.exit(1)
    
    # Test local modules
    test_local_modules()
    
    # Test basic app
    if test_basic_app():
        print("\n✅ All basic tests passed!")
    else:
        print("\n❌ Some tests failed.")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
