#!/usr/bin/env python3
"""
Test script for Blender GPX preview generation
Tests the Blender integration with a sample GPX file
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blender_gpx_preview import BlenderGPXPreview

def test_blender_integration():
    """Test the Blender GPX preview generation"""
    
    print("🧪 Testing Blender GPX Preview Integration...")
    print("=" * 50)
    
    # Check if Blender is available
    try:
        generator = BlenderGPXPreview()
        print(f"✅ Blender found at: {generator.blender_executable}")
    except Exception as e:
        print(f"❌ Blender not found: {e}")
        print("\n💡 To fix this:")
        print("1. Install Blender 4.2+ from https://www.blender.org/download/")
        print("2. Or specify the path manually when creating BlenderGPXPreview(path)")
        return False
    
    # Check if sample GPX file exists
    sample_gpx = "sample_trail.gpx"
    if not os.path.exists(sample_gpx):
        print(f"❌ Sample GPX file not found: {sample_gpx}")
        return False
    
    print(f"✅ Sample GPX file found: {sample_gpx}")
    
    # Create output directory
    output_dir = "test_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Test preview generation
    output_file = os.path.join(output_dir, "test_preview.png")
    
    print(f"\n🎨 Generating preview...")
    print(f"📁 Input: {sample_gpx}")
    print(f"📁 Output: {output_file}")
    
    # Test settings
    settings = {
        'width': 1920,
        'height': 1080,
        'samples': 32,  # Lower for faster testing
        'trail_thickness': 0.3,
        'elevation_scale': 0.001
    }
    
    try:
        result = generator.generate_preview(sample_gpx, output_file, settings)
        
        print("=== Blender Output ===")
        print("STDOUT:", result.get('stdout', 'No stdout'))
        print("STDERR:", result.get('stderr', 'No stderr'))
        
        if result['success']:
            print("✅ Preview generated successfully!")
            print(f"📸 Output file: {os.path.abspath(output_file)}")
            
            # Check file size
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"📊 File size: {file_size / 1024:.1f} KB")
                
                if file_size > 1000:  # At least 1KB
                    print("✅ File appears to be valid")
                else:
                    print("⚠️  File seems too small - might be corrupted")
            
            return True
        else:
            print("❌ Preview generation failed")
            print(f"Error: {result.get('stderr', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        return False

def test_backend_dependencies():
    """Test Flask backend dependencies"""
    
    print("\n🔧 Testing Backend Dependencies...")
    print("=" * 50)
    
    try:
        import flask
        print(f"✅ Flask: {flask.__version__}")
    except ImportError:
        print("❌ Flask not installed")
        print("   Run: pip install flask")
        return False
    
    try:
        import flask_cors
        print(f"✅ Flask-CORS: Available")
    except ImportError:
        print("❌ Flask-CORS not installed") 
        print("   Run: pip install flask-cors")
        return False
    
    try:
        from blender_backend import app
        print("✅ Blender backend module loads correctly")
    except ImportError as e:
        print(f"❌ Blender backend import failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    
    print("🚀 Elevon Blender Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Backend dependencies
    deps_ok = test_backend_dependencies()
    
    # Test 2: Blender integration
    blender_ok = test_blender_integration()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    print(f"Backend Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"Blender Integration:  {'✅ PASS' if blender_ok else '❌ FAIL'}")
    
    if deps_ok and blender_ok:
        print("\n🎉 All tests passed! Your Blender integration is ready to use.")
        print("\n📝 Next steps:")
        print("1. Run: start_blender_backend.bat")
        print("2. Open your website")
        print("3. Upload a GPX file to test the integration")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        
        if not deps_ok:
            print("\n🔧 To fix backend issues:")
            print("   pip install flask flask-cors")
        
        if not blender_ok:
            print("\n🎨 To fix Blender issues:")
            print("   1. Install Blender 4.2+ from https://www.blender.org/")
            print("   2. Make sure Blender is in your PATH")
            print("   3. Or specify the Blender path manually")

if __name__ == "__main__":
    main()
