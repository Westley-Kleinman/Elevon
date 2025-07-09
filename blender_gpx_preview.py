#!/usr/bin/env python3
"""
Blender GPX Preview Generator
Generates high-quality 3D preview images from GPX files using B    print(f"Extracted {len(coordinates)} coordinates")
    
    # Aggressive point decimation for large datasets to prevent rendering issues
    if len(coordinates) > 1500:
        # For very large datasets, keep every 6th point
        decimation_factor = 6
        coordinates = coordinates[::decimation_factor]
        print(f"Large dataset detected - aggressively decimated to {len(coordinates)} points (every {decimation_factor}th point)")
    elif len(coordinates) > 800:
        # For medium-large datasets, keep every 3rd point  
        decimation_factor = 3
        coordinates = coordinates[::decimation_factor]
        print(f"Medium-large dataset detected - decimated to {len(coordinates)} points (every {decimation_factor}th point)")
    elif len(coordinates) > 400:
        # For medium datasets, keep every 2nd point  
        decimation_factor = 2
        coordinates = coordinates[::decimation_factor]
        print(f"Medium dataset detected - decimated to {len(coordinates)} points (every {decimation_factor}th point)")
    
    print(f"Final coordinate count: {len(coordinates)}")
    return coordinatesnder
"""

import os
import sys
import subprocess
import json
import tempfile
import shutil
from pathlib import Path

