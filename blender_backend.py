#!/usr/bin/env python3
"""
Flask backend for Elevon GPX preview generation using Blender
Integrates with the existing website to provide high-quality 3D previews
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import tempfile
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
import math
from datetime import datetime
import json

from blender_gpx_preview import BlenderGPXPreview

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
PREVIEW_FOLDER = 'previews'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PREVIEW_FOLDER, exist_ok=True)

# Initialize Blender preview generator
try:
    blender_generator = BlenderGPXPreview()
    print(f"✅ Blender found at: {blender_generator.blender_executable}")
except Exception as e:
    print(f"❌ Blender not found: {e}")
    blender_generator = None

def parse_gpx_stats(gpx_file):
    """Parse GPX file and extract basic statistics"""
    try:
        tree = ET.parse(gpx_file)
        root = tree.getroot()
        
        # Handle different GPX namespaces
        ns_11 = {'default': 'http://www.topografix.com/GPX/1/1'}
        ns_10 = {'default': 'http://www.topografix.com/GPX/1/0'}
        
        coordinates = []
        
        # Try track points first with GPX 1.1 namespace
        points = root.findall('.//default:trkpt', ns_11)
        if not points:
            # Try with GPX 1.0 namespace
            points = root.findall('.//default:trkpt', ns_10)
        if not points:
            # Try route points with GPX 1.1 namespace
            points = root.findall('.//default:rtept', ns_11)
        if not points:
            # Try route points with GPX 1.0 namespace
            points = root.findall('.//default:rtept', ns_10)
        
        if not points:
            # Try without namespace prefix but with full namespaces
            points = root.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')
            if not points:
                points = root.findall('.//{http://www.topografix.com/GPX/1/0}trkpt')
            if not points:
                points = root.findall('.//{http://www.topografix.com/GPX/1/1}rtept')
            if not points:
                points = root.findall('.//{http://www.topografix.com/GPX/1/0}rtept')
        
        if not points:
            # Try completely without namespace
            points = root.findall('.//trkpt')
            if not points:
                points = root.findall('.//rtept')
        
        print(f"Found {len(points)} points in GPX file")
        
        if len(points) == 0:
            return {'error': 'No track points or route points found in GPX file'}
        
        for i, pt in enumerate(points):
            try:
                lat = float(pt.get('lat'))
                lon = float(pt.get('lon'))
                
                # Get elevation if available - try multiple namespaces
                ele_elem = pt.find('ele')
                if ele_elem is None:
                    ele_elem = pt.find('default:ele', ns_11)
                if ele_elem is None:
                    ele_elem = pt.find('default:ele', ns_10)
                if ele_elem is None:
                    ele_elem = pt.find('{http://www.topografix.com/GPX/1/1}ele')
                if ele_elem is None:
                    ele_elem = pt.find('{http://www.topografix.com/GPX/1/0}ele')
                ele = float(ele_elem.text) if ele_elem is not None else 0
                
                # Get timestamp if available - try multiple namespaces
                time_elem = pt.find('time')
                if time_elem is None:
                    time_elem = pt.find('default:time', ns_11)
                if time_elem is None:
                    time_elem = pt.find('default:time', ns_10)
                if time_elem is None:
                    time_elem = pt.find('{http://www.topografix.com/GPX/1/1}time')
                if time_elem is None:
                    time_elem = pt.find('{http://www.topografix.com/GPX/1/0}time')
                timestamp = time_elem.text if time_elem is not None else None
                
                coordinates.append((lat, lon, ele, timestamp))
                
            except ValueError as ve:
                print(f"Error parsing point {i+1}: {ve}")
                # Continue processing other points, but note the error
                continue
            except Exception as pe:
                print(f"Unexpected error parsing point {i+1}: {pe}")
                continue
        
        if not coordinates:
            return {'error': f'Found {len(points)} points but could not parse any valid coordinates (invalid lat/lon values)'}
        
        # Calculate statistics
        stats = calculate_trail_stats(coordinates)
        return stats
        
    except ET.ParseError as pe:
        print(f"XML parsing error: {pe}")
        return {'error': f'Invalid GPX file: XML parsing error - {str(pe)}'}
    except Exception as e:
        print(f"Error parsing GPX: {e}")
        return {'error': f'GPX parsing failed: {str(e)}'}

def calculate_trail_stats(coordinates):
    """Calculate trail statistics from coordinates"""
    if len(coordinates) < 2:
        return None
    
    total_distance = 0
    total_elevation_gain = 0
    elevations = [coord[2] for coord in coordinates]
    
    # Calculate distance and elevation gain
    for i in range(1, len(coordinates)):
        # Distance using Haversine formula
        lat1, lon1, ele1, _ = coordinates[i-1]
        lat2, lon2, ele2, _ = coordinates[i]
        
        # Haversine distance
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        total_distance += distance
        
        # Elevation gain (only uphill)
        if ele2 > ele1:
            total_elevation_gain += ele2 - ele1
    
    # Calculate time duration if timestamps available
    duration = None
    if coordinates[0][3] and coordinates[-1][3]:
        try:
            start_time = datetime.fromisoformat(coordinates[0][3].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(coordinates[-1][3].replace('Z', '+00:00'))
            duration = (end_time - start_time).total_seconds() / 3600  # hours
        except:
            pass
    
    return {
        'distance_km': round(total_distance, 2),
        'elevation_gain_m': round(total_elevation_gain, 1),
        'min_elevation_m': round(min(elevations), 1),
        'max_elevation_m': round(max(elevations), 1),
        'points_count': len(coordinates),
        'duration_hours': round(duration, 1) if duration else None
    }

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'blender_available': blender_generator is not None,
        'blender_path': blender_generator.blender_executable if blender_generator else None
    })

@app.route('/api/upload-gpx', methods=['POST'])
def upload_gpx():
    """Upload GPX file and generate preview"""
    
    if 'gpx' not in request.files:
        return jsonify({'error': 'No GPX file provided'}), 400
    
    file = request.files['gpx']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.gpx'):
        return jsonify({'error': 'File must be a GPX file'}), 400
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        gpx_filename = f"{file_id}.gpx"
        gpx_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, gpx_filename))
        
        # Save uploaded file
        file.save(gpx_path)
        
        # Check if file was actually saved and has content
        file_size = os.path.getsize(gpx_path) if os.path.exists(gpx_path) else 0
        print(f"📁 Saved GPX file: {gpx_path} ({file_size} bytes)")
        
        if file_size == 0:
            print(f"❌ Uploaded file is empty")
            return jsonify({'error': 'Uploaded file is empty'}), 400
        
        # Parse GPX for basic stats
        print(f"🔍 Parsing GPX file...")
        try:
            stats = parse_gpx_stats(gpx_path)
            print(f"📊 Parsing result: {stats}")
        except Exception as parse_error:
            print(f"❌ GPX parsing exception: {parse_error}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'GPX parsing failed: {str(parse_error)}'}), 400
        
        # Check if parsing returned an error
        if isinstance(stats, dict) and 'error' in stats:
            print(f"❌ GPX parsing error: {stats['error']}")
            return jsonify({'error': stats['error']}), 400
        
        if not stats:
            print(f"❌ GPX parsing returned None - unexpected error")
            return jsonify({'error': 'Unexpected GPX parsing error'}), 400
        
        response_data = {
            'file_id': file_id,
            'filename': file.filename,
            'stats': stats,
            'preview_available': blender_generator is not None
        }
        
        # Generate Blender preview if available
        if blender_generator:
            try:
                preview_filename = f"{file_id}_preview.png"
                preview_path = os.path.abspath(os.path.join(PREVIEW_FOLDER, preview_filename))
                
                # Get render settings from request
                settings = {
                    'width': int(request.form.get('width', 1920)),
                    'height': int(request.form.get('height', 1080)),
                    'samples': int(request.form.get('samples', 32)),  # Lower for faster preview
                    'trail_thickness': float(request.form.get('trail_thickness', 0.3)),
                    'elevation_scale': float(request.form.get('elevation_scale', 0.001)),
                }
                
                print(f"Generating Blender preview for {gpx_filename}...")
                print(f"GPX path: {gpx_path}")
                print(f"Preview path: {preview_path}")
                print(f"Settings: {settings}")
                
                result = blender_generator.generate_preview(gpx_path, preview_path, settings)
                print(f"Blender result: {result}")
                
                if result['success']:
                    response_data['preview_url'] = f"/api/preview/{file_id}"
                    response_data['blender_output'] = result.get('stdout', '')
                    print(f"✅ Preview generated: {preview_path}")
                    print(f"Preview file exists: {os.path.exists(preview_path)}")
                    if os.path.exists(preview_path):
                        print(f"Preview file size: {os.path.getsize(preview_path)} bytes")
                else:
                    response_data['preview_error'] = "Failed to generate Blender preview"
                    print(f"❌ Preview generation failed")
                    
            except Exception as e:
                print(f"❌ Error generating preview: {e}")
                response_data['preview_error'] = str(e)
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error processing upload: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview/<file_id>')
def get_preview(file_id):
    """Serve generated preview image"""
    preview_filename = f"{file_id}_preview.png"
    preview_path = os.path.abspath(os.path.join(PREVIEW_FOLDER, preview_filename))
    
    if not os.path.exists(preview_path):
        return jsonify({'error': 'Preview not found'}), 404
    
    return send_file(preview_path, mimetype='image/png')

@app.route('/api/regenerate-preview/<file_id>', methods=['POST'])
def regenerate_preview(file_id):
    """Regenerate preview with different settings"""
    
    if not blender_generator:
        return jsonify({'error': 'Blender not available'}), 503
    
    gpx_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, f"{file_id}.gpx"))
    if not os.path.exists(gpx_path):
        return jsonify({'error': 'GPX file not found'}), 404
    
    try:
        # Get settings from request
        data = request.get_json() or {}
        settings = {
            'width': int(data.get('width', 1920)),
            'height': int(data.get('height', 1080)),
            'samples': int(data.get('samples', 64)),
            'trail_thickness': float(data.get('trail_thickness', 0.3)),
            'elevation_scale': float(data.get('elevation_scale', 0.001)),
            'trail_color': data.get('trail_color', [0.9, 0.3, 0.1, 1.0]),
            'base_color': data.get('base_color', [0.4, 0.3, 0.2, 1.0]),
        }
        
        preview_filename = f"{file_id}_preview.png"
        preview_path = os.path.abspath(os.path.join(PREVIEW_FOLDER, preview_filename))
        
        print(f"Regenerating preview with settings: {settings}")
        result = blender_generator.generate_preview(gpx_path, preview_path, settings)
        
        if result['success']:
            return jsonify({
                'success': True,
                'preview_url': f"/api/preview/{file_id}",
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to regenerate preview'}), 500
            
    except Exception as e:
        print(f"Error regenerating preview: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup/<file_id>', methods=['DELETE'])
def cleanup_files(file_id):
    """Clean up uploaded files and previews"""
    try:
        gpx_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, f"{file_id}.gpx"))
        preview_path = os.path.abspath(os.path.join(PREVIEW_FOLDER, f"{file_id}_preview.png"))
        
        files_removed = []
        if os.path.exists(gpx_path):
            os.remove(gpx_path)
            files_removed.append('gpx')
        
        if os.path.exists(preview_path):
            os.remove(preview_path)
            files_removed.append('preview')
        
        return jsonify({
            'success': True,
            'files_removed': files_removed
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Elevon GPX Preview Server...")
    print(f"📁 Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"🖼️  Preview folder: {os.path.abspath(PREVIEW_FOLDER)}")
    
    if blender_generator:
        print(f"🎨 Blender integration: ENABLED ({blender_generator.blender_executable})")
    else:
        print("🎨 Blender integration: DISABLED (Blender not found)")
    
    app.run(debug=True, port=5000)
