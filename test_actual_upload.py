import requests
import json
import os

def test_actual_upload():
    print("🧪 Testing actual GPX upload and preview display")
    print("=" * 50)
    
    # Test with the sample trail file
    gpx_file = "Website/sample_trail.gpx"
    
    if not os.path.exists(gpx_file):
        print(f"❌ GPX file not found: {gpx_file}")
        return
    
    # Check backend health first
    try:
        health_response = requests.get("http://localhost:5000/api/health")
        health_data = health_response.json()
        print(f"✅ Backend health: {health_data['status']}")
        print(f"🎨 Blender available: {health_data.get('blender_available', False)}")
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    # Upload the file
    try:
        print(f"📁 Uploading file: {gpx_file}")
        with open(gpx_file, 'rb') as f:
            files = {'gpx': f}
            upload_response = requests.post("http://localhost:5000/api/upload-gpx", files=files)
        
        print(f"📊 Upload status: {upload_response.status_code}")
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.text}")
            return
        
        upload_data = upload_response.json()
        print(f"✅ Upload successful!")
        print(f"   📏 Points: {upload_data.get('stats', {}).get('total_points', 'Unknown')}")
        print(f"   🗂️  File ID: {upload_data.get('file_id')}")
        print(f"   🖼️  Preview available: {upload_data.get('preview_available', False)}")
        
        if upload_data.get('preview_url'):
            preview_url = f"http://localhost:5000{upload_data['preview_url']}"
            print(f"   🖼️  Full preview URL: {preview_url}")
            
            # Try to fetch the preview to check if it's actually an image
            try:
                preview_response = requests.get(preview_url)
                print(f"   📦 Preview response: {preview_response.status_code}")
                print(f"   📦 Preview size: {len(preview_response.content)} bytes")
                print(f"   📦 Content type: {preview_response.headers.get('content-type', 'Unknown')}")
                
                # Save the preview locally for inspection
                if preview_response.status_code == 200:
                    output_file = "Website/latest_preview_test.png"
                    with open(output_file, 'wb') as f:
                        f.write(preview_response.content)
                    print(f"   💾 Saved preview to: {output_file}")
                    print(f"   🌐 View at: http://localhost:8000/latest_preview_test.png")
                
            except Exception as e:
                print(f"   ❌ Failed to fetch preview: {e}")
        else:
            print("   ❌ No preview URL in response")
            
    except Exception as e:
        print(f"❌ Upload error: {e}")

if __name__ == "__main__":
    test_actual_upload()
