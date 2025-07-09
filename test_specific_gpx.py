#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blender_backend import parse_gpx_stats

def test_specific_gpx():
    """Test parsing a specific uploaded GPX file"""
    gpx_file = r"c:\Elevon\uploads\fd49c81b-3abf-405a-8f6e-66c8e42549dd.gpx"
    
    print(f"🔍 Testing GPX file: {gpx_file}")
    print(f"📁 File exists: {os.path.exists(gpx_file)}")
    
    if os.path.exists(gpx_file):
        file_size = os.path.getsize(gpx_file)
        print(f"📏 File size: {file_size} bytes")
        
        try:
            # Test our parsing function
            stats = parse_gpx_stats(gpx_file)
            print(f"✅ Parsing successful!")
            print(f"📊 Stats: {stats}")
        except Exception as e:
            print(f"❌ Parsing failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ File not found")

if __name__ == "__main__":
    test_specific_gpx()
