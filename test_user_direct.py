import tempfile
import os
from blender_gpx_preview import BlenderGPXPreview

def test_user_gpx_direct():
    print("🧪 Testing user's GPX file directly with Blender")
    print("=" * 60)
    
    gpx_file = "user_stage1.gpx"
    output_file = "c:/Elevon/user_stage1_direct.png"
    
    if not os.path.exists(gpx_file):
        print(f"❌ GPX file not found: {gpx_file}")
        return
    
    # Test with various settings to maximize visibility
    settings = {
        'width': 1200,
        'height': 800,
        'samples': 16,  # Lower for faster testing
        'trail_thickness': 8.0,  # Very thick
        'elevation_scale': 0.05,  # Small scale for large dataset
        'trail_color': [1.0, 0.0, 0.0, 1.0],  # Bright red
        'base_color': [0.0, 0.8, 0.0, 1.0],   # Bright green
        'base_size': 200  # Large base
    }
    
    print(f"📁 GPX file: {gpx_file}")
    print(f"🖼️  Output: {output_file}")
    print(f"⚙️  Settings: {settings}")
    
    try:
        blender_preview = BlenderGPXPreview()
        result = blender_preview.generate_preview(gpx_file, output_file, settings)
        
        print(f"\n🔍 Blender Result:")
        print(f"   ✅ Success: {result.get('success', False)}")
        
        if result.get('success'):
            file_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
            print(f"   📦 Output file size: {file_size:,} bytes")
            
            # Copy to website for viewing
            import shutil
            web_file = "Website/user_direct_test.png"
            shutil.copy(output_file, web_file)
            print(f"   🌐 View at: http://localhost:8000/user_direct_test.png")
            
            # Show key info from stdout
            stdout = result.get('stdout', '')
            if 'Camera positioned at:' in stdout:
                for line in stdout.split('\n'):
                    if any(keyword in line for keyword in ['Camera positioned', 'Trail center', 'Trail span', 'Found', 'points', 'coordinates']):
                        print(f"   📊 {line.strip()}")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
            if result.get('stderr'):
                print(f"   🔴 Stderr: {result['stderr'][:500]}...")
                
    except Exception as e:
        print(f"❌ Direct test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_gpx_direct()
