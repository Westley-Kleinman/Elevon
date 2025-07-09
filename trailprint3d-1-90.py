# Copyright (c) 2025 EmGi
#
# This work is licensed under the Creative Commons Attribution-NonCommercial 4.0 
# International License. To view a copy of this license, visit 
# https://creativecommons.org/licenses/by-nc/4.0/
#
# You may use, modify, and share this script for personal and non-commercial purposes.
# Commercial use is strictly prohibited without prior written permission.

'''
Version 1.9 changes

Reintroduced Caching
Fixed Part Origin
Fixed Rescale Function
Added few Error Messages
Added SingleColor Mode
Added Standard Fonts if no font is selected (thx to @hape)



'''
bl_info = {
    "name": "TrailPrint3D",
    "blender": (4, 4, 0),
    "category": "Object",
    "author": "EmGi",
    "version": (1, 91),
    "description": "Simple Addon to create 3D Printable Displays from .gpx Files (Press N to show sidebar)",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY"
}


import bpy # type: ignore
import webbrowser
import xml.etree.ElementTree as ET
import math
import requests # type: ignore
import time
from datetime import date
from datetime import datetime
import bmesh # type: ignore
from mathutils import Vector # type: ignore
import os
import sys
import json
import platform

category = "TrailPrint3D"

gpx_file_path = ""
exportPath = ""
shape = ""
name = ""
size =  48
num_subdivisions = 4
scaleElevation = 5
pathThickness = 0.4
pathScale = 0.6
shapeRotation = 0
overwritePathElevation = False
autoScale = 1
dataset = "srtm30m"  # OpenTopoData dataset

textFont = ""
textSize = 0
overwriteLength = ""
overwriteHeight = ""
overwriteTime = ""
outerBorderSize = 0



overwritePathElevation = False
centerx = 0
centery = 0
total_length = 0
total_elevation = 0
total_time = 0
time_str = ""
elevationOffset = 0
# Conversion factor: 1 degree latitude/longitude ≈ 111320 meters
LAT_LON_TO_METERS = 111.32
additionalExtrusion = 0

scaleHor = 1

# Define a path to store the counter data
counter_file = os.path.join(bpy.utils.user_resource('CONFIG'), "api_request_counter.json")
elevation_cache_file = os.path.join(bpy.utils.user_resource('CONFIG'), "elevation_cache.json")

# In-memory elevation cache
_elevation_cache = {}
cacheSize = 10000

#PANEL----------------------------------------------------------------------------------------------------------



def shape_callback(self,context):
    #print(f"Shape: {self.shape}")
    if self.shape == "HEXAGON INNER TEXT" or self.shape == "HEXAGON OUTER TEXT":
        bpy.utils.register_class(MY_PT_Shapes)
    else:
        #pass
        bpy.utils.unregister_class(MY_PT_Shapes)
        
    
# Define a Property Group to store variables
class MyProperties(bpy.types.PropertyGroup):
    file_path: bpy.props.StringProperty(
        name="File Path",
        description="Select a file",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'  # Enables file selection
    )# type: ignore
    export_path: bpy.props.StringProperty(
        name="Export Path",
        description="Where to save the STL file",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'  # Enables file selection
    )# type: ignore
    chain_path: bpy.props.StringProperty(
        name="Chain Path",
        description="Select a folder that contains multiple GPX files",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'  # Enables file selection
    )# type: ignore
    trailName: bpy.props.StringProperty(name="Trail Name", default="")
    
    shape: bpy.props.EnumProperty(
        name = "Shape",
        items=[
            ("HEXAGON", "Hexagon", "Hexagonal map"),
            ("SQUARE", "Square", "Square map"),
            ("HEART", "Heart", "Heart Map"),
            ("HEXAGON INNER TEXT", "Hexagon inner text", "Hexagonal map with inserted Text"),
            ("HEXAGON OUTER TEXT", "Hexagon outer text", "Hexagonal map with backplate and text")
        ],
        default = "HEXAGON",
        update = shape_callback #calls shape_callback when user selects diffrent shape
    )# type: ignore
    
    api: bpy.props.EnumProperty(
        name = "Api",
        items=[
            ("OPENTOPODATA", "Opentopodata", "Slower but more accurate elevation"),
            ("OPEN-ELEVATION","Open-Elevation","Faster but some regions are low quali")
        ],
        default = "OPENTOPODATA"
    )# type: ignore

    dataset: bpy.props.EnumProperty(
        name = "Dataset",
        items=[
            ("srtm30m", "srtm30m", "Latitudes -60 to 60"),
            ("aster30m","aster30m","global"),
            ("ned10m","ned10m","Continental USA, Hawaii, parts of Alaska"),
            ("mapzen","mapzen","global")
        ],
        default = "aster30m"
    )# type: ignore

    objSize: bpy.props.IntProperty(name="Object Size in mm", default = 100, min = 5, max = 1000,description = "Size of the map in mm")
    num_subdivisions: bpy.props.IntProperty(name = "Resolution (max reccomended 6)", default = 4, min = 1, max = 8, description = "Higher Number = more detailed terrain but slower generation")
    scaleElevation: bpy.props.FloatProperty(name = "Elevation Scale", default = 10, min = 0, max = 10000, description = "Multiplier to the Elevation")
    pathThickness: bpy.props.FloatProperty(name = "Path Thickness", default = 0.6, min = 0.1, max = 5, description = "Thickness of the path")
    pathScale: bpy.props.FloatProperty(name = "Path Scale", default = 0.8, min = 0.01, max = 2, description = "0.6 means path is 60% of the Map size")
    shapeRotation: bpy.props.IntProperty(name = "ShapeRotation", default = 0, min = -360, max = 360, description = "Rotation of the shape") 
    overwritePathElevation: bpy.props.BoolProperty(name="Overwrite Path Elevation (Slower)", default=False, description = "recalculate the elevation of the trail incase it differs too much from actual elevation")
    o_verticesPath: bpy.props.StringProperty(name="Path vertices ", default="")
    o_verticesMap: bpy.props.StringProperty(name="Path Map ", default="")
    o_mapScale: bpy.props.StringProperty(name="Map Scale", default = "")
    o_time: bpy.props.StringProperty(name="TimeTook",default="")
    o_apiCounter_OpenTopoData: bpy.props.StringProperty(name="apiCounter_OpenTopodata", default = "API Limit: ---/1000 daily")
    o_apiCounter_OpenElevation: bpy.props.StringProperty(name="apiCounter_OpenElevation", default = "API Limit: ---/1000 monthly")

    #other shapes
    textFont: bpy.props.StringProperty(
        name="Font",
        description="Select a file",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'  # Enables file selection
    )# type: ignore
    textSize: bpy.props.IntProperty(name="Text Size", default = 5, min = 0, max = 1000)
    overwriteLength: bpy.props.StringProperty(name="text1", default = "")
    overwriteHeight: bpy.props.StringProperty(name="text2", default = "")
    overwriteTime: bpy.props.StringProperty(name="text3", default = "")
    outerBorderSize: bpy.props.IntProperty(name="BorderSize in %", default = 20, min = 1, max = 1000, description="Only for Hexagon outer Text")
    text_angle_preset: bpy.props.IntProperty(name="Text Angle", description="Rotate Text on Shape", default=0, min = 0, max = 260)



    baseThickness: bpy.props.IntProperty(name="BaseThickness", default = 2, min = 0, max = 1000, description="Additional Thickness on lowest point")
    xTerrainOffset: bpy.props.FloatProperty(name="xTerrainOffset", default = 0, description="Gives the map an Offset in X-Direction from the path")
    yTerrainOffset: bpy.props.FloatProperty(name="yTerrainOffset", default = 0, description="Gives the map an Offset in Y-Direction from the path")

    show_stats: bpy.props.BoolProperty(name="Show Additional Info", default=False)
    rescaleMultiplier: bpy.props.FloatProperty(name = "scale", default = 1, min = 0, max = 10000)
    fixedElevationScale: bpy.props.BoolProperty(name="FixedElevationScale(10mm)", default=False, description = "Force the elevation to be 10mm High from highest to lowest point (ElevationScale still applies after that)")
    singleColorMode: bpy.props.BoolProperty(name="SingleColorMode", default = False, description = "Enable this if you dont have a Multicolor printer")
    scmTolerance: bpy.props.FloatProperty(name = "Single-ColorTolerance", default = 0.1, min = 0, max = 2, description = "The Single-Color Tolerance of the Path (default = 0.1)")
    disableCache: bpy.props.BoolProperty(name="disableCache", default = False, description = "disabling cache if you encounter random holes in your mesh")

    sAdditionalExtrusion: bpy.props.FloatProperty(name="sAdditionalExtrusion",default = 0)
    sAutoScale: bpy.props.FloatProperty(name="sAutoScale",default = 1)
    sScaleHor: bpy.props.FloatProperty(name="sScaleHor",default = 1)
    sElevationOffset: bpy.props.FloatProperty(name="sElevationOffset", default = 0)

    

# Define the operator (script execution)
class MY_OT_runGeneration(bpy.types.Operator):
    bl_idname = "wm.run_my_script"
    bl_label = "Generate"
    bl_description = "Generate the Path and the Map with current Settings"

    def execute(self, context):
        props = context.scene.my_tool  # Access stored variables
        
        runGeneration(0)
        
        return {'FINISHED'}


class MY_OT_ExportSTL(bpy.types.Operator):
    bl_idname = "wm.run_my_script5"
    bl_label = "Export STL"
    bl_description = "Export the currently selected Objects as Separate STLs by their name"

    def execute(self, context):
        props = context.scene.my_tool  # Access stored variables
        
        global exportPath
        exportPath = bpy.context.scene.my_tool.get('export_path', None)

        if exportPath == None:
            show_message_box("Export path cant be empty")
            return {'FINISHED'}
    
        exportPath = bpy.path.abspath(exportPath)

        if not exportPath or exportPath == "":
            show_message_box("Export path is empty! Please select a valid folder.")
            return {'FINISHED'}
        if not os.path.isdir(exportPath):
            show_message_box(f"Invalid export Directory: {exportPath}. Please select a valid Directory.")
            return {'FINISHED'}
        
        if not bpy.context.selected_objects:
            show_message_box("Please select the Object you want to Export")
            return{'FINISHED'}
        
        export_selected_to_STL()

        show_message_box("File Exported to your selected directory","INFO","File Exported")
        
        return {'FINISHED'}


