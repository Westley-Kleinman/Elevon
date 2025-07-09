#!/usr/bin/env python3
"""
Test the backend Blender generation directly
"""

import os
from blender_gpx_preview import BlenderGPXPreview

def test_backend_generation():
    """Test backend-style generation"""
    try:
        preview_gen = BlenderGPXPreview()
        
        # Use same paths as backend
        upload_folder = "uploads"
        preview_folder = "previews"
        
        # Create folders if they don't exist
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(preview_folder, exist_ok=True)
        
        # Use actual uploaded file
        gpx_file = "uploads/1e0d3152-4979-4e40-a35c-04ce3868b562.gpx"
        output_image = os.path.abspath(os.path.join(preview_folder, "test_preview.png"))
        
        print(f"GPX file: {gpx_file}")
        print(f"Output image: {output_image}")
        print(f"GPX exists: {os.path.exists(gpx_file)}")
        print(f"Preview folder exists: {os.path.exists(preview_folder)}")
        
        # Generate preview
        success = preview_gen.generate_preview(gpx_file, output_image)
        
        print(f"Generation success: {success}")
        print(f"Output file exists: {os.path.exists(output_image)}")
        
        if os.path.exists(output_image):
            print(f"Output file size: {os.path.getsize(output_image)} bytes")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backend_generation()
