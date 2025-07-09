#!/usr/bin/env python3
"""
Test script for GPX upload functionality
"""
import requests
import json

def test_gpx_upload():
    """Test the GPX upload endpoint"""
    print("Testing GPX upload functionality...")
    
    # Check if Flask backend is running
    try:
        response = requests.get('http://localhost:5000/')
        print("✅ Flask backend is running")
    except requests.exceptions.ConnectionError:
        print("❌ Flask backend is not running")
        return False
    
    # Test GPX upload with sample file
    try:
        with open('sample_trail.gpx', 'rb') as f:
            files = {'gpx_file': f}
            response = requests.post('http://localhost:5000/upload_gpx', files=files)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ GPX upload successful!")
                preview_data = data.get('preview_data', {})
                stats = preview_data.get('stats', {})
                points = preview_data.get('points', [])
                
                print(f"   - Points: {len(points)}")
                distance = stats.get('distance_km')
                elevation = stats.get('elevation_gain')
                total_points = stats.get('total_points')
                
                if distance is not None:
                    print(f"   - Distance: {distance:.2f} km")
                if elevation is not None:
                    print(f"   - Elevation: {elevation:.0f} m")
                if total_points is not None:
                    print(f"   - Total Points: {total_points}")
                
                return True
            else:
                print(f"❌ GPX upload failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing GPX upload: {str(e)}")
        return False

def test_demo_mode():
    """Test if the frontend demo mode works"""
    print("\nTesting demo mode...")
    
    try:
        response = requests.get('http://localhost:8080/')
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            
            # Check if demo mode is enabled
            if 'DEMO_MODE = true' in response.text:
                print("✅ Demo mode is enabled")
                return True
            else:
                print("⚠️  Demo mode setting not found (may be disabled)")
                return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing frontend: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Elevon GPX Upload System\n")
    
    backend_test = test_gpx_upload()
    frontend_test = test_demo_mode()
    
    print(f"\n📊 Test Results:")
    print(f"   Backend GPX Upload: {'✅ PASS' if backend_test else '❌ FAIL'}")
    print(f"   Frontend Access: {'✅ PASS' if frontend_test else '❌ FAIL'}")
    
    if backend_test and frontend_test:
        print("\n🎉 All tests passed! GPX upload should work correctly.")
        print("\nTo test manually:")
        print("1. Open http://localhost:8080 in your browser")
        print("2. Scroll down to the '3D Preview' section")
        print("3. Upload the sample_trail.gpx file")
        print("4. You should see trail statistics and a 3D preview")
    else:
        print("\n⚠️  Some tests failed. Check the setup.")
