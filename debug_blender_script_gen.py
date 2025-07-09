#!/usr/bin/env python3
"""
Debug Blender GPX Preview - Test the generated script
"""

import os
import sys
import tempfile
from blender_gpx_preview import BlenderGPXPreview

def debug_blender_script():
    """Generate and save the Blender script for debugging"""
    try:
        preview_gen = BlenderGPXPreview()
        
        # Use our sample GPX file
        gpx_file = "sample_trail.gpx"
        output_image = os.path.join(os.getcwd(), "debug_preview.png")  # Use full path
        
        # Generate the script
        script_content = preview_gen.generate_preview_script(gpx_file, output_image)
        
        # Save to a debug file
        debug_script_path = "debug_blender_script.py"
        with open(debug_script_path, 'w') as f:
            f.write(script_content)
        
        print(f"✅ Debug script saved to: {debug_script_path}")
        print(f"📄 Script length: {len(script_content)} characters")
        
        # Show the first few lines
        lines = script_content.split('\n')
        print(f"📝 First 10 lines:")
        for i, line in enumerate(lines[:10]):
            print(f"  {i+1:2}: {line}")
        
        return debug_script_path
        
    except Exception as e:
        print(f"❌ Error generating debug script: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_blender_script()
