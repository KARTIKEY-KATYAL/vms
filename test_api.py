"""
Test script for VMS API endpoints
Run this after starting the backend server
"""

import requests
import json
import time
import websocket
import threading

API_BASE = "http://localhost:8000"

def test_basic_endpoints():
    """Test basic API endpoints"""
    print("=== Testing Basic Endpoints ===")
    
    # Test root endpoint
    response = requests.get(f"{API_BASE}/")
    print(f"Root endpoint: {response.status_code} - {response.json()}")
    
    # Test streams endpoint
    response = requests.get(f"{API_BASE}/streams")
    print(f"Streams endpoint: {response.status_code}")
    streams_data = response.json()
    print(f"Found {len(streams_data['streams'])} streams")
    
    # Test AI models endpoint
    response = requests.get(f"{API_BASE}/ai-models")
    print(f"AI Models endpoint: {response.status_code}")
    models_data = response.json()
    print(f"Available models: {models_data['models']}")
    
    # Test dashboard stats
    response = requests.get(f"{API_BASE}/dashboard/stats")
    print(f"Dashboard stats: {response.status_code}")
    stats = response.json()
    print(f"Stats: {stats}")
    
    return streams_data['streams']

def test_stream_operations():
    """Test stream creation and operations"""
    print("\n=== Testing Stream Operations ===")
    
    # Create a test stream
    stream_config = {
        "stream_id": "test_stream_" + str(int(time.time())),
        "source": "webcam",
        "source_path": "0",
        "ai_models": ["object_detection"]
    }
    
    # Create stream
    response = requests.post(f"{API_BASE}/streams", json=stream_config)
    print(f"Create stream: {response.status_code}")
    
    if response.status_code == 200:
        stream_id = stream_config['stream_id']
        
        # Start stream
        response = requests.post(f"{API_BASE}/streams/{stream_id}/start")
        print(f"Start stream: {response.status_code}")
        
        # Wait a bit
        time.sleep(2)
        
        # Check stream status
        response = requests.get(f"{API_BASE}/streams")
        streams = response.json()['streams']
        test_stream = next((s for s in streams if s['stream_id'] == stream_id), None)
        if test_stream:
            print(f"Stream active: {test_stream['is_active']}")
        
        # Stop stream
        response = requests.post(f"{API_BASE}/streams/{stream_id}/stop")
        print(f"Stop stream: {response.status_code}")
        
        # Delete stream
        response = requests.delete(f"{API_BASE}/streams/{stream_id}")
        print(f"Delete stream: {response.status_code}")

def test_results_endpoint():
    """Test results endpoint"""
    print("\n=== Testing Results Endpoint ===")
    
    response = requests.get(f"{API_BASE}/results?limit=10")
    print(f"Results endpoint: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json()['results']
        print(f"Found {len(results)} results")
        
        if results:
            latest = results[-1]
            print(f"Latest result: Stream {latest['stream_id']}, Model {latest['model_name']}")
            print(f"Confidence: {latest['confidence']:.2f}, Alert: {latest['alert_level']}")

def on_websocket_message(ws, message):
    """Handle WebSocket messages"""
    try:
        data = json.loads(message)
        if data.get('type') == 'ai_result':
            result = data['data']
            print(f"WS Result: {result['stream_id']} - {result['model_name']} - {result['alert_level']}")
    except:
        pass

def test_websocket():
    """Test WebSocket connection"""
    print("\n=== Testing WebSocket Connection ===")
    
    def run_websocket():
        ws = websocket.WebSocketApp(
            "ws://localhost:8000/ws",
            on_message=on_websocket_message,
            on_error=lambda ws, error: print(f"WS Error: {error}"),
            on_close=lambda ws, close_status_code, close_msg: print("WS Closed"),
            on_open=lambda ws: print("WS Connected")
        )
        ws.run_forever()
    
    # Run WebSocket in separate thread
    ws_thread = threading.Thread(target=run_websocket, daemon=True)
    ws_thread.start()
    
    # Wait for connection and some messages
    time.sleep(3)
    print("WebSocket test completed (check output above)")

def main():
    """Run all tests"""
    print("VMS API Test Suite")
    print("Make sure the backend server is running on localhost:8000")
    print("-" * 50)
    
    try:
        # Test basic endpoints
        streams = test_basic_endpoints()
        
        # Test stream operations
        test_stream_operations()
        
        # Test results
        test_results_endpoint()
        
        # Test WebSocket
        test_websocket()
        
        print("\n=== Test Summary ===")
        print("All tests completed. Check output above for any errors.")
        
    except requests.ConnectionError:
        print("ERROR: Could not connect to backend server.")
        print("Make sure the backend is running on localhost:8000")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()
