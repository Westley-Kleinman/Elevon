#!/usr/bin/env python3
"""
Blender GPX Preview Generator
Generates high-quality 3D preview images from GPX files using Blender
"""

import bpy
import bmesh
import mathutils
import xml.etree.ElementTree as ET
import math
import sys
import os

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Default settings
DEFAULT_SETTINGS = {
    'trail_color': [0.9, 0.3, 0.1, 1.0],  # Bright orange-red
    'base_color': [0.4, 0.3, 0.2, 1.0],   # Earth tone
    'trail_thickness': 1.5,
    'elevation_scale': 0.001,
    'base_size': 50,
    'width': 1920,
    'height': 1080,
    'samples': 64
}

def parse_gpx(filepath):
    """Parse GPX file and extract coordinates"""
    print(f"Parsing GPX file: {filepath}")
    
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    coordinates = []
    points = []
    
    # Try different ways to find track points
    points = root.findall('.//trkpt')
    if not points:
        points = root.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')
    if not points:
        points = root.findall('.//{http://www.topografix.com/GPX/1/0}trkpt')
    if not points:
        points = root.findall('.//rtept')
    if not points:
        points = root.findall('.//{http://www.topografix.com/GPX/1/1}rtept')
    
    print(f"Found {len(points)} points")
    
    for pt in points:
        lat = float(pt.get('lat'))
        lon = float(pt.get('lon'))
        
        # Get elevation
        ele_elem = pt.find('ele')
        if ele_elem is None:
            ele_elem = pt.find('.//{http://www.topografix.com/GPX/1/1}ele')
        if ele_elem is None:
            ele_elem = pt.find('.//{http://www.topografix.com/GPX/1/0}ele')
        ele = float(ele_elem.text) if ele_elem is not None else 0
        
        coordinates.append((lat, lon, ele))
    
    # Aggressive decimation for large datasets
    if len(coordinates) > 1000:
        decimation_factor = max(1, len(coordinates) // 800)
        coordinates = coordinates[::decimation_factor]
        print(f"Decimated to {len(coordinates)} points (factor: {decimation_factor})")
    
    return coordinates

def lat_lon_to_meters(lat, lon, center_lat, center_lon):
    """Convert lat/lon to approximate meters from center point"""
    lat_m = (lat - center_lat) * 111320
    lon_m = (lon - center_lon) * 111320 * math.cos(math.radians(center_lat))
    return lat_m, lon_m

def create_trail_from_gpx(gpx_file, settings):
    """Create a 3D trail mesh from GPX data"""
    print("Creating trail from GPX data...")
    
    coordinates = parse_gpx(gpx_file)
    if not coordinates:
        print("No coordinates found in GPX file")
        return None, []
    
    # Calculate center point
    center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
    center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
    min_ele = min(coord[2] for coord in coordinates)
    
    print(f"Center: {center_lat:.6f}, {center_lon:.6f}")
    print(f"Min elevation: {min_ele:.1f}m")
    
    # Convert to 3D points
    trail_points = []
    for lat, lon, ele in coordinates:
        x, y = lat_lon_to_meters(lat, lon, center_lat, center_lon)
        z = (ele - min_ele) * settings['elevation_scale']
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
    
    # Set curve properties for thickness
    curve_data.bevel_depth = settings['trail_thickness']
    curve_data.bevel_resolution = 4
    curve_data.use_fill_caps = True
    
    print("Converting curve to mesh...")
    
    # Convert to mesh
    bpy.context.view_layer.objects.active = trail_obj
    trail_obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    
    print(f"Trail created with {len(trail_points)} points")
    return trail_obj, trail_points

def create_base_terrain(trail_points, settings):
    """Create a simple base terrain"""
    print("Creating base terrain...")
    
    if not trail_points:
        return None
    
    # Calculate bounds
    min_x = min(p[0] for p in trail_points) - settings['base_size']/4
    max_x = max(p[0] for p in trail_points) + settings['base_size']/4
    min_y = min(p[1] for p in trail_points) - settings['base_size']/4
    max_y = max(p[1] for p in trail_points) + settings['base_size']/4
    min_z = min(p[2] for p in trail_points)
    
    # Create base plane
    bpy.ops.mesh.primitive_plane_add(
        size=max(max_x-min_x, max_y-min_y) * 1.2,
        location=((max_x+min_x)/2, (max_y+min_y)/2, min_z - 2)
    )
    
    base_obj = bpy.context.active_object
    base_obj.name = "Base_Terrain"
    
    # Add some subdivisions
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=3)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    print("Base terrain created")
    return base_obj

