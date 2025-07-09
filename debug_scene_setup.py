#!/usr/bin/env python3

import bpy
import bmesh
import mathutils
import sys
import os

def clear_scene():
    """Clear all mesh objects from the scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)

def create_test_trail():
    """Create a simple visible test trail"""
    # Create a simple line of points
    points = [
        (0, 0, 0),
        (10, 0, 1),
        (20, 5, 2),
        (30, 10, 1),
        (40, 5, 0)
    ]
    
    # Create mesh
    mesh = bpy.data.meshes.new("TestTrail")
    obj = bpy.data.objects.new("TestTrail", mesh)
    bpy.context.collection.objects.link(obj)
    
    # Create vertices and edges
    bm = bmesh.new()
    
    # Add vertices
    for point in points:
        bm.verts.new(point)
    
    # Ensure face indices are valid
    bm.verts.ensure_lookup_table()
    
    # Create edges between consecutive vertices
    for i in range(len(points) - 1):
        bm.edges.new([bm.verts[i], bm.verts[i + 1]])
    
    # Convert to mesh and set thickness
    bm.to_mesh(mesh)
    bm.free()
    
    # Add solidify modifier for thickness
    solidify = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    solidify.thickness = 2.0
    solidify.offset = 0.0
    
    return obj

def setup_bright_material():
    """Create a very bright, visible material"""
    # Create material
    mat = bpy.data.materials.new(name="BrightTrail")
    mat.use_nodes = True
    
    # Clear existing nodes
    mat.node_tree.nodes.clear()
    
    # Add emission shader for maximum brightness
    emission = mat.node_tree.nodes.new(type='ShaderNodeEmission')
    emission.inputs['Color'].default_value = (1.0, 0.0, 0.0, 1.0)  # Bright red
    emission.inputs['Strength'].default_value = 10.0  # Very bright
    
    # Add output
    output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    
    # Connect emission to output
    mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    return mat

def setup_lighting():
    """Set up bright lighting"""
    # Add sun light
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 50))
    sun = bpy.context.object
    sun.data.energy = 10.0
    
    # Add area light from above
    bpy.ops.object.light_add(type='AREA', location=(20, 20, 30))
    area = bpy.context.object
    area.data.energy = 50.0
    area.data.size = 20.0

def setup_camera():
    """Set up camera to look at the trail"""
    # Add camera
    bpy.ops.object.camera_add(location=(50, -50, 30))
    camera = bpy.context.object
    
    # Point camera at origin
    direction = mathutils.Vector((0, 0, 0)) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    return camera

def setup_render_settings():
    """Configure render settings"""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    scene.render.film_transparent = False
    
    # Set background to contrasting color (blue instead of purple)
    world = bpy.context.scene.world
    if world.use_nodes:
        bg_node = world.node_tree.nodes.get('Background')
        if bg_node:
            bg_node.inputs['Color'].default_value = (0.0, 0.0, 1.0, 1.0)  # Blue background

def main():
    output_path = sys.argv[-1] if len(sys.argv) > 1 else "c:\\Elevon\\debug_scene_test.png"
    
    print("=== DEBUGGING BLENDER SCENE SETUP ===")
    
    # Clear scene
    clear_scene()
    print("Scene cleared")
    
    # Create test trail
    trail_obj = create_test_trail()
    print(f"Created trail object: {trail_obj.name}")
    
    # Create and assign bright material
    material = setup_bright_material()
    trail_obj.data.materials.append(material)
    print("Assigned bright red emission material")
    
    # Setup lighting
    setup_lighting()
    print("Added bright lighting")
    
    # Setup camera
    camera = setup_camera()
    print(f"Camera positioned at: {camera.location}")
    
    # Setup render settings
    setup_render_settings()
    print("Configured render settings")
    
    # Print scene info
    print("\n=== SCENE INFO ===")
    print(f"Objects in scene: {[obj.name for obj in bpy.context.scene.objects]}")
    print(f"Active camera: {bpy.context.scene.camera.name if bpy.context.scene.camera else 'None'}")
    print(f"Trail vertices: {len(trail_obj.data.vertices)}")
    print(f"Trail edges: {len(trail_obj.data.edges)}")
    print(f"Trail materials: {[mat.name for mat in trail_obj.data.materials]}")
    
    # Render
    print(f"\nRendering to: {output_path}")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render()
    print("Render complete!")
    
    return output_path

if __name__ == "__main__":
    output = main()
    print(f"Output saved to: {output}")