def open_website(self, context):
    webbrowser.open("https://patreon.com/EmGi3D?utm_source=Blender")  # Change this to your URL

# Operator to open a website
class MY_OT_OpenWebsite(bpy.types.Operator):
    bl_idname = "wm.open_website"
    bl_label = "Visit My Website"
    bl_description = "The Patreon Version as Additional Features!"

    def execute(self, context):
        open_website(self, context)
        #self.report({'INFO'}, "Opening website...")
        return {'FINISHED'}
    
class MY_OT_Rescale(bpy.types.Operator):
    bl_idname = "wm.rescale"
    bl_label = "Rescale the z value"
    bl_description = "Rescales the Elevation the Currently selected objects"

    def execute(self, context):
        multiZ = bpy.context.scene.my_tool.get('rescaleMultiplier', 1)

        selected_objects = [obj for obj in bpy.context.selected_objects if obj.type in {'MESH', 'CURVE'}]
        lowestZ = 1000

        for obj in selected_objects:
            bpy.context.view_layer.objects.active = obj  # Make it active
            bpy.ops.object.mode_set(mode='EDIT')
            print("1")
            if obj.type == 'MESH':
                mesh = obj.data
                for i, vert in enumerate(mesh.vertices):
                    if vert.co.z < lowestZ and vert.co.z > 0.1:
                        lowestZ = vert.co.z
                if  lowestZ != 1000:
                    print(f"lowestZ: {lowestZ}")
                    # Access mesh data
                    mesh = bmesh.from_edit_mesh(obj.data)
                    for v in mesh.verts:
                        if v.co.z > 0.1:
                            v.co.z = (v.co.z - lowestZ) * (multiZ) + lowestZ
                    bmesh.update_edit_mesh(obj.data)
            if obj.type == "CURVE":
                print("3")
                if lowestZ == 1000:
                    for spline in obj.data.splines:
                        for point in spline.bezier_points:
                            if point.co.z > 0.1 and point.co.z < lowestZ:
                                lowestZ = point.co.z
                                print("4")
            
                if lowestZ != 1000:
                    print("5")
                    # Access curve splines
                    for spline in obj.data.splines:
                        for point in spline.bezier_points:
                            if point.co.z > -0.5:
                                point.co.z *= multiZ
                                print("6")
                        for point in spline.points:  # For NURBS
                            if point.co.z > -0.5:
                                point.co.z *= multiZ

            bpy.ops.object.mode_set(mode='OBJECT')  # Exit Edit Mode

        print(f"Scaled all elevation points by {multiZ}mm on {len(selected_objects)} object(s).")

        return {'FINISHED'}
    
    
# Create the UI Panel
class MY_PT_Generate(bpy.types.Panel):
    bl_label = "Create"
    bl_idname = "PT_EmGi_3DPath+"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = category

    def draw(self, context):
        layout = self.layout
        props = context.scene.my_tool  # Get properties

        # Add input fields
        layout.label(text = "Created by: EmGi")
        layout.label(text = "Premium Version: 1.9")
        #layout.separator()  # Adds a horizontal line
        box = layout.box()
        box.prop(props, "file_path")
        box.prop(props, "export_path")
        box.prop(props, "trailName")
        box.prop(props, "shape")
        box.separator()  # Adds a horizontal line
        box.prop(props, "objSize")
        box.prop(props, "num_subdivisions")
        box.prop(props, "scaleElevation")
        box.prop(props, "pathThickness")
        box.prop(props, "pathScale")
        box.prop(props, "shapeRotation")
        box.prop(props, "overwritePathElevation")
        #layout.separator()  # Adds a horizontal line
        # Add the script execution button
        layout.label(text = "Create the File")
        layout.operator("wm.run_my_script")
        
        #layout.label(text = props.o_verticesPath)
        #layout.label(text = props.o_verticesMap)
        #layout.label(text = props.o_mapScale)
        layout.label(text = props.o_time)
        #layout.label(text = props.o_apiCounter_OpenTopoData)
        
        layout.separator()  # Adds a horizontal line
        layout.prop(props,"api")
        layout.separator()  # Adds a horizontal line
        
        layout.label(text = "Support me on Patreon")
        layout.operator("wm.open_website",text = "Open Patreon", icon='URL')  # Open website


class MY_PT_Advanced(bpy.types.Panel):
    bl_label = "Advanced"
    bl_idname = "PT_Advanced"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = category
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.my_tool  # Get properties
        
        #Add input fields
        layout.label(text = "Change Dataset (Only Opentopodata)")
        layout.prop(props, "dataset")
        layout.separator()  # Adds a horizontal line
        layout.label(text = "ONLY USE IF YOU KNOW WHAT YOU ARE DOING")
        box = layout.box()
        row = box.row()
        row.prop(props, "rescaleMultiplier")
        row.operator("wm.rescale",text = "Rescale Z", )
        box.separator()  # Adds a horizontal line
        box.prop(props, "fixedElevationScale")
        box.prop(props, "baseThickness")
        box.prop(props, "xTerrainOffset")
        box.prop(props, "yTerrainOffset")
        box.prop(props, "singleColorMode")
        box.prop(props, "scmTolerance")
        box.separator()  # Adds a horizontal line
        box.label(text = "based on last generated path")
        box.operator("wm.terrain", text = "Create Terrain from selected")
        layout.separator()  # Adds a horizontal line
        box = layout.box()
        box.label(text = "Manually export selected to STL")
        box.operator("wm.run_my_script5")

        layout.separator()  # Adds a horizontal line

        layout.prop(props,"show_stats", icon="TRIA_DOWN" if props.show_stats else "TRIA_RIGHT", emboss=False)
        if props.show_stats:
            box = layout.box()
            box.label(text = props.o_verticesPath)
            box.label(text = props.o_verticesMap)
            box.label(text = props.o_mapScale)
            box.label(text = props.o_time)
            box.separator()  # Adds a horizontal line
            box.label(text = "Opentopodata:")
            box.label(text = props.o_apiCounter_OpenTopoData)
            box.label(text = "OpenElevation:")
            box.label(text = props.o_apiCounter_OpenElevation)


class MY_PT_Shapes(bpy.types.Panel):
    bl_label = "Additional Shape Settings"
    bl_idname = "PT_ShapeSettings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = category
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.my_tool  # Get properties
        
        #print(f"shape: {props.shape}")
        if props.shape == "HEXAGON INNER TEXT" or props.shape == "HEXAGON OUTER TEXT":

            #Add input fields
            layout.prop(props, "textFont")
            layout.prop(props, "textSize")
            layout.separator()  # Adds a horizontal line
            layout.label(text = "Overwrite text:")
            layout.prop(props, "overwriteLength")
            layout.prop(props, "overwriteHeight")
            layout.prop(props, "overwriteTime")
            layout.prop(props, "outerBorderSize")
            layout.prop(props, "text_angle_preset")

# Register the classes and properties
def register():
    bpy.utils.register_class(MyProperties)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyProperties)

    bpy.utils.register_class(MY_OT_runGeneration)
    bpy.utils.register_class(MY_OT_ExportSTL)
    bpy.utils.register_class(MY_PT_Generate)
    bpy.utils.register_class(MY_PT_Advanced)
    bpy.utils.register_class(MY_OT_OpenWebsite)
    bpy.utils.register_class(MY_OT_Rescale)

def unregister():
    del bpy.types.Scene.my_tool
    bpy.utils.unregister_class(MyProperties)

    bpy.utils.unregister_class(MY_OT_runGeneration)
    bpy.utils.unregister_class(MY_OT_ExportSTL)
    bpy.utils.unregister_class(MY_PT_Generate)
    bpy.utils.unregister_class(MY_PT_Advanced)
    bpy.utils.unregister_class(MY_OT_OpenWebsite)
    bpy.utils.unregister_class(MY_OT_Rescale)



#--------------------------------------------------
#Debug
#--------------------------------------------------

def load_counter():
    if os.path.exists(counter_file):
        try:
            with open(counter_file, "r") as f:
                data = json.load(f)
                return data.get("count_openTopodata", 0), data.get("date_openTopoData", ""), data.get("count_openElevation",0), data.get("date_openElevation","")
        except:
            return 0, "", 0, ""
    return 0, "", 0, ""

# Function to save the counter data
def save_counter(count_openTopodata, date_openTopoData, count_openElevation, date_openElevation):
    with open(counter_file, "w") as f:
        json.dump({"count_openTopodata": count_openTopodata, "date_openTopoData": date_openTopoData, "count_openElevation": count_openElevation, "date_openElevation": date_openElevation}, f)

# Function to update the request counter
def update_request_counter():
    today = date.today().isoformat()  # ✅ This correctly gets today's date
    today_date = date.today().isoformat()  # Get today's date in iso format
    today_month = date.today().month  # Get current month as an integer (1-12)
    count_openTopodata, date_openTopoData, count_openElevation, date_openElevation = load_counter()

    # Reset counter if the date has changed
    if date_openTopoData != today_date:
        count_openTopodata = 0
    
    if date_openElevation != today_month:
        count_openElevation = 0

    global api
    if api == 0:
        count_openTopodata += 1
        #print("Count api opentopodata")
    elif api == 1:
        count_openElevation += 1
        #print("Count api openElevation")

    save_counter(count_openTopodata, today_date, count_openElevation,today_month)
    
    return count_openTopodata, count_openElevation  # Return the updated count

def send_api_request(addition = ""):
    
    global dataset
    request_count = update_request_counter()
    now = datetime.now()
    if api == 0:
        print(f"{now.hour:02d}:{now.minute:02d} | Fetching: {addition} | API Usage: {request_count} | {dataset}")
    elif api == 1:
        print(f"{now.hour:02d}:{now.minute:02d} | Fetching: {addition} | API Usage: {request_count}")
    
if __name__ == "__main__":
    
    register()
    #unregister()


#--------------------------------------------------------------------------------------------------------------------
#DISPLAY GENERATION----------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------

import xml.etree.ElementTree as ET
from datetime import datetime
import bpy

