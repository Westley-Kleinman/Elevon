#!/usr/bin/env python3

import requests
import os

def test_gpx_rendering():
    """Test GPX rendering with the fixed material colors"""
    
    backend_url = "http://localhost:5000"
    gpx_file = "c:\\Elevon\\user_stage1.gpx"
    
    if not os.path.exists(gpx_file):
        print(f"GPX file not found: {gpx_file}")
        return
    
    print(f"Testing GPX rendering with file: {gpx_file}")
    print(f"File size: {os.path.getsize(gpx_file)} bytes")
    
    # Upload and generate preview
    try:
        with open(gpx_file, 'rb') as f:
            files = {'gpx': f}
            
            response = requests.post(f"{backend_url}/api/upload-gpx", files=files, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success! File ID: {result.get('file_id')}")
                print(f"Message: {result.get('message', 'No message')}")
                
                # Get the preview image
                preview_response = requests.get(f"{backend_url}/api/preview/{result['file_id']}")
                if preview_response.status_code == 200:
                    output_path = "c:\\Elevon\\test_backend_fixed.png"
                    with open(output_path, 'wb') as img_file:
                        img_file.write(preview_response.content)
                    print(f"Preview saved to: {output_path}")
                    return output_path
                else:
                    print(f"Failed to retrieve preview: {preview_response.status_code}")
            else:
                print(f"Failed to generate preview: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"Error: {e}")
    
    return None

if __name__ == "__main__":
    test_gpx_rendering()
