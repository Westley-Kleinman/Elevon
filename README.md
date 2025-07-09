# Elevon - Custom 3D Trail Maps

## 🏔️ Overview

Elevon creates custom 3D-printed trail maps that turn your favorite routes into beautiful art pieces. This repository contains the complete website and GPX upload system with interactive 3D previews.

## 📁 Project Structure

```
Elevon/
├── Website/                 # Main website (HTML, CSS, JS)
│   ├── index.html          # Home page with GPX upload
│   ├── about.html          # About page
│   ├── order.html          # Order form
│   ├── style.css           # Main stylesheet
│   └── images/             # Website images
├── image-filter-web/       # Python Blender script for image color filtering
│   ├── app.py              # Image filter application
│   ├── templates/          # Image filter app templates
│   └── static/             # Image filter static files
├── trailprint3d-1-90.py    # Blender addon for 3D printable trail maps
├── sample_trail.gpx        # Sample GPX file for testing
├── test_gpx_upload.py      # Setup script for testing
├── test_gpx_functionality.py # GPX functionality tests
└── Documentation files     # Setup and deployment guides
```

## ✨ Features

### Website Features
- **Responsive Design**: Works on all devices
- **Dark Mode Support**: Automatic theme switching
- **Interactive Slideshow**: Process overview with navigation
- **GPX Upload & Preview**: Drag & drop file upload with 3D visualization

### GPX Upload System
- **Real-time 3D Preview**: Interactive Three.js visualization
- **Trail Statistics**: Distance, elevation gain, and data points
- **Multiple View Modes**: 3D perspective and top-down views
- **Auto-rotation**: Camera controls and automatic rotation
- **Demo Mode**: Works with or without backend

### TrailPrint3D Blender Addon
- **3D Printable Maps**: Generate STL files for 3D printing
- **Multiple Shapes**: Hexagon, square, and heart-shaped bases
- **Terrain Data**: Real elevation data from OpenTopoData/Open-Elevation APIs
- **Text Integration**: Add trail name, distance, elevation stats
- **Customizable**: Adjust size, resolution, path thickness
- **Professional Output**: Ready-to-print STL files

## 🚀 Quick Start

### 1. Local Development

```bash
# Start the static website
cd Website
python -m http.server 8080
# Visit: http://localhost:8080
```

### 2. Test GPX Upload

```bash
# Quick setup and test
python test_gpx_upload.py

# Test functionality
python test_gpx_functionality.py
```

### 3. Upload a GPX File
1. Open http://localhost:8080
2. Scroll to "See Your Trail in 3D" section
3. Upload `sample_trail.gpx` or your own GPX file
4. View interactive 3D preview and trail statistics

## 🌐 Deployment Options

### Static Deployment (Netlify)
- Deploy the `Website/` folder
- Uses demo mode with sample data
- Perfect for showcasing the UI/UX
- No server costs

### Full Backend (Heroku/Railway/DigitalOcean)
- Deploy Flask app for real GPX processing
- Handles actual file uploads and processing
- Requires server hosting
- Full functionality

## 🛠️ Dependencies

### Frontend
- Pure HTML, CSS, JavaScript
- Three.js for 3D visualization
- No build process required

### Backend (Optional - for image filtering utility)
- Python 3.8+
- Flask
- PIL (Python Imaging Library)
- NumPy
- xml.etree.ElementTree

Install image filter dependencies (if needed):
```bash
pip install -r image-filter-web/requirements.txt
```

## 📊 GPX Processing

The system processes GPX files by:
1. Parsing XML structure with namespace support
2. Extracting track points (latitude, longitude, elevation)
3. Converting GPS coordinates to normalized 3D coordinates
4. Calculating trail statistics (distance, elevation gain)
5. Generating interactive 3D preview data

Supported formats:
- GPX 1.0 and 1.1
- Track points and waypoints
- Elevation data
- Files up to 16MB

## 🎨 Customization

### Styling
- Main styles in `Website/style.css`
- CSS variables for easy theming
- Responsive design with mobile breakpoints
- Dark mode support

### 3D Visualization
- Three.js scene configuration in `index.html`
- Elevation-based color coding
- Interactive camera controls
- Customizable view modes

## 🎨 Blender Integration for High-Quality Previews

The system now supports integration with Blender for generating professional-quality 3D preview images from GPX files.

### Features
- **High-Quality Rendering**: Cycles renderer with customizable quality settings
- **Professional Materials**: Realistic trail and terrain materials
- **Automatic Camera Positioning**: Optimal viewing angles for each trail
- **Customizable Settings**: Trail thickness, colors, resolution, and sample count
- **Fallback Support**: Gracefully falls back to Three.js if Blender is unavailable

### Setup

#### Option 1: Use Provided Scripts
```bash
# Install Blender addon dependencies
python setup_blender_addon.py

# Install backend dependencies
pip install -r blender_requirements.txt

# Test the integration
python test_blender_integration.py

# Start the backend server
start_blender_backend.bat
```

#### Option 2: Manual Setup
1. **Install Blender 4.2+** from https://www.blender.org/
2. **Install Python dependencies**:
   ```bash
   pip install flask flask-cors
   ```
3. **Run the backend**:
   ```bash
   python blender_backend.py
   ```

### Usage

#### For Development
1. Start the Blender backend: `python blender_backend.py`
2. Open your website and upload a GPX file
3. The system will automatically detect Blender availability
4. If available, generates high-quality preview images
5. If not available, falls back to Three.js browser rendering

#### API Endpoints
- `GET /api/health` - Check Blender availability
- `POST /api/upload-gpx` - Upload GPX and generate preview
- `GET /api/preview/{file_id}` - Serve generated preview image
- `POST /api/regenerate-preview/{file_id}` - Regenerate with new settings
- `DELETE /api/cleanup/{file_id}` - Clean up temporary files

### Integration with Website

The website automatically detects if the Blender backend is running:
- ✅ **Blender Available**: Shows high-quality rendering options and settings
- ⚠️ **Blender Unavailable**: Falls back to Three.js with demo mode

### Files Added
- `blender_gpx_preview.py` - Core Blender integration
- `blender_backend.py` - Flask backend server
- `blender-integration.js` - Frontend JavaScript integration
- `start_blender_backend.bat` - Easy startup script
- `test_blender_integration.py` - Integration testing
- `blender_requirements.txt` - Python dependencies

*Note: Blender integration is currently in development. The system works with Three.js fallback if Blender is not available.*

## 🧪 Testing

- `test_gpx_upload.py` - Setup script that starts servers and creates sample data
- `test_gpx_functionality.py` - Tests GPX upload endpoint and functionality
- `sample_trail.gpx` - Sample GPX file for testing (Duke area trail)

## 📝 License

© 2025 Elevon. All rights reserved.

## 🤝 Support

For questions about the website or GPX upload system, check the documentation files or test scripts in this repository.
