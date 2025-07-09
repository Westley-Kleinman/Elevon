# Elevon Website Deployment Guide

## 🌐 Two Deployment Options

### 1. **Netlify (Static Demo)**
- Deploys the Website folder as a static site
- Shows demo 3D visualization with sample data
- Perfect for showcasing the UI/UX to customers
- URL: Will be provided by Netlify

### 2. **Flask Backend (Full Functionality)**
- Complete GPX processing with real file uploads
- Actual trail data processing and statistics
- Deploy to Heroku, Railway, or DigitalOcean
- Requires server hosting

## 🚀 Current Status

This repository contains:
- ✅ Complete static website (Website folder)
- ✅ Complete Flask backend (image-filter-web folder)
- ✅ Demo mode for static hosting
- ✅ Full functionality for server hosting

## 📁 File Structure

```
Elevon/
├── Website/              # Static website (for Netlify)
│   ├── index.html       # Main page with GPX upload
│   ├── style.css        # All styling
│   ├── gpx-demo.js      # Demo functionality
│   └── images/          # Website assets
├── image-filter-web/    # Flask backend (for server hosting)
│   ├── app.py          # Flask app with GPX processing
│   └── requirements.txt # Python dependencies
├── netlify.toml        # Netlify configuration
└── README files        # Documentation
```

## 🎯 Next Steps

1. **Test on Netlify**: Push to Git and connect to Netlify
2. **Test locally**: Run Flask app for full functionality
3. **Production**: Deploy Flask backend to server hosting

## 🔧 Configuration

- **Demo Mode**: Set in index.html (`window.DEMO_MODE = true`)
- **Production Mode**: Set to `false` when using Flask backend
- **Netlify**: Automatically uses demo mode
- **Server**: Uses full Flask functionality
