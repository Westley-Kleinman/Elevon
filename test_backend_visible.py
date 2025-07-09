import requests
import json
import os

def test_visible_trail():
    print("🧪 Testing visible trail upload through backend")
    print("=" * 50)
    
    # Test with the visible trail file
    gpx_file = "Website/test_visible_trail.gpx"
    
    if not os.path.exists(gpx_file):
        print(f"❌ GPX file not found: {gpx_file}")
        return
    
    # Upload the file with settings for maximum visibility
    try:
        print(f"📁 Uploading file: {gpx_file}")
        with open(gpx_file, 'rb') as f:
            files = {'gpx': f}
            
            # Add visibility settings as form data
            data = {
                'trail_thickness': '10.0',
                'elevation_scale': '1.0',
                'trail_color_r': '1.0',
                'trail_color_g': '0.0', 
                'trail_color_b': '0.0',
                'base_color_r': '0.0',
                'base_color_g': '1.0',
                'base_color_b': '0.0',
                'base_size': '20',
                'samples': '16',
                'width': '800',
                'height': '600'
            }
            
            upload_response = requests.post("http://localhost:5000/api/upload-gpx", 
                                          files=files, data=data)
        
        print(f"📊 Upload status: {upload_response.status_code}")
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.text}")
            return
        
        upload_data = upload_response.json()
        print(f"✅ Upload successful!")
        print(f"   🗂️  File ID: {upload_data.get('file_id')}")
        print(f"   🖼️  Preview available: {upload_data.get('preview_available', False)}")
        
        if upload_data.get('preview_url'):
            preview_url = f"http://localhost:5000{upload_data['preview_url']}"
            print(f"   🖼️  Full preview URL: {preview_url}")
            
            # Try to fetch the preview
            try:
                preview_response = requests.get(preview_url)
                print(f"   📦 Preview response: {preview_response.status_code}")
                print(f"   📦 Preview size: {len(preview_response.content)} bytes")
                
                # Save the preview locally for inspection
                if preview_response.status_code == 200:
                    output_file = "Website/backend_visible_test.png"
                    with open(output_file, 'wb') as f:
                        f.write(preview_response.content)
                    print(f"   💾 Saved preview to: {output_file}")
                    print(f"   🌐 View at: http://localhost:8000/backend_visible_test.png")
                    
                    # Return the file ID for frontend testing
                    return upload_data.get('file_id')
                
            except Exception as e:
                print(f"   ❌ Failed to fetch preview: {e}")
        else:
            print("   ❌ No preview URL in response")
            
    except Exception as e:
        print(f"❌ Upload error: {e}")

if __name__ == "__main__":
    file_id = test_visible_trail()
    if file_id:
        print(f"\n✅ Success! Test with file ID: {file_id}")
        print(f"🌐 Direct backend preview: http://localhost:5000/api/preview/{file_id}")
        print(f"🌐 Debug upload page: http://localhost:8000/debug_upload.html")