def read_gpx_1_1(filepath):
    """Reads a GPX file and extracts the coordinates, elevation, and timestamps
    from either track points (trkpt) or route points (rtept).
    """
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Define namespaces for parsing GPX
    ns = {'default': 'http://www.topografix.com/GPX/1/1'}

    # Try to find track points first
    points = root.findall('.//default:trkpt', ns)
    point_type = 'trkpt'

    # If no track points found, look for route points
    if not points:
        points = root.findall('.//default:rtept', ns)
        point_type = 'rtept'

    coordinates = []
    lowestElevation = 10000

    for pt in points:
        lat = float(pt.get('lat'))
        lon = float(pt.get('lon'))
        ele = pt.find('default:ele', ns)
        elevation = float(ele.text) if ele is not None else 0.0
        time = pt.find('default:time', ns)
        try:
            timestamp = datetime.fromisoformat(time.text.replace("Z", "+00:00")) if time is not None else None
        except Exception:
            timestamp = None
        coordinates.append((lat, lon, elevation, timestamp))
        if elevation < lowestElevation:
            lowestElevation = elevation

    global elevationOffset
    elevationOffset = max(lowestElevation - 50, 0)

    bpy.context.scene.my_tool["sElevationOffset"] = elevationOffset
    bpy.context.scene.my_tool["o_verticesPath"] = f"{point_type.upper()} vertices: {len(coordinates)}"

    return coordinates



def read_gpx_1_0(filepath):
    """Reads a GPX 1.0 file and extracts the coordinates, elevation, and timestamps."""
    tree = ET.parse(filepath)
    root = tree.getroot()
    

    # Define the namespace to handle the GPX 1.0 format correctly
    ns = {'gpx': 'http://www.topografix.com/GPX/1/0'}

    # Extract track points (latitude, longitude, elevation, timestamp)
    coordinates = []
    lowestElevation = 10000
    
    # Extracting track points
    for trkpt in root.findall('.//gpx:trkpt', ns):
        lat = float(trkpt.get('lat'))
        lon = float(trkpt.get('lon'))
        ele = trkpt.find('gpx:ele', ns)
        elevation = float(ele.text) if ele is not None else 0.0
        time = trkpt.find('gpx:time', ns)
        timestamp = datetime.fromisoformat(time.text) if time is not None else None
        #print(f"lat: {lat}, long: {lon}, ele: {elevation}, time: {timestamp}")
        coordinates.append((lat, lon, elevation, timestamp))
        
        if elevation < lowestElevation:
            lowestElevation = elevation
    
    global elevationOffset
    elevationOffset = max(lowestElevation - 50, 0)

    bpy.context.scene.my_tool["sElevationOffset"] = elevationOffset
    
    bpy.context.scene.my_tool["o_verticesPath"] = "Path vertices: " + str(len(coordinates))
    return coordinates

def read_igc(filepath):
    """Reads an IGC file and extracts the coordinates, elevation, and timestamps."""
    coordinates = []
    lowestElevation = 10000
    
    with open(filepath, 'r') as file:
        for line in file:
            # IGC B records contain position data
            if line.startswith('B'):
                try:
                    # Extract time (HHMMSS)
                    time_str = line[1:7]
                    hours = int(time_str[0:2])
                    minutes = int(time_str[2:4])
                    seconds = int(time_str[4:6])
                    
                    # Extract latitude (DDMMmmmN/S)
                    lat_str = line[7:15]
                    lat_deg = int(lat_str[0:2])
                    lat_min = int(lat_str[2:4])
                    lat_min_frac = int(lat_str[4:7]) / 1000.0
                    lat = lat_deg + (lat_min + lat_min_frac) / 60.0
                    if lat_str[7] == 'S':
                        lat = -lat
                    
                    # Extract longitude (DDDMMmmmE/W)
                    lon_str = line[15:24]
                    lon_deg = int(lon_str[0:3])
                    lon_min = int(lon_str[3:5])
                    lon_min_frac = int(lon_str[5:8]) / 1000.0
                    lon = lon_deg + (lon_min + lon_min_frac) / 60.0
                    if lon_str[8] == 'W':
                        lon = -lon
                    
                    # Extract pressure altitude (in meters)
                    pressure_alt = int(line[25:30])
                    
                    # Extract GPS altitude (in meters)
                    gps_alt = int(line[30:35])
                    
                    # Create timestamp (using current date since IGC files don't store date in B records)
                    now = datetime.now()
                    timestamp = datetime(now.year, now.month, now.day, hours, minutes, seconds)
                    
                    # Use GPS altitude for elevation
                    elevation = gps_alt
                    
                    coordinates.append((lat, lon, elevation, timestamp))
                    
                    if elevation < lowestElevation:
                        lowestElevation = elevation
                        
                except (ValueError, IndexError) as e:
                    print(f"Error parsing IGC line: {line.strip()}")
                    continue
    
    global elevationOffset
    elevationOffset = max(lowestElevation - 50, 0)
    
    bpy.context.scene.my_tool["o_verticesPath"] = "Path vertices: " + str(len(coordinates))
    return coordinates


def read_gpx_directory(directory_path):
    """Reads all GPX files in a directory and extracts coordinates, elevation, and timestamps."""
    
    # Define GPX namespace
    ns = {'default': 'http://www.topografix.com/GPX/1/1'}
    
    # List to store all coordinates from all GPX files
    coordinates = []
    coordinatesSeparate = []  # Stores a list of lists for separate files
    lowestElevation = 10000  # High initial value

    # Iterate over all files in the directory
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(".gpx"):  # Only process .gpx files
            filepath = os.path.join(directory_path, filename)

            # Parse the GPX file
            tree = ET.parse(filepath)
            root = tree.getroot()

            # Temporary list for this file's coordinates
            file_coordinates = []

            # Extract track points
            for trkpt in root.findall('.//default:trkpt', ns):
                lat = float(trkpt.get('lat'))
                lon = float(trkpt.get('lon'))
                ele = trkpt.find('default:ele', ns)
                elevation = float(ele.text) if ele is not None else 0.0
                time = trkpt.find('default:time', ns)
                timestamp = datetime.fromisoformat(time.text) if time is not None else None
                
                point = (lat, lon, elevation, timestamp)
                coordinates.append(point)
                file_coordinates.append(point)

                # Track lowest elevation
                if elevation < lowestElevation:
                    lowestElevation = elevation

            # Append the file-specific list to coordinatesSeparate
            if file_coordinates:
                coordinatesSeparate.append(file_coordinates)

    # Calculate elevation offset
    global elevationOffset
    elevationOffset = max(lowestElevation - 50, 0)

    bpy.context.scene.my_tool["sElevationOffset"] = elevationOffset

    # Store the number of points in the Blender scene property
    bpy.context.scene.my_tool["o_verticesPath"] = f"Path vertices: {len(coordinates)}"
    
    print(f"Total GPX files processed: {len(coordinatesSeparate)}")
    print(f"Total points collected: {len(coordinates)}")
    
    return coordinates, coordinatesSeparate

#CACHE

# Load cache from disk
def load_elevation_cache():
    """Load the elevation cache from disk"""

    global _elevation_cache
    if os.path.exists(elevation_cache_file):
        try:
            with open(elevation_cache_file, "r") as f:
                _elevation_cache = json.load(f)
        except Exception as e:
            print(f"Error loading elevation cache: {str(e)}")
            _elevation_cache = {}
    else:
        _elevation_cache = {}

# Save cache to disk
def save_elevation_cache():
    """Save the elevation cache to disk"""
    # Limit cache size to prevent excessive file sizes
    if len(_elevation_cache) > cacheSize:
        # Keep only the most recent entries
        keys = list(_elevation_cache.keys())
        for key in keys[:-cacheSize]:
            del _elevation_cache[key]
            
    try:
        with open(elevation_cache_file, "w") as f:
            json.dump(_elevation_cache, f)
    except Exception as e:
        print(f"Error saving elevation cache: {str(e)}")

def get_cached_elevation(lat, lon, api_type="opentopodata"):
    """Get elevation from cache if available"""
    key = f"{lat:.5f}_{lon:.5f}_{api_type}"
    return _elevation_cache.get(key)

def cache_elevation(lat, lon, elevation, api_type="opentopodata"):
    """Cache elevation data"""
    key = f"{lat:.5f}_{lon:.5f}_{api_type}"
    _elevation_cache[key] = elevation


def calculate_scale(hexSize, coordinates):
    
    
    #for lat, lon, ele in coordinates:
    min_lat = min(point[0] for point in coordinates)
    max_lat = max(point[0] for point in coordinates)
    min_lon = min(point[1] for point in coordinates)
    max_lon = max(point[1] for point in coordinates)
    
    
    R = 6371  # Earth's radius in meters (Web Mercator standard)
    x1 = R * math.radians(min_lon)
    y1 = R * math.log(math.tan(math.pi / 4 + math.radians(min_lat) / 2))
    x2 = R * math.radians(max_lon)
    y2 = R * math.log(math.tan(math.pi / 4 + math.radians(max_lat) / 2))
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    
    
    
    maxer = max(width,height, distance)
    
    scale = (hexSize * pathScale) / maxer
    return scale

def convert_to_blender_coordinates(lat, lon, elevation,timestamp):
    
    R = 6371  # Earth's radius in meters (Web Mercator standard)
    x = R * math.radians(lon) * scaleHor
    y = R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * scaleHor
    z = (elevation - elevationOffset) /1000 * scaleElevation * autoScale
    
    
    
    
    return (x, y, z)

# Convert offsets to latitude/longitude
def convert_to_geo(y, x, x_offset, y_offset):
    """Converts Blender x/y offsets to latitude/longitude."""
    
    R = 6371  # Earth's radius in meters (Web Mercator standard)
    longitude = math.degrees((x + x_offset) / (R * scaleHor) )
    latitude = math.degrees(2 * math.atan(math.exp((y + y_offset) / (R * scaleHor) )) - math.pi / 2)
    return latitude, longitude

