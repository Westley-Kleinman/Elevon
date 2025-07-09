import tempfile
import os
from blender_gpx_preview import BlenderGPXPreview

def debug_purple_screen():
    print("🔍 DEBUGGING PURPLE SCREEN ISSUE")
    print("=" * 50)
    
    # Create a super simple GPX with just 3 points in a line
    simple_gpx = """<?xml version='1.0' encoding='UTF-8'?>
<gpx version='1.1' creator='Debug' xmlns='http://www.topografix.com/GPX/1/1'>
  <trk>
    <name>Debug Trail</name>
    <trkseg>
      <trkpt lat='0.000' lon='0.000'>
        <ele>0</ele>
      </trkpt>
      <trkpt lat='0.001' lon='0.000'>
        <ele>10</ele>
      </trkpt>
      <trkpt lat='0.002' lon='0.000'>
        <ele>0</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as f:
        f.write(simple_gpx)
        gpx_file = f.name
    
    try:
        output_file = "c:/Elevon/debug_purple.png"
        
        # Extreme settings to ensure visibility
        settings = {
            'width': 800,
            'height': 600,
            'samples': 4,  # Low for speed
            'trail_thickness': 50.0,  # MASSIVE thickness
            'elevation_scale': 10.0,   # Huge elevation
            'trail_color': [1.0, 0.0, 0.0, 1.0],  # Pure red
            'base_color': [0.0, 1.0, 0.0, 1.0],   # Pure green
            'base_size': 10  # Small base
        }
        
        print(f"📁 GPX: Simple 3-point trail")
        print(f"🖼️  Output: {output_file}")
        print(f"⚙️  Settings: Massive trail thickness, huge elevation")
        
        blender_preview = BlenderGPXPreview()
        result = blender_preview.generate_preview(gpx_file, output_file, settings)
        
        print(f"\n🔍 Result: {result.get('success', False)}")
        
        if result.get('success'):
            file_size = os.path.getsize(output_file)
            print(f"📦 File size: {file_size:,} bytes")
            
            # Copy to website
            import shutil
            shutil.copy(output_file, "Website/debug_purple.png")
            print(f"🌐 View: http://localhost:8000/debug_purple.png")
            
            # Extract key info from stdout
            stdout = result.get('stdout', '')
            print(f"\n📊 Key Info from Blender:")
            for line in stdout.split('\n'):
                if any(keyword in line for keyword in ['Camera positioned', 'Trail center', 'Trail span', 'coordinates', 'Trail created']):
                    print(f"   {line.strip()}")
        else:
            print(f"❌ Failed: {result.get('error')}")
            
    finally:
        os.unlink(gpx_file)

if __name__ == "__main__":
    debug_purple_screen()