def setup_materials(settings):
    """Create bright, visible materials"""
    print("Setting up materials...")
    
    # Trail material with emission for maximum visibility
    trail_mat = bpy.data.materials.new("Trail_Material")
    trail_mat.use_nodes = True
    trail_mat.node_tree.nodes.clear()
    
    # Use emission shader for bright visibility
    emission = trail_mat.node_tree.nodes.new('ShaderNodeEmission')
    output = trail_mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    trail_mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    # Set trail color - use emission for maximum brightness
    emission.inputs['Color'].default_value = settings['trail_color']
    emission.inputs['Strength'].default_value = 3.0  # Bright but not overwhelming
    
    # Base material
    base_mat = bpy.data.materials.new("Base_Material")
    base_mat.use_nodes = True
    base_mat.node_tree.nodes.clear()
    
    bsdf = base_mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    output_base = base_mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    base_mat.node_tree.links.new(bsdf.outputs['BSDF'], output_base.inputs['Surface'])
    
    bsdf.inputs['Base Color'].default_value = settings['base_color']
    bsdf.inputs['Roughness'].default_value = 0.8
    
    print("Materials created successfully")
    return trail_mat, base_mat

def setup_lighting():
    """Setup professional lighting"""
    print("Setting up lighting...")
    
    # Add key light (sun)
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 20))
    key_light = bpy.context.active_object
    key_light.data.energy = 5.0
    key_light.rotation_euler = (0.3, 0, 0.8)
    
    # Add fill light (area)
    bpy.ops.object.light_add(type='AREA', location=(-5, 5, 10))
    fill_light = bpy.context.active_object
    fill_light.data.energy = 2.0
    fill_light.data.size = 10
    
    # Set world background to dark blue for contrast
    world = bpy.context.scene.world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get('Background')
    if bg_node:
        bg_node.inputs['Color'].default_value = (0.1, 0.1, 0.3, 1.0)  # Dark blue
        bg_node.inputs['Strength'].default_value = 0.3
    
    print("Lighting setup complete")

def setup_camera(trail_obj, trail_points):
    """Position camera for optimal view"""
    print("Setting up camera...")
    
    if not trail_points:
        return None
    
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
    
    # Calculate camera distance - ensure we can see the entire trail
    span_x = max_x - min_x
    span_y = max_y - min_y
    span = max(span_x, span_y)
    
    # Scale camera distance intelligently for different trail sizes
    if span > 10000:  # Very large trails (>10km)
        distance = min(span * 0.8, 15000)  # Cap at 15km distance
        height = distance * 0.6
    elif span > 1000:  # Large trails (1-10km)
        distance = span * 1.2
        height = distance * 0.7
    else:  # Small trails (<1km)
        distance = max(span * 1.5, 100)  # Minimum distance of 100 units
        height = max(distance * 0.8, 80)  # Minimum height of 80 units
    
    # Position camera diagonally above the trail center
    camera_x = center_x + distance * 0.6
    camera_y = center_y - distance * 0.6
    camera_z = center_z + height
    
    # Delete default camera if it exists
    default_camera = bpy.data.objects.get("Camera")
    if default_camera:
        bpy.data.objects.remove(default_camera, do_unlink=True)
    
    # Add new camera
    bpy.ops.object.camera_add(location=(camera_x, camera_y, camera_z))
    camera = bpy.context.active_object
    camera.name = "TrailCamera"
    
    # Point camera at trail center
    direction = mathutils.Vector((center_x, center_y, center_z)) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    print(f"Camera positioned at: ({camera_x:.1f}, {camera_y:.1f}, {camera_z:.1f})")
    print(f"Trail center: ({center_x:.1f}, {center_y:.1f}, {center_z:.1f})")
    print(f"Trail span: {span:.1f} units ({span/1000:.1f}km)")
    print("Camera setup complete")
    return camera

def main():
    # Get arguments
    if len(sys.argv) < 3:
        print("Usage: blender --background --python script.py -- <gpx_file> <output_image>")
        return
    
    gpx_file = sys.argv[-2]
    output_file = sys.argv[-1]
    
    print(f"Processing GPX file: {gpx_file}")
    print(f"Output file: {output_file}")
    
    # Use default settings
    settings = DEFAULT_SETTINGS.copy()
    
    # Make sure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Create trail from GPX
    trail_obj, trail_points = create_trail_from_gpx(gpx_file, settings)
    if not trail_obj:
        print("Failed to create trail from GPX")
        return
    
    # Create base terrain
    base_obj = create_base_terrain(trail_points, settings)
    
    # Setup materials
    trail_mat, base_mat = setup_materials(settings)
    
    # Apply materials
    trail_obj.data.materials.append(trail_mat)
    if base_obj:
        base_obj.data.materials.append(base_mat)
    
    # Setup lighting
    setup_lighting()
    
    # Setup camera
    camera = setup_camera(trail_obj, trail_points)
    
    # Render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = settings['width']
    scene.render.resolution_y = settings['height']
    scene.render.filepath = output_file
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    
    # Cycles settings for quality
    scene.cycles.samples = settings['samples']
    scene.cycles.use_denoising = True
    
    print(f"Rendering to: {output_file}")
    print(f"Resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
    print(f"Samples: {scene.cycles.samples}")
    
    # Render
    bpy.ops.render.render()
    
    print("Render complete!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
