#!/usr/bin/env python3
"""
Debug GPX parsing
"""
import xml.etree.ElementTree as ET

def test_gpx_parse():
    """Test GPX parsing directly"""
    try:
        with open('sample_trail.gpx', 'r') as f:
            content = f.read()
            print(f"File content length: {len(content)}")
            print("First 200 chars:")
            print(content[:200])
            print("\nLast 200 chars:")
            print(content[-200:])
        
        # Try parsing
        tree = ET.parse('sample_trail.gpx')
        root = tree.getroot()
        print(f"\nRoot tag: {root.tag}")
        print(f"Root attributes: {root.attrib}")
        
        # Find track points
        tracks = root.findall('.//trkpt')
        print(f"Found {len(tracks)} track points (no namespace)")
        
        # Try with namespace
        tracks_ns = root.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')
        print(f"Found {len(tracks_ns)} track points (with namespace)")
        
        tracks = tracks_ns if tracks_ns else tracks
        
        if tracks:
            first_point = tracks[0]
            print(f"First point: lat={first_point.get('lat')}, lon={first_point.get('lon')}")
            ele_elem = first_point.find('ele')
            if ele_elem is not None:
                print(f"First point elevation: {ele_elem.text}")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_gpx_parse()
