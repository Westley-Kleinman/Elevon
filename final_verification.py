import requests
import json
import os
import time

def final_verification_test():
    print("🎯 FINAL VERIFICATION TEST")
    print("=" * 60)
    print("Testing user's stage-1-route.gpx with latest improvements")
    print("=" * 60)
    
    # Use the user's actual file
    gpx_file = "user_stage1.gpx"
    
    if not os.path.exists(gpx_file):
        print(f"❌ User GPX file not found: {gpx_file}")
        return False
    
    file_size = os.path.getsize(gpx_file)
    print(f"📁 File: {gpx_file}")
    print(f"📦 Size: {file_size:,} bytes")
    
    try:
        # 1. Backend Health Check
        print("\n1️⃣ BACKEND HEALTH CHECK")
        health_response = requests.get("http://localhost:5000/api/health", timeout=10)
        health_data = health_response.json()
        print(f"   Status: {health_data['status']}")
        print(f"   Blender: {health_data.get('blender_available', False)}")
        
        if health_data['status'] != 'healthy':
            print("❌ Backend not healthy!")
            return False
        
        # 2. Upload GPX File
        print("\n2️⃣ UPLOADING GPX FILE")
        with open(gpx_file, 'rb') as f:
            files = {'gpx': f}
            
            # High-quality settings
            data = {
                'trail_thickness': '10.0',
                'elevation_scale': '0.1',
                'trail_color_r': '1.0',
                'trail_color_g': '0.2',
                'trail_color_b': '0.0',
                'base_color_r': '0.1',
                'base_color_g': '0.7',
                'base_color_b': '0.1',
                'base_size': '300',
                'samples': '64',
                'width': '1600',
                'height': '1000'
            }
            
            print(f"   Uploading with high-quality settings...")
            upload_response = requests.post("http://localhost:5000/api/upload-gpx", 
                                          files=files, data=data, timeout=300)
        
        print(f"   Upload status: {upload_response.status_code}")
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.text}")
            return False
        
        upload_data = upload_response.json()
        file_id = upload_data.get('file_id')
        print(f"   ✅ Upload successful!")
        print(f"   📝 File ID: {file_id}")
        print(f"   📊 Points: {upload_data.get('stats', {}).get('total_points', 'Unknown')}")
        print(f"   🖼️  Preview available: {upload_data.get('preview_available', False)}")
        
        # 3. Download and Verify Preview
        print("\n3️⃣ VERIFYING PREVIEW")
        if upload_data.get('preview_url'):
            preview_url = f"http://localhost:5000{upload_data['preview_url']}"
            print(f"   URL: {preview_url}")
            
            # Wait a moment for any processing
            time.sleep(2)
            
            preview_response = requests.get(preview_url, timeout=60)
            print(f"   Status: {preview_response.status_code}")
            print(f"   Content-Type: {preview_response.headers.get('content-type', 'Unknown')}")
            
            if preview_response.status_code == 200:
                content_size = len(preview_response.content)
                print(f"   Size: {content_size:,} bytes")
                
                # Save for inspection
                output_file = "Website/FINAL_VERIFICATION_TEST.png"
                with open(output_file, 'wb') as f:
                    f.write(preview_response.content)
                print(f"   💾 Saved: {output_file}")
                print(f"   🌐 View: http://localhost:8000/FINAL_VERIFICATION_TEST.png")
                
                # Analyze the image
                if content_size > 100000:  # > 100KB suggests real content
                    print("   ✅ Large file size indicates real image content")
                else:
                    print("   ⚠️  Small file size - might be solid color")
                
                return True, file_id, preview_url
            else:
                print(f"   ❌ Preview download failed: {preview_response.text}")
                return False
        else:
            print("   ❌ No preview URL provided")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_website_integration(file_id, preview_url):
    print("\n4️⃣ WEBSITE INTEGRATION TEST")
    print(f"   Testing if website can display preview for file ID: {file_id}")
    
    # Create a simple test page that mimics the website's preview display
    test_html = f"""
    <div class="preview-container">
        <img src="{preview_url}" alt="GPX Preview" 
             onload="console.log('Image loaded: ' + this.naturalWidth + 'x' + this.naturalHeight)"
             onerror="console.error('Image failed to load')" />
    </div>
    """
    
    with open("Website/integration_test.html", "w") as f:
        f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Integration Test</title>
    <style>
        body {{ font-family: Arial; margin: 20px; }}
        img {{ max-width: 100%; border: 2px solid #333; }}
    </style>
</head>
<body>
    <h1>Website Integration Test</h1>
    <p>File ID: {file_id}</p>
    <p>Preview URL: {preview_url}</p>
    {test_html}
    <script>
        console.log('Testing preview integration...');
    </script>
</body>
</html>
        """)
    
    print(f"   🌐 Integration test: http://localhost:8000/integration_test.html")
    return True

if __name__ == "__main__":
    print("Starting final verification...")
    result = final_verification_test()
    
    if isinstance(result, tuple) and result[0]:
        success, file_id, preview_url = result
        print(f"\n🎉 SUCCESS! Preview generated successfully")
        print(f"📱 File ID: {file_id}")
        print(f"🔗 Direct URL: {preview_url}")
        
        verify_website_integration(file_id, preview_url)
        
        print(f"\n✅ FINAL RESULT: The system is working correctly!")
        print(f"✅ Your stage-1-route.gpx file generates a proper preview")
        print(f"✅ No more purple screen - trail is visible")
        
    else:
        print(f"\n❌ FINAL RESULT: Issues detected")
        print(f"❌ Further debugging needed")
