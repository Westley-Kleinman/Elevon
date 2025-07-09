#!/usr/bin/env python3

import requests

def test_empty_upload():
    """Test uploading an empty GPX file to the backend"""
    
    url = "http://127.0.0.1:5000/api/upload-gpx"
    gpx_file = r"c:\Elevon\empty_trail.gpx"
    
    print(f"🔍 Testing upload of empty trail: {gpx_file}")
    
    try:
        with open(gpx_file, 'rb') as f:
            files = {'gpx': f}
            response = requests.post(url, files=files, timeout=30)
        
        print(f"📡 Response status: {response.status_code}")
        print(f"📄 Response text: {response.text}")
        
        if response.status_code == 200:
            print("✅ Upload successful!")
        else:
            print("❌ Upload failed!")
            
    except Exception as e:
        print(f"❌ Upload error: {e}")

if __name__ == "__main__":
    test_empty_upload()
