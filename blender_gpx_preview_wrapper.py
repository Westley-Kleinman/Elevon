#!/usr/bin/env python3
"""
Blender GPX Preview Generator - Backend Wrapper
Provides Python interface to the Blender GPX preview script
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
        # Try common Blender installation paths
        possible_paths = [
            "C:\\Program Files\\Blender Foundation\\Blender 4.4\\blender.exe",
            "C:\\Program Files\\Blender Foundation\\Blender 4.3\\blender.exe", 
            "C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe",
            "C:\\Program Files\\Blender Foundation\\Blender 4.1\\blender.exe",
            "C:\\Program Files\\Blender Foundation\\Blender 4.0\\blender.exe",
            "/usr/bin/blender",
            "/usr/local/bin/blender",
            "/Applications/Blender.app/Contents/MacOS/Blender"
        ]
        
        for path in possible_paths:
            if os.path.isfile(path):
                return path
        
        # Try to find in PATH
        import shutil
        blender_path = shutil.which("blender")
        if blender_path:
            return blender_path
        
        raise FileNotFoundError("Blender executable not found")
    
    def is_available(self):
        """Check if Blender is available"""
        try:
            return os.path.isfile(self.blender_executable)
        except:
            return False
    
    def generate_preview(self, gpx_file, output_image, settings=None):
        """Generate a preview image from a GPX file using Blender"""
        if not os.path.exists(gpx_file):
            raise FileNotFoundError(f"GPX file not found: {gpx_file}")
        
        # Use the fixed Blender script
        script_path = os.path.join(os.path.dirname(__file__), "blender_gpx_preview.py")
        
        try:
            # Run Blender in background mode
            cmd = [
                self.blender_executable,
                '--background',
                '--python', script_path,
                '--', gpx_file, output_image
            ]
            
            print(f"Running Blender command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            print(f"Blender exit code: {result.returncode}")
            if result.stdout:
                print(f"Blender stdout: {result.stdout}")
            if result.stderr:
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
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': "Blender execution timed out (5 minutes)",
                'stdout': '',
                'stderr': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to run Blender: {str(e)}",
                'stdout': '',
                'stderr': ''
            }

def main():
    """CLI interface for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate GPX preview using Blender')
    parser.add_argument('gpx_file', help='Path to GPX file')
    parser.add_argument('output_image', help='Output image path')
    parser.add_argument('--blender', help='Path to Blender executable')
    
    args = parser.parse_args()
    
    # Create preview generator
    blender_exe = args.blender if args.blender else None
    generator = BlenderGPXPreview(blender_exe)
    
    if not generator.is_available():
        print(f"Error: Blender not found at {generator.blender_executable}")
        return 1
    
    print(f"Using Blender: {generator.blender_executable}")
    
    # Generate preview
    result = generator.generate_preview(args.gpx_file, args.output_image)
    
    if result['success']:
        print(f"Preview generated successfully: {result['output_file']}")
        return 0
    else:
        print(f"Error generating preview: {result['error']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
