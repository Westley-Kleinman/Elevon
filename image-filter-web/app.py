from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
import numpy as np
import io
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import math
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable Flask static file caching
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'gpx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_gpx(gpx_file):
    """Parse GPX file and extract track points with elevation data"""
    try:
        tree = ET.parse(gpx_file)
        root = tree.getroot()
        
        # Handle different GPX namespaces
        namespaces = {
            'gpx': 'http://www.topografix.com/GPX/1/1',
            'gpx10': 'http://www.topografix.com/GPX/1/0'
        }
        
        points = []
        
        # Try to find track points with namespaces
        for ns_prefix, ns_uri in namespaces.items():
            tracks = root.findall(f'.//{{{ns_uri}}}trkpt')
            if tracks:
                for trkpt in tracks:
                    lat = float(trkpt.get('lat'))
                    lon = float(trkpt.get('lon'))
                    
                    # Try to get elevation
                    ele_elem = trkpt.find(f'{{{ns_uri}}}ele')
                    ele = float(ele_elem.text) if ele_elem is not None else 0
                    
                    points.append({'lat': lat, 'lon': lon, 'ele': ele})
                break
        
        # If no namespaced track points found, try without namespace
        if not points:
            tracks = root.findall('.//trkpt')
            if tracks:
                for trkpt in tracks:
                    lat = float(trkpt.get('lat'))
                    lon = float(trkpt.get('lon'))
                    
                    # Try to get elevation
                    ele_elem = trkpt.find('ele')
                    ele = float(ele_elem.text) if ele_elem is not None else 0
                    
                    points.append({'lat': lat, 'lon': lon, 'ele': ele})
        
        # Try waypoints if no track points found
        if not points:
            for ns_prefix, ns_uri in namespaces.items():
                waypoints = root.findall(f'.//{{{ns_uri}}}wpt')
                if waypoints:
                    for wpt in waypoints:
                        lat = float(wpt.get('lat'))
                        lon = float(wpt.get('lon'))
                        
                        ele_elem = wpt.find(f'{{{ns_uri}}}ele')
                        ele = float(ele_elem.text) if ele_elem is not None else 0
                        
                        points.append({'lat': lat, 'lon': lon, 'ele': ele})
                    break
            
            # Try waypoints without namespace
            if not points:
                waypoints = root.findall('.//wpt')
                if waypoints:
                    for wpt in waypoints:
                        lat = float(wpt.get('lat'))
                        lon = float(wpt.get('lon'))
                        
                        ele_elem = wpt.find('ele')
                        ele = float(ele_elem.text) if ele_elem is not None else 0
                        
                        points.append({'lat': lat, 'lon': lon, 'ele': ele})
        
        return points
    except Exception as e:
        print(f"Error parsing GPX: {str(e)}")
        return []

def generate_preview_data(points):
    """Generate simplified 3D preview data from GPS points"""
    if not points:
        return None
    
    # Convert GPS coordinates to local coordinate system
    min_lat = min(p['lat'] for p in points)
    max_lat = max(p['lat'] for p in points)
    min_lon = min(p['lon'] for p in points)
    max_lon = max(p['lon'] for p in points)
    min_ele = min(p['ele'] for p in points)
    max_ele = max(p['ele'] for p in points)
    
    # Normalize coordinates
    preview_points = []
    for point in points:
        # Convert to normalized coordinates (0-1 range)
        x = (point['lon'] - min_lon) / (max_lon - min_lon) if max_lon != min_lon else 0.5
        y = (point['lat'] - min_lat) / (max_lat - min_lat) if max_lat != min_lat else 0.5
        z = (point['ele'] - min_ele) / (max_ele - min_ele) if max_ele != min_ele else 0.5
        
        preview_points.append([x, y, z])
    
    return {
        'points': preview_points,
        'bounds': {
            'lat': [min_lat, max_lat],
            'lon': [min_lon, max_lon], 
            'ele': [min_ele, max_ele]
        },
        'stats': {
            'total_points': len(points),
            'distance_km': calculate_distance(points),
            'elevation_gain': calculate_elevation_gain(points)
        }
    }

def calculate_distance(points):
    """Calculate total distance of the track in kilometers"""
    if len(points) < 2:
        return 0
    
    total_distance = 0
    for i in range(1, len(points)):
        lat1, lon1 = math.radians(points[i-1]['lat']), math.radians(points[i-1]['lon'])
        lat2, lon2 = math.radians(points[i]['lat']), math.radians(points[i]['lon'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Earth's radius in kilometers
        
        total_distance += c * r
    
    return round(total_distance, 2)

def calculate_elevation_gain(points):
    """Calculate total elevation gain in meters"""
    if len(points) < 2:
        return 0
    
    total_gain = 0
    for i in range(1, len(points)):
        elevation_diff = points[i]['ele'] - points[i-1]['ele']
        if elevation_diff > 0:
            total_gain += elevation_diff
    
# Color filter logic (vectorized, similar to your desktop app)
def filter_by_colors(image, color_tolerance_list):
    arr = np.array(image.convert('RGBA'))
    rgb_arr = arr[..., :3]
    mask = np.zeros(rgb_arr.shape[:2], dtype=bool)
    for color, tol in color_tolerance_list:
        color = np.array(color)
        dist = np.linalg.norm(rgb_arr - color, axis=2)
        mask |= dist <= tol
    out_img = np.ones(arr.shape, dtype=np.uint8) * 255
    out_img[mask, :3] = 0
    out_img[..., 3] = 255
    return Image.fromarray(out_img)

@app.route('/upload_gpx', methods=['POST'])
def upload_gpx():
    """Handle GPX file upload and return 3D preview data"""
    if 'gpx_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['gpx_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Reset file pointer to beginning
            file.stream.seek(0)
            
            # Parse the GPX file directly from memory
            points = parse_gpx(file.stream)
            
            print(f"Debug: Found {len(points)} points in GPX file")
            if points:
                print(f"Debug: Sample point: {points[0]}")
            
            if not points:
                return jsonify({'error': 'No valid track data found in GPX file'}), 400
            
            # Generate preview data
            preview_data = generate_preview_data(points)
            
            if not preview_data:
                return jsonify({'error': 'Failed to generate preview data'}), 500
            
            return jsonify({
                'success': True,
                'preview_data': preview_data,
                'filename': secure_filename(file.filename)
            })
            
        except Exception as e:
            print(f"Debug: Error processing GPX file: {str(e)}")
            return jsonify({'error': f'Failed to process GPX file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type. Please upload a .gpx file'}), 400

# Color filter logic (vectorized, similar to your desktop app)
def filter_by_colors(image, color_tolerance_list):
    arr = np.array(image.convert('RGBA'))
    rgb_arr = arr[..., :3]
    mask = np.zeros(rgb_arr.shape[:2], dtype=bool)
    for color, tol in color_tolerance_list:
        color = np.array(color)
        dist = np.linalg.norm(rgb_arr - color, axis=2)
        mask |= dist <= tol
    out_img = np.ones(arr.shape, dtype=np.uint8) * 255
    out_img[mask, :3] = 0
    out_img[..., 3] = 255
    return Image.fromarray(out_img)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return 'All processing is now done in your browser. No files are uploaded to the server.', 400
    return render_template('index.html')

@app.route('/elevon')
def elevon_website():
    """Serve the Elevon website"""
    return send_file('../Website/index.html')

@app.route('/elevon/<path:filename>')
def elevon_static(filename):
    """Serve static files for Elevon website"""
    return send_file(f'../Website/{filename}')

if __name__ == '__main__':
    app.run(debug=True)