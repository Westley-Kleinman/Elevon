#!/usr/bin/env python3

import requests

def test_stage1_upload():
    """Test uploading the stage-1-route.gpx file to the backend"""
    
    url = "http://127.0.0.1:5000/api/upload-gpx"
    gpx_file = r"c:\Elevon\test_stage1.gpx"
    
    print(f"🔍 Testing upload of stage-1 route: {gpx_file}")
    
    try:
        with open(gpx_file, 'rb') as f:
            files = {'gpx': f}
            response = requests.post(url, files=files, timeout=300)  # 5 minute timeout
        
        print(f"📡 Response status: {response.status_code}")
        print(f"📄 Response text: {response.text}")
        
        if response.status_code == 200:
            print("✅ Upload successful!")
        else:
            print("❌ Upload failed!")
            
    except Exception as e:
        print(f"❌ Upload error: {e}")

if __name__ == "__main__":
    test_stage1_upload()
