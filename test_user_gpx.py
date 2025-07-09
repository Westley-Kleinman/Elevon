import requests
import json
import os

def test_user_gpx():
    print("🧪 Testing user's actual stage-1-route.gpx file")
    print("=" * 60)
    
    # Test with the user's actual file
    gpx_file = "user_stage1.gpx"
    
    if not os.path.exists(gpx_file):
        print(f"❌ GPX file not found: {gpx_file}")
        return
    
    file_size = os.path.getsize(gpx_file)
    print(f"📁 File: {gpx_file}")
    print(f"📦 File size: {file_size:,} bytes")
    
    # Upload the file with debugging
    try:
        print(f"⏳ Uploading to backend...")
        with open(gpx_file, 'rb') as f:
            files = {'gpx': f}
            
            # Use high visibility settings
            data = {
                'trail_thickness': '5.0',
                'elevation_scale': '0.1',  # Reduced for large dataset
                'trail_color_r': '1.0',
                'trail_color_g': '0.0', 
                'trail_color_b': '0.0',
                'base_color_r': '0.0',
                'base_color_g': '0.8',
                'base_color_b': '0.0',
                'base_size': '100',  # Larger base for big trail
                'samples': '32',     # Higher quality
                'width': '1200',
                'height': '800'
            }
            
            upload_response = requests.post("http://localhost:5000/api/upload-gpx", 
                                          files=files, data=data, timeout=300)
        
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
            print(f"   🖼️  Preview URL: {preview_url}")
            
            # Fetch the preview
            try:
                print("   ⏳ Downloading preview...")
                preview_response = requests.get(preview_url, timeout=60)
                print(f"   📦 Preview status: {preview_response.status_code}")
                print(f"   📦 Preview size: {len(preview_response.content):,} bytes")
                print(f"   📦 Content type: {preview_response.headers.get('content-type', 'Unknown')}")
                
                if preview_response.status_code == 200:
                    output_file = "Website/user_stage1_test.png"
                    with open(output_file, 'wb') as f:
                        f.write(preview_response.content)
                    print(f"   💾 Saved to: {output_file}")
                    print(f"   🌐 View at: http://localhost:8000/user_stage1_test.png")
                    
                    return upload_data.get('file_id')
                else:
                    print(f"   ❌ Preview download failed: {preview_response.text}")
                
            except Exception as e:
                print(f"   ❌ Failed to fetch preview: {e}")
        else:
            print("   ❌ No preview URL in response")
            
    except Exception as e:
        print(f"❌ Upload error: {e}")

if __name__ == "__main__":
    file_id = test_user_gpx()
    if file_id:
        print(f"\n🎯 Test completed!")
        print(f"📱 File ID: {file_id}")
        print(f"🔗 Direct preview: http://localhost:5000/api/preview/{file_id}")
    else:
        print("\n❌ Test failed")