def create_curve_from_coordinates(coordinates):
    """
    Create a curve in Blender based on a list of (x, y, z) coordinates.
    """
    # Create a new curve object
    curve_data = bpy.data.curves.new('GPX_Curve', type='CURVE')
    curve_data.dimensions = '3D'
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(count=len(coordinates) - 1)

    # Populate the curve with points
    for i, coord in enumerate(coordinates):
        polyline.points[i].co = (coord[0], coord[1], coord[2], 1)  # (x, y, z, w)

    # Create an object with this curve
    curve_object = bpy.data.objects.new('GPX_Curve_Object', curve_data)
    bpy.context.collection.objects.link(curve_object)
    curve_object.data.bevel_depth = pathThickness  # Set the thickness of the curve
    curve_object.data.bevel_resolution = 4  # Set the resolution for smoothness
    
    mod = curve_object.modifiers.new(name="Remesh",type="REMESH")
    mod.mode = "VOXEL"
    mod.voxel_size = 0.05 * pathThickness * 10
    mod.adaptivity = 0.0
    curve_object.data.use_fill_caps = True
        
    curve_object.data.name = name + "_Trail"
    curve_object.name = name + "_Trail"
    
    
    curve_object.select_set(True)


    bpy.context.view_layer.objects.active = curve_object

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.smooth()
    bpy.ops.object.mode_set(mode='OBJECT')



    # Convert to mesh
    if shape == "HEXAGON INNER TEXT" or shape == "HEXAGON OUTER TEXT":
        #bpy.ops.object.convert(target='MESH')
        pass

def simplify_curve(points_with_extra, min_distance=0.1000):
    """
    Removes points that are too close to any previously accepted point.
    Keeps the full (x, y, z, time) format.
    """

    if not points_with_extra:
        return []

    simplified = [points_with_extra[0]]
    last_xyz = Vector(points_with_extra[0][:3])
    skipped = 0

    for pt in points_with_extra[1:]:
        current_xyz = Vector(pt[:3])
        if (current_xyz - last_xyz).length >= min_distance:
            simplified.append(pt)
            last_xyz = current_xyz
        else:
            skipped += 1
            pass

    print(f"Smooth curve: Removed {skipped} vertices")
    return simplified

def create_hexagon(size):
    """Creates a hexagon at (0,0,0), subdivides it, and rotates it by 90 degrees."""
    verts = []
    faces = []
    for i in range(6):
        angle = math.radians(60 * i)
        x = size * math.cos(angle)
        y = size * math.sin(angle)
        verts.append((x, y, 0))
    verts.append((0, 0, 0))  # Center vertex
    faces = [[i, (i + 1) % 6, 6] for i in range(6)]
    mesh = bpy.data.meshes.new("Hexagon")
    obj = bpy.data.objects.new("Hexagon", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    #bpy.ops.mesh.subdivide(number_cuts=num_subdivisions)
    for _ in range(num_subdivisions):
        bpy.ops.mesh.subdivide(number_cuts=1)  # 1 cut per loop for even refinement
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.name = name
    obj.data.name = name
    return obj

def create_heart(size):
    """Creates a full heart-shaped mesh in Blender and applies a Remesh modifier."""
    verts = []
    faces = []
    
    # Heart parametric equations (full heart)
    steps = 200
    for i in range(steps + 1):
        t = i / steps * (2 * math.pi)
        x = size * (16 * math.sin(t) ** 3) / 16
        y = size * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16
        verts.append((x, y, 0))
    
    # Add the center vertex for triangulation
    verts.append((0, -size / 2, 0))
    center_index = len(verts) - 1
    
    # Create faces
    for i in range(steps):
        faces.append([i, (i + 1) % steps, center_index])
    
    # Create the mesh
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    # Set the mesh data
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    bpy.context.view_layer.objects.active = obj
    
    # Enter Edit mode
    bpy.ops.object.mode_set(mode='EDIT')

    # Extrude the surface
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={
        'value': (0, 0, 2)
    })
    
    bpy.ops.object.mode_set(mode='OBJECT')
    

    
    
    # Add Remesh modifier
    remesh = obj.modifiers.new(name="Remesh", type='REMESH')
    remesh.mode = 'SHARP'
    remesh.octree_depth = num_subdivisions + 1    
    remesh.scale = 0.9
    remesh.sharpness = 1.0 
    
    
    if "Remesh" in obj.modifiers:
        bpy.ops.object.modifier_apply(modifier="Remesh")
        
    bpy.ops.object.mode_set(mode='EDIT')
    
    
    # Get the mesh data
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Find the top coplanar faces
    bm.faces.ensure_lookup_table()
    top_faces = [f for f in bm.faces if f.normal == Vector((0, 0, 1))]

    top_normals = {tuple(f.normal) for f in top_faces}

    # Delete faces that are not coplanar with the top surfaces
    faces_to_delete = [f for f in bm.faces if tuple(f.normal) not in top_normals]

    bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES')
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Update the mesh
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()


    # Back to Object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    
    return obj




