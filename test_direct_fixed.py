#!/usr/bin/env python3

import sys
import os

# Add the current directory to the path for imports
sys.path.insert(0, 'c:/Elevon')

# Test the fixed materials directly with Blender
output_path = "c:\\Elevon\\test_direct_fixed.png"
gpx_file = "c:\\Elevon\\user_stage1.gpx"

print(f"Testing direct Blender rendering with fixed materials...")
print(f"GPX file: {gpx_file}")
print(f"Output: {output_path}")

# Prepare the command
blender_cmd = f'& "C:\\Program Files\\Blender Foundation\\Blender 4.4\\blender.exe" --background --python c:\\Elevon\\blender_gpx_preview.py -- "{gpx_file}" "{output_path}"'

print(f"Running: {blender_cmd}")
