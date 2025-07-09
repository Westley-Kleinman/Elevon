# TrailPrint3D Blender Addon Setup Guide

## Overview

The TrailPrint3D Blender addon creates 3D printable trail maps from GPX files. This is separate from your website's GPX preview system - this addon is for actually generating STL files for 3D printing.

## Installation Steps

### 1. Install Python Dependencies

Run the setup script to install required packages:

```bash
python setup_blender_addon.py
```

If the automatic setup fails, manually install in Blender:

1. Open Blender
2. Go to Scripting workspace
3. Run this code in the console:

```python
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
```

### 2. Install the Addon

**Option A: Manual Installation**
1. Copy `trailprint3d-1-90.py` to Blender's addons folder:
   - Windows: `%APPDATA%\Blender Foundation\Blender\4.4\scripts\addons\`
   - Create the folders if they don't exist

**Option B: Install via Blender**
1. Open Blender
2. Go to `Edit > Preferences > Add-ons`
3. Click `Install...`
4. Navigate to and select `trailprint3d-1-90.py`
5. Enable the addon by checking the box next to "TrailPrint3D"

### 3. Access the Addon

1. Press `N` in the 3D viewport to show the sidebar
2. Look for the "TrailPrint3D" tab
3. You should see the addon interface with options for:
   - File Path (select your GPX file)
   - Export Path (where to save STL files)
   - Trail Name
   - Shape options (Hexagon, Square, Heart)
   - Size and resolution settings

## Usage

### Basic Workflow

1. **Prepare GPX File**: Use a GPX file from your GPS device or app
2. **Set Parameters**:
   - File Path: Select your GPX file
   - Export Path: Choose where to save STL files
   - Trail Name: Give your trail a name
   - Object Size: Set size in mm (default 100mm)
   - Shape: Choose Hexagon, Square, or Heart

3. **Generate**: Click "Generate" to create the 3D model
4. **Export**: Click "Export STL" to save files for 3D printing

### Advanced Features

- **Elevation API**: Uses OpenTopoData or Open-Elevation for terrain data
- **Text Integration**: Add trail statistics to the model
- **Multiple Shapes**: Hexagon, square, heart shapes available
- **Resolution Control**: Adjust detail level for terrain mesh
- **Path Customization**: Control trail thickness and elevation scaling

## Integration with Your Website

This Blender addon is **separate** from your website's GPX upload feature:

- **Website**: Shows 3D preview in browser (Three.js)
- **Blender Addon**: Creates actual 3D printable files (STL)

You could potentially offer this as a service:
1. Customers upload GPX files on your website
2. They see the 3D preview
3. You use this Blender addon to generate actual 3D printable files
4. Ship physical 3D printed trail maps

## Troubleshooting

### Common Issues

1. **"requests" module not found**
   - Run the setup script or manually install requests in Blender's Python

2. **API rate limits**
   - The addon has built-in rate limiting for elevation APIs
   - Free tiers: OpenTopoData (1000/day), Open-Elevation (1000/month)

3. **Large GPX files are slow**
   - Reduce resolution setting
   - Use smaller GPX files or simplify tracks

4. **Addon not showing**
   - Make sure it's enabled in Preferences > Add-ons
   - Press 'N' to show the sidebar
   - Look for "TrailPrint3D" tab

## Files

- `trailprint3d-1-90.py` - The main Blender addon
- `setup_blender_addon.py` - Dependency installer
- Your GPX files - Trail data to process

## Next Steps

1. Install the addon using the steps above
2. Test with the `sample_trail.gpx` file from your website
3. Experiment with different shapes and settings
4. Consider how to integrate this into your business workflow
