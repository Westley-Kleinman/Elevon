#!/usr/bin/env python3
"""
Simple Blender test to debug the integration
"""

import subprocess
import tempfile
import os

def test_simple_blender():
    """Test if Blender can run a simple script"""
    
    blender_path = r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"
    
    # Create a simple test script
    simple_script = '''
import bpy
import os

print("Blender is running successfully!")
print(f"Blender version: {bpy.app.version}")

# Create a simple cube
bpy.ops.mesh.primitive_cube_add()

# Set render settings
scene = bpy.context.scene
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.render.filepath = r"C:\\Elevon\\test_outputs\\simple_test.png"

print(f"Rendering to: {scene.render.filepath}")

# Make sure directory exists
os.makedirs(r"C:\\Elevon\\test_outputs", exist_ok=True)

# Render
bpy.ops.render.render(write_still=True)

print("Simple render complete!")
'''

    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(simple_script)
        script_path = f.name
    
    try:
        print("Running simple Blender test...")
        result = subprocess.run([
            blender_path,
            '--background',
            '--python', script_path
        ], capture_output=True, text=True, timeout=60)
        
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")
        
        # Check if output file was created
        output_file = r"C:\Elevon\test_outputs\simple_test.png"
        if os.path.exists(output_file):
            print(f"✅ Output file created: {output_file}")
            print(f"File size: {os.path.getsize(output_file)} bytes")
        else:
            print("❌ Output file not created")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        os.unlink(script_path)

if __name__ == "__main__":
    test_simple_blender()
