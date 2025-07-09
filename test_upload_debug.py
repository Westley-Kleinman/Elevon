#!/usr/bin/env python3
"""
Test file upload with detailed debugging
"""

import requests
import os

def test_upload_with_debug():
    """Test upload with detailed debugging"""
    
    # Test the backend health first
    try:
        health_response = requests.get('http://127.0.0.1:5000/api/health')
        print(f"Health check: {health_response.status_code}")
        print(f"Health response: {health_response.text}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Test file upload
    gpx_file_path = 'sample_trail.gpx'
    
    if not os.path.exists(gpx_file_path):
        print(f"❌ GPX file not found: {gpx_file_path}")
        return
    
    file_size = os.path.getsize(gpx_file_path)
    print(f"📁 GPX file: {gpx_file_path}")
    print(f"📏 File size: {file_size} bytes")
    
    # Read file content to verify it's valid
    with open(gpx_file_path, 'r') as f:
        content = f.read()[:200]  # First 200 chars
        print(f"📄 File content preview: {content}")
    
    # Test upload
    try:
        with open(gpx_file_path, 'rb') as f:
            files = {'gpx': f}
            response = requests.post('http://127.0.0.1:5000/api/upload-gpx', files=files)
            
        print(f"📤 Upload status: {response.status_code}")
        print(f"📤 Upload response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Upload successful!")
        else:
            print("❌ Upload failed!")
            
    except Exception as e:
        print(f"❌ Upload error: {e}")

if __name__ == "__main__":
    test_upload_with_debug()
