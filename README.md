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

## 🎨 Blender Addon for 3D Printing

For creating actual 3D printable trail maps:

### Installation
```bash
# Install dependencies
python setup_blender_addon.py

# Install addon (run as administrator if needed)
install_blender_addon.bat
```

### Manual Installation
1. Copy `trailprint3d-1-90.py` to Blender's addons folder
2. Enable the addon in Blender: Edit > Preferences > Add-ons
3. Search for "TrailPrint3D" and enable it
4. Press 'N' in 3D viewport to access the panel

See `BLENDER_ADDON_GUIDE.md` for detailed instructions.

## 🧪 Testing

- `test_gpx_upload.py` - Setup script that starts servers and creates sample data
- `test_gpx_functionality.py` - Tests GPX upload endpoint and functionality
- `sample_trail.gpx` - Sample GPX file for testing (Duke area trail)

## 📝 License

© 2025 Elevon. All rights reserved.

## 🤝 Support

For questions about the website or GPX upload system, check the documentation files or test scripts in this repository.
