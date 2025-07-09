#!/usr/bin/env python3
"""
Direct Blender test for large GPX files to debug rendering issues
"""

import os
import tempfile
from blender_gpx_preview import BlenderGPXPreview

def test_blender_direct():
    """Test Blender directly with large GPX file"""
    
    gpx_file = "test_stage1.gpx"
    output_image = os.path.abspath("test_direct_render.png")
    
    if not os.path.exists(gpx_file):
        print(f"❌ GPX file not found: {gpx_file}")
        return
    
    print("🧪 Testing Blender direct rendering")
    print(f"📁 GPX file: {gpx_file}")
    print(f"🖼️  Output: {output_image}")
    
    # Create Blender generator
    try:
        blender = BlenderGPXPreview()
        print(f"✅ Blender found: {blender.blender_executable}")
    except Exception as e:
        print(f"❌ Blender not found: {e}")
        return
    
    # Test with very conservative settings for large file
    settings = {
        'width': 800,           # Smaller resolution
        'height': 600,          # Smaller resolution  
        'samples': 16,          # Lower samples
        'trail_thickness': 0.1, # Thinner trail
        'elevation_scale': 0.0005  # Less elevation scaling
    }
    
    print(f"⚙️  Settings: {settings}")
    
    # Generate preview
    try:
        result = blender.generate_preview(gpx_file, output_image, settings)
        
        print(f"🔍 Result: {result}")
        
        if result.get('success'):
            print("✅ Rendering successful!")
            if os.path.exists(output_image):
                size = os.path.getsize(output_image)
                print(f"📦 Output file size: {size} bytes")
            else:
                print("❌ Output file does not exist despite success")
        else:
            print("❌ Rendering failed")
            print(f"Stdout: {result.get('stdout', 'No output')}")
            print(f"Stderr: {result.get('stderr', 'No errors')}")
            
    except Exception as e:
        print(f"❌ Exception during rendering: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_blender_direct()
