import tempfile
import os
from blender_gpx_preview import BlenderGPXPreview

def test_simple_trail():
    print("🧪 Testing simple 5-point trail with maximum visibility")
    print("=" * 60)
    
    # Create a simple GPX file with just 5 points in a clear pattern
    gpx_content = """<?xml version='1.0' encoding='UTF-8'?>
<gpx version='1.1' creator='Test' xmlns='http://www.topografix.com/GPX/1/1'>
  <trk>
    <name>Simple Test Trail</name>
    <trkseg>
      <trkpt lat='35.0000' lon='-78.0000'>
        <ele>100</ele>
      </trkpt>
      <trkpt lat='35.0010' lon='-78.0000'>
        <ele>110</ele>
      </trkpt>
      <trkpt lat='35.0020' lon='-78.0000'>
        <ele>120</ele>
      </trkpt>
      <trkpt lat='35.0030' lon='-78.0000'>
        <ele>110</ele>
      </trkpt>
      <trkpt lat='35.0040' lon='-78.0000'>
        <ele>100</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""
    
    # Write to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as f:
        f.write(gpx_content)
        gpx_file = f.name
    
    try:
        output_file = "c:/Elevon/test_simple_trail.png"
        
        # Use extremely visible settings
        settings = {
            'width': 800,
            'height': 600,
            'samples': 8,  # Lower for faster rendering
            'trail_thickness': 10.0,  # Very thick trail
            'elevation_scale': 1.0,   # Full elevation scale
            'trail_color': [1.0, 0.0, 0.0, 1.0],  # Bright red
            'base_color': [0.0, 1.0, 0.0, 1.0],   # Bright green
            'base_size': 20  # Smaller base for better proportions
        }
        
        print(f"📁 GPX file: {gpx_file}")
        print(f"🖼️  Output: {output_file}")
        print(f"⚙️  Settings: {settings}")
        
        blender_preview = BlenderGPXPreview()
        result = blender_preview.generate_preview(gpx_file, output_file, settings)
        
        print(f"🔍 Result: {result}")
        
        if result.get('success'):
            file_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
            print(f"✅ Rendering successful!")
            print(f"📦 Output file size: {file_size} bytes")
            
            # Copy to website for viewing
            import shutil
            web_file = "Website/simple_trail_test.png"
            shutil.copy(output_file, web_file)
            print(f"🌐 View at: http://localhost:8000/simple_trail_test.png")
        else:
            print(f"❌ Rendering failed: {result}")
            
    finally:
        # Clean up temp file
        if os.path.exists(gpx_file):
            os.unlink(gpx_file)

if __name__ == "__main__":
    test_simple_trail()
