#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from blender_backend import parse_gpx_stats

def test_recent_gpx():
    """Test parsing the most recent uploaded GPX file"""
    gpx_file = r"c:\Elevon\uploads\e509ad45-9c9f-4546-bb3b-58e94ac326a8.gpx"
    
    print(f"🔍 Testing GPX file: {gpx_file}")
    print(f"📁 File exists: {os.path.exists(gpx_file)}")
    
    if os.path.exists(gpx_file):
        file_size = os.path.getsize(gpx_file)
        print(f"📏 File size: {file_size} bytes")
        
        # Read and show first few lines
        with open(gpx_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:10]
            print("📄 First 10 lines:")
            for i, line in enumerate(lines, 1):
                print(f"  {i:2}: {line.rstrip()}")
        
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
    test_recent_gpx()