def create_rectangle(width, height):
    """Creates a rectangle at (0,0,0), subdivides it, and rotates it by 90 degrees."""
    verts = [
        (-width / 2, -height / 2, 0),  # Bottom-left
        (width / 2, -height / 2, 0),   # Bottom-right
        (width / 2, height / 2, 0),    # Top-right
        (-width / 2, height / 2, 0)    # Top-left
    ]
    faces = [[0, 1, 2, 3]]
    mesh = bpy.data.meshes.new("Rectangle")
    obj = bpy.data.objects.new("Rectangle", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    for _ in range(num_subdivisions+1):
        bpy.ops.mesh.subdivide(number_cuts=1)  # 1 cut per loop for even refinement
    #bpy.ops.mesh.subdivide(number_cuts=num_subdivisions)  # Can change number of subdivisions if needed
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.name = name
    obj.data.name = name
    
    return obj

# Get real elevation for a point
def get_elevation_single(lat, lon):
    """Fetches real elevation for a single latitude and longitude using OpenTopoData."""
    url = f"https://api.opentopodata.org/v1/{dataset}?locations={lat},{lon}"
    response = requests.get(url).json()
    elevation = response['results'][0]['elevation'] if 'results' in response else 0
    return elevation  # Scale down elevation to match Blender terrain


def get_elevation_openTopoData(coords, lenv = 0, pointsDone = 0):
    """Fetches real elevation for each vertex using OpenTopoData with request batching."""

    # Ensure the cache is loaded
    if not _elevation_cache:
        load_elevation_cache()

    # First, check which coordinates need fetching (not in cache)
    coords_to_fetch = []
    coords_indices = []

    elevations = [0] * len(coords)  # Pre-allocate list


    
    #check if coordinates are in cache or not
    for i, (lat, lon) in enumerate(coords):
        cached_elevation = get_cached_elevation(lat, lon)
        if cached_elevation is not None and disableCache == 0:
            # Use cached elevation
            elevations[i] = cached_elevation
        else:
            # Need to fetch this coordinate
            elevations[i] = -5
            coords_to_fetch.append((lat, lon))
            coords_indices.append(i)

    if len(coords) - len(coords_to_fetch) > 0:
        print(f"Using: {len(coords) - len(coords_to_fetch)} cached Coordinates")
    
    # If all elevations were found in cache, return immediately
    if not coords_to_fetch:
        return elevations
    
    #coords = [convert_to_geo(y, x, v[0], v[1]) for v in vertices]
    #elevations = []
    batch_size = 100
    for i in range(0, len(coords_to_fetch), batch_size):
        batch = coords_to_fetch[i:i + batch_size]
        query = "|".join([f"{c[0]},{c[1]}" for c in batch])
        url = f"https://api.opentopodata.org/v1/{dataset}?locations={query}"
        #print(url)
        last_request_time = time.monotonic()
        response = requests.get(url)
        nr = i + len(batch) + pointsDone
        addition = f" {nr}/{int(lenv)}"
        send_api_request(addition)
        response.raise_for_status()
        
        
        data = response.json()
        # Handle the elevation data and replace 'null' with 0
        for o, result in enumerate(data['results']):
            elevation = result.get('elevation', None)  # Safe get, default to None if key is missing
            if elevation is None:
                print("API RETURNED INVALID ELEVATION -> APPLIED 0")
                elevation = 0  # Replace None (null in JSON) with 0
            cache_elevation(batch[o][0], batch[o][1], elevation)
            ind = coords_indices[i+o]
            elevations[ind] = elevation
        
        # Get current time
        now = time.monotonic()  # Monotonic time is safer for measuring elapsed time
        elapsed_time = now - last_request_time
        if i + batch_size < len(coords_to_fetch) and elapsed_time < 1.3:
            time.sleep(1.3 - elapsed_time)  # Pause to prevent request throttling



    return elevations

def get_elevation_openElevation(coords, lenv = 0, pointsDone = 0):
    """Fetches real elevation for each vertex using Open-Elevation with request batching."""
    
    elevations = []
    batch_size = 1000
    for i in range(0, len(coords), batch_size):
        batch = coords[i:i + batch_size]
        # Open-Elevation expects a POST request with JSON body
        payload = {"locations": [{"latitude": c[0], "longitude": c[1]} for c in batch]}
        url = "https://api.open-elevation.com/api/v1/lookup"
        last_request_time = time.monotonic()
        
        headers = {'Content-Type': 'application/json'}
        nr = i + len(batch) + pointsDone
        addition = f" {nr}/{int(lenv)}"
        send_api_request(addition)
        
        response = requests.post(url, json=payload, headers=headers)
        
        #print(url)
        #print(payload)
        
        response.raise_for_status()

        data = response.json()
        
        
        # Handle the elevation data and replace 'null' with 0
        for result in data['results']:
            elevation = result.get('elevation', None)
            if elevation is None:
                elevation = 0
            elevations.append(elevation)
        
        # Get current time for request rate limiting
        now = time.monotonic()  
        elapsed_time = now - last_request_time
        if elapsed_time < 2:
            time.sleep(2 - elapsed_time)  # Pause to prevent request throttling

    return elevations

def get_elevation_path_openElevation(vertices):
    """Fetches real elevation for each vertex using OpenTopoData with request batching."""
    v = vertices
    coords = [(v[0], v[1], v[2], v[3]) for v in vertices]
    elevations = []
    batch_size = 1000
    for i in range(0, len(coords), batch_size):
        batch = coords[i:i + batch_size]
        # Open-Elevation expects a POST request with JSON body
        payload = {"locations": [{"latitude": c[0], "longitude": c[1]} for c in batch]}
        url = "https://api.open-elevation.com/api/v1/lookup"
        last_request_time = time.monotonic()
        
        headers = {'Content-Type': 'application/json'}

        addition = f"(overwrite path) {i + len(batch)}/{len(coords)}"
        send_api_request(addition)

        response = requests.post(url, json=payload, headers=headers)
        
        #print(url)
        #print(payload)
        
        response.raise_for_status()

        data = response.json()
        
        elevations.extend([r['elevation'] for r in data['results']])
        now = time.monotonic()  # Monotonic time is safer for measuring elapsed time
        elapsed_time = now - last_request_time
        if i + batch_size < len(coords) and elapsed_time < 1.4:
            time.sleep(1.4 - elapsed_time)  # Pause to prevent request throttling
    
    for i in range(len(vertices)):
        coords[i] =  (coords[i][0], coords[i][1], elevations[i], coords[i][3])
        #print(elevations[i])
    
    return coords
# Get real elevation for each vertex

def get_elevation_path_openTopoData(vertices):
    """Fetches real elevation for each vertex using OpenTopoData with request batching."""
    v = vertices
    coords = [(v[0], v[1], v[2], v[3]) for v in vertices]
    elevations = []
    batch_size = 100
    for i in range(0, len(coords), batch_size):
        batch = coords[i:i + batch_size]
        query = "|".join([f"{c[0]},{c[1]}" for c in batch])
        url = f"https://api.opentopodata.org/v1/{dataset}?locations={query}"
        last_request_time = time.monotonic()
        response = requests.get(url).json()
        addition = f"(overwrite path) {i + len(batch)}/{len(coords)}"
        send_api_request(addition)
        
        elevations.extend([r['elevation'] for r in response['results']])
        now = time.monotonic()  # Monotonic time is safer for measuring elapsed time
        elapsed_time = now - last_request_time
        if i + batch_size < len(coords) and elapsed_time < 1.4:
            time.sleep(1.4 - elapsed_time)  # Pause to prevent request throttling
    
    for i in range(len(vertices)):
        coords[i] =  (coords[i][0], coords[i][1], elevations[i], coords[i][3])
        #print(elevations[i])
    
    return coords

# Get tile elevation
def get_tile_elevation(obj):
    mesh = obj.data
    global api
    
    #Split in chunk size
    chunk_size = 1000
    vertices = list(mesh.vertices)
    elevations = []
    for i in range(0, len(vertices), chunk_size):
        chunk = vertices[i:i + chunk_size]
        if api == 1:
            vertos = [c.co for c in chunk ]
            coords = [convert_to_geo(obj.location.y, obj.location.x, v[0], v[1]) for v in vertos]
            chunk_elevations = get_elevation_openElevation(coords, len(vertices), int((i)))
        else:
            vertos = [c.co for c in chunk ]
            coords = [convert_to_geo(obj.location.y, obj.location.x, v[0], v[1]) for v in vertos]
            chunk_elevations = get_elevation_openTopoData(coords, len(vertices), int((i)))
    
            
        elevations.extend(chunk_elevations)



        #Free memory after processing chunk
        del chunk_elevations

    save_elevation_cache()

    lowestZ = min(elevations)
    highestZ = max(elevations)
    global additionalExtrusion
    additionalExtrusion = lowestZ
    diff = highestZ - lowestZ
    
    bpy.context.scene.my_tool["o_verticesMap"] = "Map vertices: " + str(len(mesh.vertices))

    return elevations, diff

# Transform MapObject
def transform_MapObject(obj, newX, newY):
    obj.location.x += newX
    obj.location.y += newY

def haversine(lat1, lon1, lat2, lon2):
    """Calculates the great-circle distance between two points using the Haversine formula."""
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c  # distance in kilometers
    #print(f"Distance between 2 points: {distance}")
    return distance
    
    
def calculate_total_length(points):
    """Calculates the total path length in kilometers."""
    total_distance = 0.0
    for i in range(1, len(points)):
        lon1, lat1, _, _ = points[i - 1]
        lon2, lat2, _, _ = points[i]
        total_distance += haversine(lon1, lat1, lon2, lat2)
    return total_distance

def calculate_total_elevation(points):
    """Calculates the total elevation gain in meters."""
    total_elevation = 0.0
    for i in range(1, len(points)):
        _, _, elev1, _ = points[i - 1]
        _, _, elev2, _ = points[i]
        if elev2 > elev1:
            total_elevation += elev2 - elev1
    return total_elevation

def calculate_total_time(points):
    hrs = 0
    """Calculates the total time taken between the first and last points."""
    if len(points) < 2:
        return 0.0
    start_time = points[0][3]
    end_time = points[-1][3]
    if start_time != None and end_time != None:
        time_diff = end_time - start_time
        hours = int(time_diff.total_seconds() / 3600)
        minutes = int((time_diff.total_seconds() / 3600 - hours) * 60)
        time_str = f"{hours}h {minutes}m"
        #print(time_str)
        hrs = time_diff.total_seconds() / 3600
    
    return hrs

def update_text_object(obj_name, new_text):
    """Updates the text of a Blender text object."""
    text_obj = bpy.data.objects.get(obj_name)
    if text_obj and text_obj.type == 'FONT':
        text_obj.data.body = new_text
        
def export_to_STL(Obj,flname):
    
    Obj.select_set(True)  # Select the object
    
    
    bpy.ops.wm.stl_export(filepath=exportPath +  flname, export_selected_objects = True)

    #print(exportPath + Obj.name + ".stl")
    #bpy.ops.export_mesh.stl(filepath=exportPath +  curveObj.name + ".stl", use_selection=True)
    
    Obj.select_set(False)  # Select the object

def export_selected_to_STL():

    active_obj = bpy.context.active_object

    bpy.ops.wm.stl_export(filepath=exportPath +  active_obj.name + ".stl", export_selected_objects = True)




def zoom_camera_to_selected(obj):
    
    bpy.ops.object.select_all(action='DESELECT')
    
    obj.select_set(True)  # Select the object
    
    area = [area for area in bpy.context.screen.areas if area.type == "VIEW_3D"][0]
    region = area.regions[-1]

    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.view3d.view_selected(use_all_regions=False)
        
        
def create_text(name, text, position, scale_multiplier, rotation=(0, 0, 0), extrude=20):
    txt_data = bpy.data.curves.new(name=name, type='FONT')
    txt_obj = bpy.data.objects.new(name=name, object_data=txt_data)
    bpy.context.collection.objects.link(txt_obj)
    
    global textFont

    txt_data.body = text
    txt_data.extrude = extrude
    #txt_data.font = bpy.data.fonts.load("C:/Windows/Fonts/ariblk.ttf")  # Adjust path if needed
    txt_data.font = bpy.data.fonts.load(textFont)
    txt_data.align_x = 'CENTER'
    txt_data.align_y = "CENTER"
    
    txt_obj.scale = (scale_multiplier, scale_multiplier, 1)
    txt_obj.location = position
    txt_obj.rotation_euler = rotation
    
    txt_obj.location.z -= 1
    
    return txt_obj

def HexagonInnerText():
    
    global total_elevation
    global total_length
    
    thickness = 5
        # Place text objects
    text_size = (size / 2) * (1 - pathScale / 200) * 0.2 * (textSize / 5)
    
    
    dist =  (size/2 - size/2 * (1-pathScale)/2)
    
    temp_y = math.sin(math.radians(90)) * (dist  * math.cos(math.radians(30)))
    

    
    t_name = create_text("t_name", "Name", (0, temp_y, 0.1),text_size)

    
    angle_offset = math.radians(30)
    for i, (text_name, angle) in enumerate(zip(["t_length", "t_elevation", "t_duration"], [210, 270, 330])):
        angle_centered = angle + 90
        x = math.cos(math.radians(angle)) * (dist * math.cos(math.radians(30)))
        y = math.sin(math.radians(angle)) * (dist * math.cos(math.radians(30)))
        rot_z = math.radians(angle_centered)
        create_text(text_name, text_name.split("_")[1].capitalize(), (x, y, 0.1),text_size,  (0, 0, rot_z), 100)
    
    tName = bpy.data.objects.get("t_name")
    tElevation = bpy.data.objects.get("t_elevation")
    tLength = bpy.data.objects.get("t_length")
    tDuration = bpy.data.objects.get("t_duration")
    

    
    transform_MapObject(tName, centerx, centery)
    transform_MapObject(tElevation, centerx, centery)
    transform_MapObject(tLength, centerx, centery)
    transform_MapObject(tDuration, centerx, centery)
    
    
    update_text_object("t_name", f"{name}")
    update_text_object("t_elevation", f"{total_elevation:.2f} m")
    update_text_object("t_length", f"{total_length:.2f} km")
    update_text_object("t_duration", f"{time_str}")

    if overwriteLength != "":
        update_text_object("t_length", overwriteLength)
    if overwriteHeight != "":
        update_text_object("t_elevation", overwriteHeight)
    if overwriteTime != "":
        update_text_object("t_duration", overwriteTime)
    
    convert_text_to_mesh("t_name", obj.name)
    convert_text_to_mesh("t_elevation", obj.name)
    convert_text_to_mesh("t_length", obj.name)
    convert_text_to_mesh("t_duration", obj.name)
    
    
    bpy.ops.object.select_all(action='DESELECT')

    tName.select_set(True)
    tElevation.select_set(True)
    tLength.select_set(True)
    tDuration.select_set(True)
    #curveObj.select_set(True)
    
    bpy.context.view_layer.objects.active = tName
    
    bpy.ops.object.join()

    tName.name = name + "_Text"
    
def HexagonOuterText():


    
    outersize = size * ( 1 + outerBorderSize/100)
    thickness = 5
    
    
    verts = []
    faces = []
    for i in range(6):
        angle = math.radians(60 * i)
        x = outersize/2 * math.cos(angle)
        y = outersize/2 * math.sin(angle)
        verts.append((x, y, 0))
    verts.append((0, 0, 0))  # Center vertex
    faces = [[i, (i + 1) % 6, 6] for i in range(6)]
    mesh = bpy.data.meshes.new("HexagonOuter")
    outerHex = bpy.data.objects.new("HexagonOuter", mesh)
    bpy.context.collection.objects.link(outerHex)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    outerHex.name = name
    outerHex.data.name = name
    
    bpy.context.view_layer.objects.active = outerHex
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move()
    bpy.ops.transform.translate(value=(0, 0, -8))#bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.mode_set(mode='OBJECT')

    # Get the mesh data
    mesh = outerHex.data

    # Get selected faces
    selected_faces = [face for face in mesh.polygons if face.select]
    
    if selected_faces:
        for face in selected_faces:
            for vert_idx in face.vertices:
                vert = mesh.vertices[vert_idx]
                vert.co.z =  - thickness;
    else:
        print("No face selected.")
    
    transform_MapObject(outerHex, centerx, centery)
    
        # Place text objects
        
    text_size = (size / 2) * (1 - pathScale / 200) * 0.2 * (textSize / 5)
    
    dist = (outersize - size)/4 + size/2
    #dist =  (size/2 + size/2 * (1-pathScale)/2)
    
    temp_y = math.sin(math.radians(90)) * (dist  * math.cos(math.radians(30)))
    
    
    #t_name = create_text("t_name", "Name", (0, temp_y, 1 + additionalExtrusion - 2 ),text_size,(0, 0, 0),0.4)

    for i, (text_name, angle) in enumerate(zip(["t_name","t_length", "t_elevation", "t_duration"], [90 + text_angle_preset, 210 + text_angle_preset, 270 + text_angle_preset, 330 + text_angle_preset])):
        angle_centered = angle + 90
        x = math.cos(math.radians(angle)) * (dist * math.cos(math.radians(30)))
        y = math.sin(math.radians(angle)) * (dist * math.cos(math.radians(30)))
        rot_z = math.radians(angle_centered)
        if i == 0:
            rot_z += math.radians(180)
        create_text(text_name, text_name.split("_")[1].capitalize(), (x, y,1.4),text_size,  (0, 0, rot_z), 0.4)
    
    tName = bpy.data.objects.get("t_name")
    tElevation = bpy.data.objects.get("t_elevation")
    tLength = bpy.data.objects.get("t_length")
    tDuration = bpy.data.objects.get("t_duration")
    
    
    transform_MapObject(tName, centerx, centery)
    transform_MapObject(tElevation, centerx, centery)
    transform_MapObject(tLength, centerx, centery)
    transform_MapObject(tDuration, centerx, centery)
    
    
    update_text_object("t_name", f"{name}")
    update_text_object("t_elevation", f"{total_elevation:.2f} m")
    update_text_object("t_length", f"{total_length:.2f} km")
    update_text_object("t_duration", f"{time_str}")

    if overwriteLength != "":
        update_text_object("t_length", overwriteLength)
    if overwriteHeight != "":
        update_text_object("t_elevation", overwriteHeight)
    if overwriteTime != "":
        update_text_object("t_duration", overwriteTime)

    
    convert_text_to_mesh("t_name", outerHex.name, False)
    convert_text_to_mesh("t_elevation", outerHex.name, False)
    convert_text_to_mesh("t_length", outerHex.name, False)
    convert_text_to_mesh("t_duration", outerHex.name, False)
    
    
    bpy.ops.object.select_all(action='DESELECT')
    
    tName.select_set(True)
    tElevation.select_set(True)
    tLength.select_set(True)
    tDuration.select_set(True)
    
    bpy.context.view_layer.objects.active = tName

    
    bpy.ops.object.join()

    tName.name = name + "_Text"
    outerHex.name = name + "_Plate"
    
def BottomText():
    
    global total_elevation
    global total_length
    
    thickness = 0.1
        # Place text objects
    text_size = (size / 15)
    
    
    dist =  (size/2 - size/2 * (1-pathScale)/2)
    
    temp_y = size/4
    
    
    global additionalExtrusion
    
    tname = create_text("t_name", "Name", (0, temp_y,1.1 +  additionalExtrusion - 2),text_size)
    tElevation = create_text("t_elevation","Elevation",(0,temp_y*0.33,1.1 + additionalExtrusion - 2), text_size)
    tLength = create_text("t_length","Length",(0,-temp_y*0.33,1.1 + additionalExtrusion - 2), text_size)
    tDuration = create_text("t_duration","Duration",(0,-temp_y,1.1+ additionalExtrusion - 2), text_size)
    
    tName = bpy.data.objects.get("t_name")
    tElevation = bpy.data.objects.get("t_elevation")
    tLength = bpy.data.objects.get("t_length")
    tDuration = bpy.data.objects.get("t_duration")
    
    transform_MapObject(tName, centerx, centery)
    transform_MapObject(tElevation, centerx, centery)
    transform_MapObject(tLength, centerx, centery)
    transform_MapObject(tDuration, centerx, centery)
    
    tName.data.extrude = 0.1
    tElevation.data.extrude = 0.1
    tLength.data.extrude = 0.1
    tDuration.data.extrude = 0.1
    
    tName.scale.x *= -1
    tElevation.scale.x *= -1
    tLength.scale.x *= -1
    tDuration.scale.x *= -1
    
    update_text_object("t_name", f"{name}")
    update_text_object("t_elevation", f"{total_elevation:.2f} m")
    update_text_object("t_length", f"{total_length:.2f} km")
    update_text_object("t_duration", f"{time_str}")
    
    convert_text_to_mesh("t_name", obj.name, False)
    convert_text_to_mesh("t_elevation", obj.name, False)
    convert_text_to_mesh("t_length", obj.name, False)
    convert_text_to_mesh("t_duration", obj.name, False)
    
    
    bpy.ops.object.select_all(action='DESELECT')

    tName.select_set(True)
    tElevation.select_set(True)
    tLength.select_set(True)
    tDuration.select_set(True)
    curveObj.select_set(True)
    
    bpy.context.view_layer.objects.active = curveObj
    
    bpy.ops.object.join()
    

def convert_text_to_mesh(text_obj_name, mesh_obj_name, merge = True):
    # Get the text and mesh objects
    text_obj = bpy.data.objects.get(text_obj_name)
    mesh_obj = bpy.data.objects.get(mesh_obj_name)
    
    if not text_obj or not mesh_obj:
        print("One or both objects not found")
        return
    
    # Ensure the text object is selected and active
    bpy.ops.object.select_all(action='DESELECT')
    text_obj.select_set(True)
    bpy.context.view_layer.objects.active = text_obj
    
    # Convert text to mesh
    bpy.ops.object.convert(target='MESH')
    
    # Enter edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Enable auto-merge vertices
    bpy.context.tool_settings.use_mesh_automerge = True
    
    # Switch back to object mode to move it
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Move the text object up by 1
    text_obj.location.z += 1
    
    # Move the text object down by 1 (merging overlapping vertices)
    text_obj.location.z -= 1
    
    # Disable auto-merge vertices
    bpy.context.tool_settings.use_mesh_automerge = False
    
    if merge == True:
        # Add boolean modifier
        bool_mod = text_obj.modifiers.new(name="Boolean", type='BOOLEAN')
        bool_mod.object = mesh_obj
        bool_mod.operation = 'INTERSECT'
        bool_mod.solver = 'FAST'
        
        # Apply the boolean modifier
        bpy.ops.object.select_all(action='DESELECT')
        text_obj.select_set(True)
        bpy.context.view_layer.objects.active = text_obj
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    
        # Move the text object up by 1
        text_obj.location.z += 0.4

def intersect_trails_with_existing_box(cutobject):
    # Get the box object

    cutobject.scale.z = 1000
    bpy.context.view_layer.objects.active = cutobject
    bpy.ops.object.transform_apply(scale=True)
    
    #cube = bpy.data.objects.get(cutobject)
    cube = cutobject
    if not cube:
        print(f"Object named '{cutobject}' not found.")
        return

    # Get cube's bounding box in world coordinates
    cube_bb = [cube.matrix_world @ Vector(corner) for corner in cube.bound_box]

    def is_point_inside_cube(point, bb):
        min_corner = Vector((min(v[0] for v in bb),
                             min(v[1] for v in bb),
                             min(v[2] for v in bb)))
        max_corner = Vector((max(v[0] for v in bb),
                             max(v[1] for v in bb),
                             max(v[2] for v in bb)))
        return all(min_corner[i] <= point[i] <= max_corner[i] for i in range(3))

    for obj in bpy.data.objects:
        if "_Trail" in obj.name and obj.type in {'CURVE', 'MESH'}:
            # Convert curve to mesh
            if obj.type == 'CURVE':
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.ops.object.convert(target='MESH')
                trail_mesh = bpy.context.object
            else:
                trail_mesh = obj

            # Check if any vertex is inside the cube
            for v in trail_mesh.data.vertices:
                global_coord = trail_mesh.matrix_world @ v.co
                if is_point_inside_cube(global_coord, cube_bb):
                    # Apply Boolean modifier
                    bool_mod = cube.modifiers.new(name=f"Intersect_{trail_mesh.name}", type='BOOLEAN')
                    bool_mod.operation = 'INTERSECT'
                    bool_mod.object = trail_mesh
                    bpy.context.view_layer.objects.active = cube
                    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
                    break  # No need to keep checking this object

def separate_duplicate_xy(coordinates, offset=0.05):
    seen_xy = set()

    for i, point in enumerate(coordinates):
        # Convert tuple to list if needed
        if isinstance(point, tuple):
            point = list(point)
            coordinates[i] = point  # Update the original array with the list version

        x, y, z = point[0], point[1], point[2]
        xy_key = (x, y,z)

        if xy_key in seen_xy:
            point[2] += offset
            point[1] += offset
            #print("Duplicate")
        else:
            seen_xy.add(xy_key)
    
    return(coordinates)

def single_color_mode(crv, mapName):


    map = bpy.data.objects.get(mapName)
    
    crv_data = crv.data
    crv_data.dimensions = "2D"
    crv_data.dimensions = "3D"
    crv_data.extrude = 200

    #Create a duplicate object of the curve that will be slightly thicker
    crv_thick = crv.copy()
    crv_thick.data = crv.data.copy()
    #crv_thick.data.bevel_depth = pathThickness * 1.1  # Set the thickness of the curve
    crv_thick.data.bevel_depth = pathThickness + scmTolerance # Set the thickness of the curve
    bpy.context.collection.objects.link(crv_thick)

    # Ensure the text object is selected and active
    bpy.ops.object.select_all(action='DESELECT')
    crv.select_set(True)
    bpy.context.view_layer.objects.active = crv
    bpy.ops.object.convert(target='MESH')

    # Add boolean modifier
    bool_mod = crv.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.object = map
    bool_mod.operation = 'INTERSECT'
    bool_mod.solver = 'FAST'

    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    #crv.location.z += 1
    for v in crv.data.vertices:
        v.co += Vector((0,0,1))

    #Adding another Intersect Modifier to make the path "Plane" with the Map
    # Add boolean modifier
    bool_mod = crv.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.object = map
    bool_mod.operation = 'INTERSECT'
    bool_mod.solver = 'FAST'

    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    #doing the same for the duplicate
    bpy.ops.object.select_all(action='DESELECT')
    crv_thick.select_set(True)
    bpy.context.view_layer.objects.active = crv_thick
    bpy.ops.object.convert(target='MESH')

    # Add boolean modifier
    bool_mod = crv_thick.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.object = map
    bool_mod.operation = 'INTERSECT'
    bool_mod.solver = 'FAST'

    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    # Move the text object up by x
    crv_thick.location.z += 1

    bpy.ops.object.select_all(action='DESELECT')
    map.select_set(True)
    bpy.context.view_layer.objects.active = map

    bool_mod = map.modifiers.new(name="Boolean", type="BOOLEAN")
    bool_mod.object = crv_thick
    bool_mod.operation = "DIFFERENCE"
    bool_mod.solver = "FAST"

    bpy.ops.object.modifier_apply(modifier = bool_mod.name)
    bpy.data.objects.remove(crv_thick, do_unlink = True)





def show_message_box(message, ic = "ERROR", ti = "ERROR"):
    #toggle_console()
    def draw(self, context):
        self.layout.label(text=message)
    print(message)
    bpy.context.window_manager.popup_menu(draw, title=ti, icon=ic)

def toggle_console():
    try:
        if platform.system() == "Windows":
            bpy.ops.wm.console_toggle()
    except Exception as e:
        print(f"Could not toggle console: {e}")
    
def runGeneration(type):   
    
    start_time = time.time()

    toggle_console()
    
    for i in range(30):
        print(" ")
    print("------------------------------------------------")
    print("SCRIPT STARTED - DO NOT CLOSE THIS WINDOW")
    print("------------------------------------------------")
    print(" ")

    # Path to your GPX file
    global gpx_file_path
    gpx_file_path = bpy.context.scene.my_tool.get('file_path', None)
    global gpx_chain_path
    gpx_chain_path = bpy.context.scene.my_tool.get('chain_path', None)
    global exportPath
    exportPath = bpy.context.scene.my_tool.get('export_path', None)
    global shape
    shape = (bpy.context.scene.my_tool.shape)
    global name
    name = bpy.context.scene.my_tool.get('trailName', "")
    global size
    size =  bpy.context.scene.my_tool.get('objSize', 100)
    global num_subdivisions
    num_subdivisions = bpy.context.scene.my_tool.get('num_subdivisions', 4)
    global scaleElevation
    scaleElevation = bpy.context.scene.my_tool.get('scaleElevation', 10)
    global pathThickness
    pathThickness = bpy.context.scene.my_tool.get('pathThickness', 0.6)
    global pathScale
    pathScale = bpy.context.scene.my_tool.get('pathScale', 0.8)
    global shapeRotation
    shapeRotation = bpy.context.scene.my_tool.get('shapeRotation', 0)
    global overwritePathElevation
    overwritePathElevation = bpy.context.scene.my_tool.get('overwritePathElevation', False)
    global api
    api = bpy.context.scene.my_tool.get('api',0)
    global dataset
    dataset_int = bpy.context.scene.my_tool.get("dataset",1)
    global fixedElevationScale
    fixedElevationScale = bpy.context.scene.my_tool.get('fixedElevationScale', False)
    global baseThickness
    baseThickness = bpy.context.scene.my_tool.get("baseThickness",2)
    global xTerrainOffset
    xTerrainOffset = bpy.context.scene.my_tool.get("xTerrainOffset",0)
    global yTerrainOffset
    yTerrainOffset = bpy.context.scene.my_tool.get("yTerrainOffset",0)
    global singleColorMode
    singleColorMode = bpy.context.scene.my_tool.get("singleColorMode",0)
    global scmTolerance
    scmTolerance = bpy.context.scene.my_tool.get("scmTolerance",0)
    global disableCache
    disableCache = bpy.context.scene.my_tool.get("disableCache",0)

    #OTHER VARIABLES FOR TEXT BASED SHAPES
    #Add input fields
    global textFont
    textFont = bpy.context.scene.my_tool.get("textFont","")
    global textSize
    textSize = bpy.context.scene.my_tool.get("textSize",10)
    global overwriteLength
    overwriteLength = bpy.context.scene.my_tool.get("overwriteLength","")
    global overwriteHeight
    overwriteHeight = bpy.context.scene.my_tool.get("overwriteHeight","")
    global overwriteTime
    overwriteTime = bpy.context.scene.my_tool.get("overwriteTime","")
    global outerBorderSize
    outerBorderSize = bpy.context.scene.my_tool.get("outerBorderSize",20)
    global text_angle_preset
    text_angle_preset = int(bpy.context.scene.my_tool.text_angle_preset)

    if dataset_int == 0: dataset = "srtm30m"
    elif dataset_int == 1: dataset = "aster30m"
    elif dataset_int == 2: dataset = "ned10m"
    elif dataset_int == 3: dataset = "mapzen"
    else: dataset = "aster30m"

    #print(f"Dataset selected: {dataset}")
    if name == "":
        if type == 0:
            name_with_ext = os.path.basename(gpx_file_path)
            name = os.path.splitext(name_with_ext)[0]
        if type == 1:
            name_with_ext = os.path.basename(os.path.normpath(gpx_chain_path))
            name = os.path.splitext(name_with_ext)[0]

    
    #check for valid values
    if type == 0:
        #print(gpx_file_path)
        gpx_file_path = bpy.path.abspath(gpx_file_path)
        #print(gpx_file_path)
        
        if not gpx_file_path or gpx_file_path == "":
            show_message_box("File path is empty! Please select a valid file.")
            return
        
        if not os.path.isfile(gpx_file_path):
            show_message_box(f"Invalid file path: {gpx_file_path}. Please select a valid file.")
            return
    
    if type == 1:
        gpx_chain_path = bpy.path.abspath(gpx_chain_path)
        if not gpx_chain_path or gpx_chain_path == "":
            show_message_box("CHAIN path is empty! Please select a valid folder.")
            return
    
    if exportPath == None:
        show_message_box("Export path cant be empty")
        return
    
    exportPath = bpy.path.abspath(exportPath)

    if not exportPath or exportPath == "":
        show_message_box("Export path is empty! Please select a valid folder.")
        return
    if not os.path.isdir(exportPath):
        show_message_box(f"Invalid export Directory: {exportPath}. Please select a valid Directory.")
        return


    if textFont == "" and (shape == "HEXAGON OUTER TEXT" or shape == "HEXAGON INNER TEXT"):
        if platform.system() == "Windows":
            textFont = "C:/WINDOWS/FONTS/ariblk.ttf"
        elif platform.system() == "Darwin":
            textFont = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
        else:
            show_message_box(f"Please select a font in the Shape Settings Tab.")
            return
             
    #STARTSETTINGS
    #Leave edit mode      
    if bpy.context.object and bpy.context.object.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Disable Auto Merge Vertices
    bpy.context.scene.tool_settings.use_mesh_automerge = False
        
        
    # Load GPX data        
    try:
        if type == 0:
            
            file_extension = os.path.splitext(gpx_file_path)[1].lower()
            if file_extension == '.gpx':
                tree = ET.parse(gpx_file_path)
                root = tree.getroot()
                version = root.get("version")
                
                if version == "1.0":
                    coordinates = read_gpx_1_0(gpx_file_path)
                if version == "1.1":
                    coordinates = read_gpx_1_1(gpx_file_path)
            elif file_extension == '.igc':
                coordinates = read_igc(gpx_file_path)
            else:
                show_message_box("Unsupported file format. Please use .gpx or .igc files.")
                return
        if type == 1:
            coordinates, separate_paths = read_gpx_directory(gpx_chain_path)
    except Exception as e:
        show_message_box("GPX file seems to have wrong format")
        return
    #Calculating some Stats about the path
    global total_length
    global total_elevation
    global total_time
    total_length = calculate_total_length(coordinates)
    total_elevation = calculate_total_elevation(coordinates)
    total_time = calculate_total_time(coordinates)

    hours = int(total_time)
    minutes = int((total_time - hours) * 60)
    global time_str
    time_str = f"{hours}h {minutes}m"

    while len(coordinates) < 300:
        i = 0
        while i < len(coordinates) - 1:
            p1 = coordinates[i]
            p2 = coordinates[i + 1]

            # Calculate midpoint (only for x, y, z)
            midpoint = [
                (p1[0] + p2[0]) / 2,
                (p1[1] + p2[1]) / 2,
                (p1[2] + p2[2]) / 2,
                (p1[3])  # Optional: interpolate time too
            ]

            # Insert midpoint before p2
            coordinates.insert(i + 1, midpoint)

            # Skip over the new point and the original next point
            i += 2

    #Simplifying the Path
    #placed somewhere else

    #CALCULATE biggest distance so you can calculate the value for the smoothing
    min_x = min(point[0] for point in coordinates)
    max_x = max(point[0] for point in coordinates)
    min_y = min(point[1] for point in coordinates)
    max_y = max(point[1] for point in coordinates)
    p1 = convert_to_blender_coordinates(min_x, min_y, 0,"")
    p2 = convert_to_blender_coordinates(max_x,max_y, 0,"")

    distance = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


    #Überschreiben der elevation werte der GXP mit den Elevation werte der gleichen API mit der das Terrain erstellt wird
    if overwritePathElevation == True:
        print(" ")
        print(" ")
        print("------------------------------------------------")
        print("FETCHING ELEVATION DATA FOR THE PATH")
        print("------------------------------------------------")
        print(" ")
        try:
            if type == 0:
                if api == 1:
                    coordinates = get_elevation_path_openElevation(coordinates)
                else:
                    coordinates = get_elevation_path_openTopoData(coordinates)
            if type == 1:
                if api == 1:
                    separate_paths = [get_elevation_path_openElevation(path) for path in separate_paths]
                else:
                    separate_paths = [get_elevation_path_openTopoData(path) for path in separate_paths]
        except Exception as e:
            show_message_box("Bad Response from API. This may happen sometimes")
            return
    
    #CALCULATE SCALE 
    global scaleHor
    scaleHor = calculate_scale(size, coordinates)
    print(f"scaleHor: {scaleHor}")

    bpy.context.scene.my_tool["sScaleHor"] = scaleHor


    

    # Convert coordinates to Blender format and create a curve
    #print("Converting Coordinates to Blender format coordinates for X and Y coordsd")
    blender_coords = [convert_to_blender_coordinates(lat, lon, ele,timestamp) for lat, lon, ele, timestamp in coordinates]
    
    if type == 1:
        blender_coords_separate = [
            [convert_to_blender_coordinates(lat, lon, ele, timestamp) for lat, lon, ele, timestamp in path]
            for path in separate_paths
            ]

  
    
    #CALCULATE CENTER
    min_x = min(point[0] for point in blender_coords)
    max_x = max(point[0] for point in blender_coords)
    min_y = min(point[1] for point in blender_coords)
    max_y = max(point[1] for point in blender_coords)
    
    global centerx
    global centery
    centerx = (max_x-min_x)/2 + min_x
    centery = (max_y-min_y)/2 + min_y
    
    #DELETE OBJECTS THAT SIT AT THE CENTER TO PREVENT OVERLAPPING
    target_location = Vector((centerx,centery,0))
    for obs in bpy.data.objects:
        if (obs.location - target_location).length <= 0.1:
            bpy.data.objects.remove(obs, do_unlink = True)
            print("deleted overlapping object (Previous generated objects)")

    bpy.ops.object.select_all(action='DESELECT')
    # CREATE SHAPES
    #print("Creating MapObject")
    if shape == "HEXAGON": #hexagon
        MapObject = create_hexagon(size/2)
    elif shape == "SQUARE": #rectangle
        MapObject = create_rectangle(size,size)
    elif shape == "HEXAGON INNER TEXT": #Hexagon with inner text
        MapObject = create_hexagon(size/2)
    elif shape == "HEXAGON OUTER TEXT": #Hexagon with outer text
        MapObject = create_hexagon(size/2)
    elif shape == "HEARTH": #Hearth
        MapObject = create_heart(size/2)
    else:
        MapObject = create_hexagon(size/2)
        
    
    #SHAPE ROTATION
    offsetRotation = 45
    MapObject.rotation_euler[2] += shapeRotation * (3.14159265 / 180)
    MapObject.select_set(True)
    bpy.context.view_layer.objects.active = MapObject
    bpy.ops.object.transform_apply(location = False, rotation=True, scale = False)
    #move object to the center of the path
    transform_MapObject(MapObject, centerx + xTerrainOffset, centery + yTerrainOffset)
    

    #fetch and apply the elevation
    print("------------------------------------------------")
    print("FETCHING ELEVATION DATA FOR THE MAP")
    print("------------------------------------------------")
    
    global autoScale
    tileVerts, diff = get_tile_elevation(MapObject)
    
    if fixedElevationScale == True:
        if diff > 0:
            autoScale = 10/(diff/1000)
        else:
            autoScale = 10
    else:
        autoScale = scaleHor
    
    #print(f"autoScale: {autoScale}")

    bpy.context.scene.my_tool["sAutoScale"] = autoScale

    #print(f"elev: {(diff/1000) * autoScale * scaleElevation}")

    if fixedElevationScale == False:
        if diff == 0:
            show_message_box("Terrain seems to be Flat. Might not have Elevation data for that Region. Try Diffrent Api or diffrent Datasets")
        elif (diff/1000) * autoScale * scaleElevation < 2 :
            show_message_box("Terrain seems to be Flat. Increasing ScaleElevation could helpk", "INFO")

    
    #RECALCULATE THE COORDS WITH AUTOSCALE APPLIED
    blender_coords = [convert_to_blender_coordinates(lat, lon, ele,timestamp) for lat, lon, ele, timestamp in coordinates]

    blender_coords = simplify_curve(blender_coords, .12)

    #PREVENT CLIPPING OF IDENTICAL COORDINATES
    blender_coords = separate_duplicate_xy(blender_coords, 0.05) 
    
    if type == 1:
        blender_coords_separate = [
            [convert_to_blender_coordinates(lat, lon, ele, timestamp) for lat, lon, ele, timestamp in path]
            for path in separate_paths
            ]
    

    #calculate real Scale
    tdist = 0
    lat1 = coordinates[0][0]
    lon1 = coordinates[0][1]
    lat2 = coordinates[-1][0]
    lon2 = coordinates[-1][1]
    tdist = haversine(lat1,lon1 ,lat2 , lon2)
    #print(f"lat1: {lat1} | lon1: {lon1} ||| lat2: {lat2} | lon2: {lon2}")
    #print(f"tdist:{tdist}")
    mscale = (tdist/size) * 1000000
    #print(f"scale: {mscale}")
    bpy.context.scene.my_tool["o_mapScale"] = f"Map Scale: 1:{mscale:.0f}"

            
    #CREATE THE PATH
    #print("Creating Curve")

    if type == 0:
            create_curve_from_coordinates(blender_coords)
    if type == 1:
        for crds in blender_coords_separate:
            create_curve_from_coordinates(crds)

    try:
        #if type == 0:
        #    create_curve_from_coordinates(blender_coords)
        #if type == 1:
        #    for crds in blender_coords_separate:
        #        create_curve_from_coordinates(crds)
                
            bpy.ops.object.join()
        #print("Curve Created")
    except Exception as e:
        show_message_box("Bad Response from API while creating the curve. This may happen sometimes")
        return
    
    global curveObj
    curveObj = bpy.context.view_layer.objects.active
    
    bpy.ops.object.select_all(action='DESELECT')
    
    
    
    mesh = MapObject.data
        
    
    lowestZ = 1000
    for i, vert in enumerate(mesh.vertices):
        vert.co.z = (tileVerts[i] - elevationOffset)/1000 * scaleElevation * autoScale
        if vert.co.z < lowestZ:
            lowestZ = vert.co.z
            
    global additionalExtrusion
    additionalExtrusion = lowestZ

    bpy.context.scene.my_tool["sAdditionalExtrusion"] = additionalExtrusion
    
    
    
    

    # Extrude hexagon to z=0 and scale bottom face
    #bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'
    bpy.context.view_layer.objects.active = MapObject
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move()
    bpy.ops.transform.translate(value=(0, 0, -1))#bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    global obj
    obj = bpy.context.object


    # Get the mesh data
    mesh = obj.data
    # Get selected faces
    selected_faces = [face for face in mesh.polygons if face.select]
    
    
    if selected_faces:
        for face in selected_faces:
            for vert_idx in face.vertices:
                vert = mesh.vertices[vert_idx]
                vert.co.z = additionalExtrusion - baseThickness
    else:
        print("No face selected.")
    
    #CHANGE OBJECT ORIGIN
    bpy.context.view_layer.objects.active = MapObject
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.translate(value=(0, 0, -additionalExtrusion+baseThickness))#bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.context.view_layer.objects.active = curveObj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.transform.translate(value=(0, 0, -additionalExtrusion+baseThickness))#bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    
    
    #ADDITIONAL SHIT
    if shape == "HEXAGON INNER TEXT":
        HexagonInnerText()
    if shape == "HEXAGON OUTER TEXT":
        HexagonOuterText()
    else:
        print("")
        #BottomText()
    
    
    #sets 3D cursor to origin of tile
    location = obj.location
    bpy.context.scene.cursor.location = location
    curveObj.select_set(True)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    
    #Set tile as parent to path
    #curveObj.parent = obj
    #curveObj.matrix_parent_inverse = obj.matrix_world.inverted()
    
    #bpy.ops.object.select_all(action='DESELECT')
    if singleColorMode == 1:
        single_color_mode(curveObj,obj.name)
    
    

    #ZOOM TO OBJECT
    zoom_camera_to_selected(obj)
    
    bpy.ops.object.select_all(action='DESELECT')
    
    #EXPORT STL
    export_to_STL(curveObj,curveObj.name + ".stl")
    export_to_STL(obj,obj.name + ".stl")
    
    if shape == "HEXAGON INNER TEXT" or shape == "HEXAGON OUTER TEXT":
        tobj = bpy.data.objects.get(name + "_Text" )
        export_to_STL(tobj,tobj.name + ".stl")
    if shape == "HEXAGON OUTER TEXT":
        plobj = bpy.data.objects.get(name + "_Plate")
        export_to_STL(plobj,plobj.name + ".stl")
    
    
    end_time = time.time()
    duration = end_time - start_time
    
    bpy.context.scene.my_tool["o_time"] = "Skript ran for: " + f"Script ran for {duration:.0f} seconds"
    
    #API Counter updaten
    count_openTopoData, last_date_openTopoData, count_openElevation, last_date_openElevation  = load_counter()
    if count_openTopoData < 1000:
        bpy.context.scene.my_tool["o_apiCounter_OpenTopoData"] = f"API Limit: {count_openTopoData:.0f}/1000 daily"
    else:
        bpy.context.scene.my_tool["o_apiCounter_OpenTopoData"] = f"API Limit: {count_openTopoData:.0f}/1000 (daily limit reached. might cause problems)"
    
    if count_openElevation < 1000:
        bpy.context.scene.my_tool["o_apiCounter_OpenElevation"] = f"API Limit: {count_openElevation:.0f}/1000 Monthly"
    else:
        bpy.context.scene.my_tool["o_apiCounter_OpenElevation"] = f"API Limit: {count_openElevation:.0f}/1000 (Monthly limit reached. might cause problems)"
        
    
        
    print(f"Finished")

    toggle_console()