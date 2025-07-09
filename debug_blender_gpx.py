#!/usr/bin/env python3
"""
Debug the Blender GPX script to see what's happening
"""

import tempfile
import subprocess
import os

def debug_blender_gpx():
    """Create and run a debug version of the Blender GPX script"""
    
    blender_path = r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"
    gpx_file = r"C:\Elevon\sample_trail.gpx"
    output_file = r"C:\Elevon\test_outputs\debug_preview.png"
    
    # Simple debug script that just tries to parse the GPX
    debug_script = f'''
import bpy
import xml.etree.ElementTree as ET
import os

print("=== BLENDER GPX DEBUG SCRIPT ===")

gpx_file = r"{gpx_file}"
output_file = r"{output_file}"

print(f"GPX file: {{gpx_file}}")
print(f"Output file: {{output_file}}")

# Check if GPX file exists
if not os.path.exists(gpx_file):
    print(f"ERROR: GPX file does not exist: {{gpx_file}}")
    exit(1)

print("GPX file exists, attempting to parse...")

try:
    tree = ET.parse(gpx_file)
    root = tree.getroot()
    print(f"Successfully parsed GPX file")
    print(f"Root tag: {{root.tag}}")
    print(f"Root attributes: {{root.attrib}}")
    
    # Try to find track points
    ns = {{'default': 'http://www.topografix.com/GPX/1/1'}}
    points = root.findall('.//default:trkpt', ns)
    print(f"Found {{len(points)}} track points with namespace")
    
    if not points:
        points = root.findall('.//trkpt')
        print(f"Found {{len(points)}} track points without namespace")
    
    if points:
        first_point = points[0]
        print(f"First point: lat={{first_point.get('lat')}}, lon={{first_point.get('lon')}}")
        
        # Get elevation
        ele_elem = first_point.find('.//ele')
        if ele_elem is not None:
            print(f"First point elevation: {{ele_elem.text}}")
        else:
            print("No elevation data found")
    
except Exception as e:
    print(f"ERROR parsing GPX: {{e}}")
    import traceback
    traceback.print_exc()

# Create a simple scene and render test
print("Creating simple test scene...")

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Add a cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))

# Make sure output directory exists
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Set up render
scene = bpy.context.scene
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.render.filepath = output_file
scene.render.image_settings.file_format = 'PNG'

print(f"Rendering test image to: {{output_file}}")

# Render
bpy.ops.render.render(write_still=True)

print("Debug script complete!")
'''
    
    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(debug_script)
        script_path = f.name
    
    try:
        print("Running Blender debug script...")
        result = subprocess.run([
            blender_path,
            '--background',
            '--python', script_path
        ], capture_output=True, text=True, timeout=120)
        
        print("=== STDOUT ===")
        print(result.stdout)
        print("\n=== STDERR ===")
        print(result.stderr)
        print(f"\n=== Return Code: {result.returncode} ===")
        
        # Check if output file was created
        if os.path.exists(output_file):
            print(f"\n✅ Output file created: {output_file}")
            file_size = os.path.getsize(output_file)
            print(f"File size: {file_size} bytes")
        else:
            print(f"\n❌ Output file not created: {output_file}")
            
    except Exception as e:
        print(f"Error running script: {e}")
    finally:
        os.unlink(script_path)

if __name__ == "__main__":
    debug_blender_gpx()
