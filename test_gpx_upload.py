#!/usr/bin/env python3
"""
Test script for GPX upload functionality
This script helps you test the GPX upload feature locally
"""

import os
import sys
import subprocess
import webbrowser
import time

def main():
    print("🏔️  Elevon GPX Upload Test Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('image-filter-web/app.py'):
        print("❌ Error: Please run this script from the Elevon root directory")
        print("   Current directory:", os.getcwd())
        sys.exit(1)
    
    print("✅ Found Flask app")
    
    # Check Python dependencies
    print("\n📦 Checking dependencies...")
    try:
        import flask
        import PIL
        import numpy
        print("✅ Flask, PIL, and numpy are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r image-filter-web/requirements.txt")
        sys.exit(1)
    
    # Check if sample GPX file exists
    sample_gpx_path = "sample_trail.gpx"
    if not os.path.exists(sample_gpx_path):
        print(f"\n📁 Creating sample GPX file: {sample_gpx_path}")
        create_sample_gpx(sample_gpx_path)
        print("✅ Sample GPX file created")
    else:
        print("✅ Sample GPX file found")
    
    print("\n🚀 Starting Flask server...")
    print("   The server will start on http://localhost:5000")
    print("   Your Elevon website will be available at http://localhost:5000/elevon")
    print("   Press Ctrl+C to stop the server")
    print("\n" + "=" * 50)
    
    # Start the Flask app
    try:
        os.chdir('image-filter-web')
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://localhost:5000/elevon')
        
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Start Flask
        subprocess.run([sys.executable, 'app.py'], check=True)
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Thanks for testing!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

def create_sample_gpx(filename):
    """Create a sample GPX file for testing"""
    gpx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Elevon Test">
  <trk>
    <name>Sample Mountain Trail</name>
    <trkseg>
      <trkpt lat="35.7796" lon="-78.6382">
        <ele>100</ele>
      </trkpt>
      <trkpt lat="35.7806" lon="-78.6392">
        <ele>110</ele>
      </trkpt>
      <trkpt lat="35.7816" lon="-78.6402">
        <ele>125</ele>
      </trkpt>
      <trkpt lat="35.7826" lon="-78.6412">
        <ele>140</ele>
      </trkpt>
      <trkpt lat="35.7836" lon="-78.6422">
        <ele>160</ele>
      </trkpt>
      <trkpt lat="35.7846" lon="-78.6432">
        <ele>180</ele>
      </trkpt>
      <trkpt lat="35.7856" lon="-78.6442">
        <ele>200</ele>
      </trkpt>
      <trkpt lat="35.7866" lon="-78.6452">
        <ele>220</ele>
      </trkpt>
      <trkpt lat="35.7876" lon="-78.6462">
        <ele>245</ele>
      </trkpt>
      <trkpt lat="35.7886" lon="-78.6472">
        <ele>270</ele>
      </trkpt>
      <trkpt lat="35.7896" lon="-78.6482">
        <ele>290</ele>
      </trkpt>
      <trkpt lat="35.7906" lon="-78.6492">
        <ele>315</ele>
      </trkpt>
      <trkpt lat="35.7916" lon="-78.6502">
        <ele>340</ele>
      </trkpt>
      <trkpt lat="35.7926" lon="-78.6512">
        <ele>360</ele>
      </trkpt>
      <trkpt lat="35.7936" lon="-78.6522">
        <ele>380</ele>
      </trkpt>
      <trkpt lat="35.7946" lon="-78.6532">
        <ele>400</ele>
      </trkpt>
      <trkpt lat="35.7956" lon="-78.6542">
        <ele>420</ele>
      </trkpt>
      <trkpt lat="35.7966" lon="-78.6552">
        <ele>440</ele>
      </trkpt>
      <trkpt lat="35.7976" lon="-78.6562">
        <ele>460</ele>
      </trkpt>
      <trkpt lat="35.7986" lon="-78.6572">
        <ele>480</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>'''
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(gpx_content)

if __name__ == '__main__':
    main()
