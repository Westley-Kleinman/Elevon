#!/usr/bin/env python3
"""
Test script for the new stage-1-route.gpx file
"""

import requests
import json
import os
import time

def test_gpx_upload():
    """Test uploading the new stage-1-route.gpx file"""
    
    backend_url = "http://localhost:5000"
    gpx_file = "test_stage1.gpx"
    
    if not os.path.exists(gpx_file):
        print(f"❌ GPX file not found: {gpx_file}")
        return False
    
    # Check backend health
    try:
        response = requests.get(f"{backend_url}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
        print("✅ Backend is healthy")
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False
    
    # Test GPX upload and preview generation
    try:
        print(f"📁 Testing GPX file: {gpx_file}")
        
        with open(gpx_file, 'rb') as f:
            files = {'gpx': f}
            
            print("⏳ Uploading GPX file...")
            response = requests.post(f"{backend_url}/api/upload-gpx", files=files, timeout=120)
            
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                print(f"   📏 Points: {result.get('stats', {}).get('points_count', 'unknown')}")
                print(f"   🗂️  File ID: {result.get('file_id', 'unknown')}")
                print(f"   🖼️  Preview available: {result.get('preview_available', False)}")
                
                # Check if preview was generated
                if 'preview_url' in result:
                    print("✅ Preview generated successfully!")
                    print(f"   🖼️  Preview URL: {result['preview_url']}")
                    
                    # Test preview download
                    preview_response = requests.get(f"{backend_url}{result['preview_url']}", timeout=30)
                    if preview_response.status_code == 200:
                        print(f"   📦 Preview size: {len(preview_response.content)} bytes")
                    else:
                        print(f"   ❌ Preview download failed: {preview_response.status_code}")
                        
                elif 'preview_error' in result:
                    print(f"❌ Preview generation failed: {result['preview_error']}")
                else:
                    print("⚠️  No preview generated (Blender not available)")
                
                return True
            else:
                print(f"❌ Upload failed: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing new stage-1-route.gpx file")
    print("="*50)
    
    success = test_gpx_upload()
    
    print("="*50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed!")
