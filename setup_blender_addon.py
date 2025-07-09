#!/usr/bin/env python3
"""
Setup script for TrailPrint3D Blender addon dependencies
This script installs the required Python packages for the Blender addon
"""

import subprocess
import sys
import os

def install_blender_dependencies():
    """Install required packages for the TrailPrint3D Blender addon"""
    
    # Get Blender's Python executable path
    # This varies by OS and Blender version
    blender_python_paths = [
        # Windows paths
        r"C:\Program Files\Blender Foundation\Blender 4.4\4.4\python\bin\python.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.3\4.3\python\bin\python.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.2\4.2\python\bin\python.exe",
        # Add Steam version path
        os.path.expanduser(r"~\AppData\Local\Steam\steamapps\common\Blender\4.4\python\bin\python.exe"),
        # Add other common paths
        r"C:\Users\{}\AppData\Roaming\Blender Foundation\Blender\4.4\python\bin\python.exe".format(os.getenv('USERNAME', '')),
    ]
    
    blender_python = None
    for path in blender_python_paths:
        if os.path.exists(path):
            blender_python = path
            break
    
    if not blender_python:
        print("❌ Could not find Blender's Python executable.")
        print("Please manually install the following packages in Blender's Python:")
        print("- requests")
        print("- xml (usually included)")
        print("- mathutils (Blender built-in)")
        print("\nTo install manually:")
        print("1. Open Blender")
        print("2. Go to Scripting workspace")
        print("3. Run this code:")
        print("""
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
""")
        return False
    
    print(f"✅ Found Blender Python at: {blender_python}")
    
    # Required packages for the TrailPrint3D addon
    packages = [
        "requests",  # For API calls to elevation services
    ]
    
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([blender_python, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    print("\n🎉 All dependencies installed successfully!")
    print("\nNext steps:")
    print("1. Copy trailprint3d-1-90.py to your Blender addons folder, or")
    print("2. Install it via Blender > Edit > Preferences > Add-ons > Install...")
    print("3. Enable the 'TrailPrint3D' addon")
    print("4. Press 'N' in the 3D viewport to access the addon panel")
    
    return True

if __name__ == "__main__":
    print("🔧 Setting up TrailPrint3D Blender addon dependencies...")
    install_blender_dependencies()