class BlenderGPXPreview:
    def __init__(self, blender_executable=None):
        """Initialize the Blender GPX preview generator"""
        self.blender_executable = blender_executable or self.find_blender()
        
    def find_blender(self):
        """Find Blender executable on the system"""
        possible_paths = [
            r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe", 
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
            # Steam version
            os.path.expanduser(r"~\AppData\Local\Steam\steamapps\common\Blender\blender.exe"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        # Try to find in PATH
        try:
            result = subprocess.run(['where', 'blender'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
            
        raise FileNotFoundError("Blender executable not found. Please install Blender or specify the path.")
    
    def generate_preview_script(self, gpx_file, output_image, settings=None):
        """Generate a Blender Python script for creating GPX previews"""
        settings = settings or {}
        
        script = f'''
import bpy
import bmesh
import xml.etree.ElementTree as ET
import math
import os
from mathutils import Vector

print("Starting GPX processing script...")

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete(use_global=False)

# Clear existing curves
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='CURVE')
bpy.ops.object.delete(use_global=False)

# Clear existing cameras and lights
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='CAMERA')
bpy.ops.object.delete(use_global=False)

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='LIGHT')
bpy.ops.object.delete(use_global=False)

# GPX parsing function
def parse_gpx(filepath):
    """Parse GPX file and extract coordinates"""
    print(f"Parsing GPX file: {{filepath}}")
    
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Handle different GPX namespaces - try both 1.0 and 1.1
    ns_11 = {{'default': 'http://www.topografix.com/GPX/1/1'}}
    ns_10 = {{'default': 'http://www.topografix.com/GPX/1/0'}}
    
    coordinates = []
    points = []
    
    # Try GPX 1.1 track points first
    points = root.findall('.//default:trkpt', ns_11)
    if not points:
        # Try GPX 1.1 route points
        points = root.findall('.//default:rtept', ns_11)
    
    if not points:
        # Try GPX 1.0 track points
        points = root.findall('.//default:trkpt', ns_10)
        if not points:
            # Try GPX 1.0 route points
            points = root.findall('.//default:rtept', ns_10)
    
    if not points:
        # Try without namespace prefix but with full namespace (GPX 1.1)
        points = root.findall('.//{{http://www.topografix.com/GPX/1/1}}trkpt')
        if not points:
            points = root.findall('.//{{http://www.topografix.com/GPX/1/1}}rtept')
    
    if not points:
        # Try without namespace prefix but with full namespace (GPX 1.0)
        points = root.findall('.//{{http://www.topografix.com/GPX/1/0}}trkpt')
        if not points:
            points = root.findall('.//{{http://www.topografix.com/GPX/1/0}}rtept')
    
    if not points:
        # Try completely without namespace (some GPX files don't use it)
        points = root.findall('.//trkpt')
        if not points:
            points = root.findall('.//rtept')
    
    print(f"Found {{len(points)}} points")
    
    for pt in points:
        lat = float(pt.get('lat'))
        lon = float(pt.get('lon'))
        
        # Get elevation if available - try multiple approaches for both GPX 1.0 and 1.1
        ele_elem = pt.find('ele')
        if ele_elem is None:
            # Try with GPX 1.1 namespace
            ele_elem = pt.find('default:ele', ns_11)
        if ele_elem is None:
            # Try with GPX 1.0 namespace  
            ele_elem = pt.find('default:ele', ns_10)
        if ele_elem is None:
            # Try with full GPX 1.1 namespace
            ele_elem = pt.find('{{http://www.topografix.com/GPX/1/1}}ele')
        if ele_elem is None:
            # Try with full GPX 1.0 namespace
            ele_elem = pt.find('{{http://www.topografix.com/GPX/1/0}}ele')
        ele = float(ele_elem.text) if ele_elem is not None else 0
        
        coordinates.append((lat, lon, ele))
    
    print(f"Extracted {{len(coordinates)}} coordinates")
    
    # Aggressive point decimation for large datasets to prevent rendering issues
    if len(coordinates) > 1500:
        # For very large datasets, keep every 8th point for even more aggressive decimation
        decimation_factor = 8
        coordinates = coordinates[::decimation_factor]
        print(f"Large dataset detected - aggressively decimated to {{len(coordinates)}} points (every {{decimation_factor}}th point)")
    elif len(coordinates) > 800:
        # For medium-large datasets, keep every 4th point  
        decimation_factor = 4
        coordinates = coordinates[::decimation_factor]
        print(f"Medium-large dataset detected - decimated to {{len(coordinates)}} points (every {{decimation_factor}}th point)")
    elif len(coordinates) > 400:
        # For medium datasets, keep every 2nd point  
        decimation_factor = 2
        coordinates = coordinates[::decimation_factor]
        print(f"Medium dataset detected - decimated to {{len(coordinates)}} points (every {{decimation_factor}}th point)")
    
    print(f"Final coordinate count: {{len(coordinates)}}")
    return coordinates

def lat_lon_to_meters(lat, lon, center_lat, center_lon):
    """Convert lat/lon to approximate meters from center point"""
    # Approximate conversion (good enough for visualization)
    lat_m = (lat - center_lat) * 111320
    lon_m = (lon - center_lon) * 111320 * math.cos(math.radians(center_lat))
    return lat_m, lon_m

def create_trail_from_gpx(gpx_file, trail_thickness=0.2, elevation_scale=0.001):
    """Create a 3D trail mesh from GPX data"""
    print("Creating trail from GPX data...")
    
    coordinates = parse_gpx(gpx_file)
    
    if not coordinates:
        print("No coordinates found in GPX file")
        return None, []
    
    # Calculate center point
    center_lat = sum(coord[0] for coord in coordinates)  / len(coordinates)
    center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
    min_ele = min(coord[2] for coord in coordinates)
    
    print(f"Center: {{center_lat:.6f}}, {{center_lon:.6f}}")
    print(f"Min elevation: {{min_ele:.1f}}m")
    
    # Convert to 3D points
    trail_points = []
    for lat, lon, ele in coordinates:
        x, y = lat_lon_to_meters(lat, lon, center_lat, center_lon)
        z = (ele - min_ele) * elevation_scale
        trail_points.append((x, y, z))
    
    # Create curve from points
    curve_data = bpy.data.curves.new('GPX_Trail', type='CURVE')
    curve_data.dimensions = '3D'
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(count=len(trail_points) - 1)
    
    for i, point in enumerate(trail_points):
        polyline.points[i].co = (point[0], point[1], point[2], 1)
    
    # Create object
    trail_obj = bpy.data.objects.new('GPX_Trail', curve_data)
    bpy.context.collection.objects.link(trail_obj)
    
    # Set curve properties
    curve_data.bevel_depth = trail_thickness
    curve_data.bevel_resolution = 4
    curve_data.use_fill_caps = True
    
    print("Converting curve to mesh...")
    
    # Convert to mesh
    bpy.context.view_layer.objects.active = trail_obj
    trail_obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    
    print(f"Trail created with {{len(trail_points)}} points")
    return trail_obj, trail_points

def create_base_terrain(trail_points, base_size=50, base_thickness=2):
    """Create a simple base terrain"""
    print("Creating base terrain...")
    
    # Calculate bounds
    min_x = min(p[0] for p in trail_points) - base_size/4
    max_x = max(p[0] for p in trail_points) + base_size/4
    min_y = min(p[1] for p in trail_points) - base_size/4
    max_y = max(p[1] for p in trail_points) + base_size/4
    min_z = min(p[2] for p in trail_points)
    
    # Create base plane
    bpy.ops.mesh.primitive_plane_add(
        size=max(max_x-min_x, max_y-min_y) * 1.2,
        location=((max_x+min_x)/2, (max_y+min_y)/2, min_z - base_thickness/2)
    )
    
    base_obj = bpy.context.active_object
    base_obj.name = "Base_Terrain"
    
    # Add some subdivisions and displacement
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=3)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    print("Base terrain created")
    return base_obj

def setup_materials():
    """Create materials for trail and base"""
    print("Setting up materials...")
    
    # Trail material (bright red/orange)
    trail_mat = bpy.data.materials.new("Trail_Material")
    trail_mat.use_nodes = True
    trail_mat.node_tree.nodes.clear()
    
    # Add principled BSDF
    bsdf = trail_mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    output = trail_mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    trail_mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    # Set trail color (bright orange/red)
    bsdf.inputs['Base Color'].default_value = ({settings.get('trail_color', [0.9, 0.3, 0.1, 1.0])})
    bsdf.inputs['Metallic'].default_value = 0.2
    bsdf.inputs['Roughness'].default_value = 0.3
    
    # Base material (earth tones)
    base_mat = bpy.data.materials.new("Base_Material")
    base_mat.use_nodes = True
    base_mat.node_tree.nodes.clear()
    
    bsdf_base = base_mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    output_base = base_mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    base_mat.node_tree.links.new(bsdf_base.outputs['BSDF'], output_base.inputs['Surface'])
    
    # Set base color (earth tone)
    bsdf_base.inputs['Base Color'].default_value = ({settings.get('base_color', [0.4, 0.3, 0.2, 1.0])})
    bsdf_base.inputs['Roughness'].default_value = 0.8
    
    return trail_mat, base_mat

def setup_lighting():
    """Setup professional lighting"""
    print("Setting up lighting...")
    
    # Add key light
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 20))
    key_light = bpy.context.active_object
    key_light.data.energy = 3
    key_light.rotation_euler = (0.3, 0, 0.8)
    
    # Add fill light
    bpy.ops.object.light_add(type='AREA', location=(-5, 5, 10))
    fill_light = bpy.context.active_object
    fill_light.data.energy = 1
    fill_light.data.size = 10
    
    # Set world background
    world = bpy.context.scene.world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.1, 0.1, 0.15, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.3
    
    print("Lighting setup complete")

def setup_camera(trail_obj, trail_points):
    """Position camera for optimal view"""
    print("Setting up camera...")
    
    # Calculate bounding box
    min_x = min(p[0] for p in trail_points)
    max_x = max(p[0] for p in trail_points)
    min_y = min(p[1] for p in trail_points)
    max_y = max(p[1] for p in trail_points)
    min_z = min(p[2] for p in trail_points)
    max_z = max(p[2] for p in trail_points)
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2
    
    # Calculate camera distance
    span = max(max_x - min_x, max_y - min_y)
    distance = span * 1.5
    
    # Add new camera
    bpy.ops.object.camera_add(
        location=(center_x + distance * 0.7, center_y - distance * 0.7, center_z + distance * 0.5)
    )
    camera = bpy.context.active_object
    
    # Point camera at trail center
    direction = Vector((center_x, center_y, center_z)) - camera.location
    camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    print("Camera setup complete")
    return camera

# Main execution
def main():
    gpx_file = r"{gpx_file}"
    output_file = r"{output_image}"
    
    print(f"Processing GPX file: {{gpx_file}}")
    print(f"Output file: {{output_file}}")
    
    # Make sure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir:  # Only create directory if it's not empty
        os.makedirs(output_dir, exist_ok=True)
    
    # Create trail from GPX
    trail_obj, trail_points = create_trail_from_gpx(
        gpx_file,
        trail_thickness={settings.get('trail_thickness', 0.3)},
        elevation_scale={settings.get('elevation_scale', 0.001)}
    )
    
    if not trail_obj:
        print("Failed to create trail from GPX")
        return
    
    # Create base terrain
    base_obj = create_base_terrain(trail_points, base_size={settings.get('base_size', 50)})
    
    # Setup materials
    trail_mat, base_mat = setup_materials()
    
    # Apply materials
    trail_obj.data.materials.append(trail_mat)
    base_obj.data.materials.append(base_mat)
    
    # Setup lighting
    setup_lighting()
    
    # Setup camera
    camera = setup_camera(trail_obj, trail_points)
    
    # Render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = {settings.get('width', 1920)}
    scene.render.resolution_y = {settings.get('height', 1080)}
    scene.render.filepath = output_file
    scene.render.image_settings.file_format = 'PNG'
    
    # Cycles settings for quality
    scene.cycles.samples = {settings.get('samples', 64)}
    scene.cycles.use_denoising = True
    
    print(f"Rendering to: {{output_file}}")
    print(f"Resolution: {{scene.render.resolution_x}}x{{scene.render.resolution_y}}")
    print(f"Samples: {{scene.cycles.samples}}")
    
    # Render
    bpy.ops.render.render(write_still=True)
    
    print("Render complete!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error in main execution: {{e}}")
        import traceback
        traceback.print_exc()
'''
        return script
    
    def generate_preview(self, gpx_file, output_image, settings=None):
        """Generate a preview image from a GPX file using Blender"""
        if not os.path.exists(gpx_file):
            raise FileNotFoundError(f"GPX file not found: {gpx_file}")
        
        # Create temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
            script_content = self.generate_preview_script(gpx_file, output_image, settings)
            script_file.write(script_content)
            script_path = script_file.name
        
        try:
            # Run Blender in background mode
            cmd = [
                self.blender_executable,
                '--background',
                '--python', script_path
            ]
            
            print(f"Running Blender command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            print(f"Blender exit code: {result.returncode}")
            print(f"Blender stdout: {result.stdout}")
            print(f"Blender stderr: {result.stderr}")
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f"Blender execution failed with code {result.returncode}",
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            
            if not os.path.exists(output_image):
                return {
                    'success': False,
                    'error': "Output image was not created",
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            
            return {
                'success': True,
                'output_file': output_image,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        finally:
            # Clean up temporary script
            try:
                os.unlink(script_path)
            except:
                pass

def main():
    """CLI interface for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate GPX preview using Blender')
    parser.add_argument('gpx_file', help='Path to GPX file')
    parser.add_argument('output_image', help='Output image path')
    parser.add_argument('--width', type=int, default=1920, help='Image width')
    parser.add_argument('--height', type=int, default=1080, help='Image height')
    parser.add_argument('--samples', type=int, default=64, help='Render samples')
    parser.add_argument('--blender', help='Path to Blender executable')
    
    args = parser.parse_args()
    
    settings = {
        'width': args.width,
        'height': args.height,
        'samples': args.samples
    }
    
    generator = BlenderGPXPreview(args.blender)
    result = generator.generate_preview(args.gpx_file, args.output_image, settings)
    
    if result['success']:
        print(f"✅ Preview generated successfully: {result['output_file']}")
    else:
        print(f"❌ Failed to generate preview")

if __name__ == "__main__":
    main()
