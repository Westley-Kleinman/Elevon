# Elevon GPX Upload & 3D Preview System

## 🏔️ Overview

This system allows users to upload GPX files to your Elevon website and see an instant 3D preview of their trail. The preview shows elevation, distance, and terrain data in a beautiful interactive 3D visualization.

## ✨ Features

- **Drag & Drop GPX Upload**: Easy file upload with visual feedback
- **Real-time 3D Preview**: Interactive 3D visualization using Three.js
- **Trail Statistics**: Automatic calculation of distance, elevation gain, and data points
- **Multiple View Modes**: 3D perspective and top-down views
- **Auto-rotation**: Automatic camera rotation for better viewing
- **Mobile Responsive**: Works on all devices
- **Dark Mode Support**: Matches your website's theme system

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd image-filter-web
pip install -r requirements.txt
```

### 2. Test the System

```bash
# From the Elevon root directory
python test_gpx_upload.py
```

This will:
- Check all dependencies
- Create a sample GPX file for testing
- Start the Flask server
- Open your browser to http://localhost:5000/elevon

### 3. Test GPX Upload

1. Go to your website at http://localhost:5000/elevon
2. Scroll down to the "See Your Trail in 3D" section
3. Upload the generated `sample_trail.gpx` file or any of your own GPX files
4. Watch the 3D preview generate!

## 🛠️ How It Works

### Backend (Flask)

1. **GPX Parser**: Extracts track points, coordinates, and elevation data from GPX files
2. **Data Processing**: Converts GPS coordinates to normalized 3D coordinates
3. **Statistics Calculator**: Computes distance, elevation gain, and trail metrics
4. **API Endpoint**: `/upload_gpx` accepts GPX files and returns processed data

### Frontend (JavaScript + Three.js)

1. **File Upload Handler**: Manages drag-and-drop and file selection
2. **3D Renderer**: Creates interactive 3D visualization using Three.js
3. **Trail Visualization**: Renders trail line, elevation surface, and markers
4. **Interactive Controls**: Camera controls, auto-rotation, view modes

## 📁 File Structure

```
Elevon/
├── image-filter-web/           # Flask backend
│   ├── app.py                 # Main Flask app with GPX processing
│   └── requirements.txt       # Python dependencies
├── Website/
│   ├── index.html            # Updated with GPX upload section
│   └── style.css             # New GPX section styling
├── test_gpx_upload.py        # Test script
└── sample_trail.gpx          # Generated test file
```

## 🎨 Customization

### Styling

The GPX section styling is in `Website/style.css` under the section:
```css
/* GPX UPLOAD AND PREVIEW SECTION */
```

You can customize:
- Colors (uses your existing CSS variables)
- Layout and spacing
- Animation effects
- Preview container size

### 3D Visualization

In `index.html`, you can modify:
- Trail line color and thickness
- Lighting and shadows
- Camera angles and movement
- Marker styles and colors

### Backend Processing

In `app.py`, you can adjust:
- File size limits (`MAX_CONTENT_LENGTH`)
- Coordinate processing algorithms
- Statistics calculations
- Error handling

## 🔧 Integration with Blender/TrailPrint3D

### Current Implementation
The current system provides a **3D preview** for customers to see their trail before ordering.

### Future Blender Integration Options

**Option 1: Server-side Blender (Advanced)**
- Install Blender on your server
- Create Python scripts to interface with TrailPrint3D
- Generate actual 3D models server-side
- Pros: Real Blender output, Cons: Requires server resources

**Option 2: API Integration (Recommended)**
- Keep current preview system
- Add "Generate Full 3D Model" button
- Send GPX data to a separate Blender service
- Pros: Scalable, Cons: More complex setup

**Option 3: Desktop Integration (Simple)**
- Current preview for immediate feedback
- Export GPX data for manual Blender processing
- Pros: Uses existing workflow, Cons: Manual step

## 📊 Trail Statistics

The system automatically calculates:
- **Distance**: Total trail distance in kilometers
- **Elevation Gain**: Total upward elevation change in meters
- **Data Points**: Number of GPS coordinates in the file

## 🌐 Deployment

### Local Development
Use the test script: `python test_gpx_upload.py`

### Production Deployment
1. Deploy the Flask app to your hosting service
2. Update the fetch URL in the JavaScript to your production domain
3. Ensure file upload limits are configured properly
4. Consider adding file cleanup routines

### Hosting Recommendations
- **Heroku**: Easy deployment, good for testing
- **Digital Ocean**: More control, cost-effective
- **AWS/GCP**: Scalable for high traffic

## 🔍 Troubleshooting

### Common Issues

**GPX file not parsing:**
- Check file format (must be valid XML)
- Ensure track points have lat/lon coordinates
- Verify elevation data exists

**3D preview not showing:**
- Check browser console for JavaScript errors
- Ensure Three.js CDN is loading
- Try the 2D fallback mode

**Upload failing:**
- Check file size (max 16MB)
- Verify server is running
- Check Flask console for errors

### Browser Support

- **Full 3D**: Modern browsers with WebGL support
- **2D Fallback**: All browsers with Canvas support
- **Mobile**: Responsive design works on all devices

## 💡 Next Steps

1. **Test with your actual GPX files**
2. **Customize the styling to match your brand**
3. **Consider integrating with your existing order system**
4. **Add more trail analysis features (gradient, difficulty, etc.)**
5. **Implement caching for better performance**

## 🤝 Support

If you need help:
1. Check the browser console for JavaScript errors
2. Check the Flask console for server errors
3. Test with the provided sample GPX file first
4. Verify all dependencies are installed correctly

Happy mapping! 🗺️✨
