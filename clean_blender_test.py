#!/usr/bin/env python3

import bpy
import bmesh
import mathutils
import xml.etree.ElementTree as ET
import math
import sys

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Settings for rendering
settings = {
    'trail_color': [0.9, 0.3, 0.1, 1.0],  # Bright orange-red
    'base_color': [0.4, 0.3, 0.2, 1.0],   # Earth tone
    'trail_thickness': 2.0,                # Make it thicker
    'elevation_scale': 0.001,
    'width': 800,
    'height': 600,
    'samples': 32
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
    
    # Decimate for large datasets
    if len(coordinates) > 500:
        decimation_factor = max(1, len(coordinates) // 500)
        coordinates = coordinates[::decimation_factor]
        print(f"Decimated to {len(coordinates)} points")
    
    return coordinates

def lat_lon_to_meters(lat, lon, center_lat, center_lon):
    """Convert lat/lon to approximate meters from center point"""
    lat_m = (lat - center_lat) * 111320
    lon_m = (lon - center_lon) * 111320 * math.cos(math.radians(center_lat))
    return lat_m, lon_m

def create_trail_mesh(coordinates):
    """Create a thick trail mesh from coordinates"""
    if not coordinates:
        return None
    
    # Calculate center point
    center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
    center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
    min_ele = min(coord[2] for coord in coordinates)
    
    # Convert to 3D points
    trail_points = []
    for lat, lon, ele in coordinates:
        x, y = lat_lon_to_meters(lat, lon, center_lat, center_lon)
        z = (ele - min_ele) * settings['elevation_scale']
        trail_points.append((x, y, z))
    
    # Create mesh
    mesh = bpy.data.meshes.new("GPX_Trail")
    obj = bpy.data.objects.new("GPX_Trail", mesh)
    bpy.context.collection.objects.link(obj)
    
    # Create the mesh using bmesh
    bm = bmesh.new()
    
    # Add vertices
    for point in trail_points:
        bm.verts.new(point)
    
    bm.verts.ensure_lookup_table()
    
    # Create edges between consecutive vertices
    for i in range(len(trail_points) - 1):
        bm.edges.new([bm.verts[i], bm.verts[i + 1]])
    
    # Convert to mesh
    bm.to_mesh(mesh)
    bm.free()
    
    # Add solidify modifier for thickness
    solidify = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    solidify.thickness = settings['trail_thickness']
    solidify.offset = 0.0
    
    return obj, trail_points

def create_base(trail_points):
    """Create a base terrain"""
    if not trail_points:
        return None
    
    # Calculate bounds
    min_x = min(p[0] for p in trail_points) 
    max_x = max(p[0] for p in trail_points)
    min_y = min(p[1] for p in trail_points)
    max_y = max(p[1] for p in trail_points)
    min_z = min(p[2] for p in trail_points)
    
    # Create base plane
    size = max(max_x - min_x, max_y - min_y) * 1.5
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    bpy.ops.mesh.primitive_plane_add(
        size=size,
        location=(center_x, center_y, min_z - 1)
    )
    
    base_obj = bpy.context.active_object
    base_obj.name = "Base"
    
    return base_obj

def setup_materials():
    """Create bright, visible materials"""
    # Trail material with emission for maximum visibility
    trail_mat = bpy.data.materials.new("Trail_Material")
    trail_mat.use_nodes = True
    trail_mat.node_tree.nodes.clear()
    
    # Use emission shader for bright visibility
    emission = trail_mat.node_tree.nodes.new('ShaderNodeEmission')
    output = trail_mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    trail_mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    # Bright orange-red color
    emission.inputs['Color'].default_value = settings['trail_color']
    emission.inputs['Strength'].default_value = 5.0  # Very bright
    
    # Base material
    base_mat = bpy.data.materials.new("Base_Material")
    base_mat.use_nodes = True
    base_mat.node_tree.nodes.clear()
    
    bsdf = base_mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    output_base = base_mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    base_mat.node_tree.links.new(bsdf.outputs['BSDF'], output_base.inputs['Surface'])
    
    bsdf.inputs['Base Color'].default_value = settings['base_color']
    bsdf.inputs['Roughness'].default_value = 0.8
    
    return trail_mat, base_mat

def setup_lighting():
    """Setup bright lighting"""
    # Sun light
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 50))
    sun = bpy.context.object
    sun.data.energy = 10.0
    
    # Area light
    bpy.ops.object.light_add(type='AREA', location=(20, 20, 30))
    area = bpy.context.object
    area.data.energy = 50.0
    area.data.size = 20.0

def setup_camera(trail_points):
    """Setup camera to view the trail"""
    if not trail_points:
        return
    
    # Calculate bounds
    min_x = min(p[0] for p in trail_points)
    max_x = max(p[0] for p in trail_points)
    min_y = min(p[1] for p in trail_points)
    max_y = max(p[1] for p in trail_points)
    min_z = min(p[2] for p in trail_points)
    max_z = max(p[2] for p in trail_points)
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2
    
    # Calculate appropriate camera distance
    span = max(max_x - min_x, max_y - min_y)
    distance = max(span * 1.5, 100)  # Minimum distance
    
    # Position camera
    camera_x = center_x + distance * 0.7
    camera_y = center_y - distance * 0.7
    camera_z = center_z + distance * 0.5
    
    # Add camera
    bpy.ops.object.camera_add(location=(camera_x, camera_y, camera_z))
    camera = bpy.context.active_object
    
    # Point camera at trail center
    direction = mathutils.Vector((center_x, center_y, center_z)) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    print(f"Camera at: {camera.location}")
    print(f"Looking at: {center_x}, {center_y}, {center_z}")

def main():
    gpx_file = sys.argv[-2] if len(sys.argv) > 2 else "user_stage1.gpx"
    output_file = sys.argv[-1] if len(sys.argv) > 1 else "test_clean_render.png"
    
    print(f"GPX file: {gpx_file}")
    print(f"Output: {output_file}")
    
    # Parse GPX
    coordinates = parse_gpx(gpx_file)
    if not coordinates:
        print("No coordinates found!")
        return
    
    # Create trail mesh
    trail_obj, trail_points = create_trail_mesh(coordinates)
    if not trail_obj:
        print("Failed to create trail!")
        return
    
    # Create base
    base_obj = create_base(trail_points)
    
    # Setup materials
    trail_mat, base_mat = setup_materials()
    
    # Apply materials
    trail_obj.data.materials.append(trail_mat)
    if base_obj:
        base_obj.data.materials.append(base_mat)
    
    # Setup lighting
    setup_lighting()
    
    # Setup camera
    setup_camera(trail_points)
    
    # Render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = settings['width']
    scene.render.resolution_y = settings['height']
    scene.render.filepath = output_file
    scene.render.image_settings.file_format = 'PNG'
    scene.cycles.samples = settings['samples']
    scene.render.film_transparent = False
    
    # Set background to contrasting color
    world = bpy.context.scene.world
    if world.use_nodes:
        bg_node = world.node_tree.nodes.get('Background')
        if bg_node:
            bg_node.inputs['Color'].default_value = (0.1, 0.1, 0.3, 1.0)  # Dark blue
    
    print("Rendering...")
    bpy.ops.render.render()
    print("Render complete!")

if __name__ == "__main__":
    main()
