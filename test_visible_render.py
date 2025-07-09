#!/usr/bin/env python3
"""
Test Blender rendering with very visible settings to debug purple screen issue
"""

import os
from blender_gpx_preview import BlenderGPXPreview

def test_visible_render():
    """Test with very visible, obvious settings"""
    
    gpx_file = "test_stage1.gpx"
    output_image = os.path.abspath("test_visible_render.png")
    
    if not os.path.exists(gpx_file):
        print(f"❌ GPX file not found: {gpx_file}")
        return
    
    print("🧪 Testing Blender rendering with highly visible settings")
    print(f"📁 GPX file: {gpx_file}")
    print(f"🖼️  Output: {output_image}")
    
    # Create Blender generator
    try:
        blender = BlenderGPXPreview()
        print(f"✅ Blender found: {blender.blender_executable}")
    except Exception as e:
        print(f"❌ Blender not found: {e}")
        return
    
    # Test with very visible settings
    settings = {
        'width': 800,
        'height': 600,
        'samples': 16,                      # Lower samples for speed
        'trail_thickness': 2.0,             # VERY thick trail
        'elevation_scale': 0.01,            # Much more elevation
        'trail_color': [1.0, 0.0, 0.0, 1.0],  # Pure red trail
        'base_color': [0.0, 0.5, 0.0, 1.0]    # Green terrain base
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
                
                # Try to open the image to see what it looks like
                print("🖼️  Opening rendered image...")
                os.system(f'start "{output_image}"')
            else:
                print("❌ Output file does not exist despite success")
        else:
            print("❌ Rendering failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Stdout: {result.get('stdout', 'No output')}")
            print(f"Stderr: {result.get('stderr', 'No errors')}")
            
    except Exception as e:
        print(f"❌ Exception during rendering: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_visible_render()
