/**
 * Blender GPX Preview Integration
 * Integrates high-quality Blender rendering with the existing GPX upload system
 */

class BlenderGPXPreview {
    constructor(backendUrl = 'http://localhost:5000') {
        this.backendUrl = backendUrl;
        this.currentFileId = null;
        this.isGenerating = false;
    }

    /**
     * Check if Blender backend is available
     */
    async checkBackendHealth() {
        try {
            const response = await fetch(`${this.backendUrl}/api/health`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Backend health check failed:', error);
            return { status: 'offline', blender_available: false };
        }
    }

    /**
     * Upload GPX file and generate Blender preview
     */
    async uploadAndGeneratePreview(file, settings = {}) {
        if (this.isGenerating) {
            throw new Error('Preview generation already in progress');
        }

        this.isGenerating = true;

        try {
            const formData = new FormData();
            formData.append('gpx', file);
            
            // Add render settings
            Object.entries(settings).forEach(([key, value]) => {
                formData.append(key, value.toString());
            });

            const response = await fetch(`${this.backendUrl}/api/upload-gpx`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                // Try to get the error message from the response body
                let errorMessage = `Upload failed: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    if (errorData.error) {
                        errorMessage = errorData.error;
                    }
                } catch (e) {
                    // If we can't parse the JSON, stick with the status text
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            this.currentFileId = data.file_id;
            
            return data;

        } finally {
            this.isGenerating = false;
        }
    }

    /**
     * Regenerate preview with different settings
     */
    async regeneratePreview(fileId, settings) {
        if (!fileId) {
            throw new Error('No file ID provided');
        }

        const response = await fetch(`${this.backendUrl}/api/regenerate-preview/${fileId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });

        if (!response.ok) {
            throw new Error(`Regeneration failed: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Get preview image URL
     */
    getPreviewUrl(fileId) {
        return `${this.backendUrl}/api/preview/${fileId}?t=${Date.now()}`;
    }

    /**
     * Clean up files on server
     */
    async cleanup(fileId) {
        if (!fileId) return;

        try {
            await fetch(`${this.backendUrl}/api/cleanup/${fileId}`, {
                method: 'DELETE'
            });
        } catch (error) {
            console.error('Cleanup failed:', error);
        }
    }
}

/**
 * Enhanced GPX Upload Interface with Blender Integration
 */
class EnhancedGPXUpload {
    constructor() {
        this.blenderPreview = new BlenderGPXPreview();
        this.currentFileId = null;
        this.fallbackToThreeJS = true;
        
        this.init();
    }

    async init() {
        // Check if Blender backend is available
        const health = await this.blenderPreview.checkBackendHealth();
        this.blenderAvailable = health.blender_available;
        
        console.log('Blender backend status:', health);
        
        this.setupEventListeners();
        this.updateUI();
    }

    setupEventListeners() {
        const dropZone = document.getElementById('gpx-drop-zone');
        const fileInput = document.getElementById('gpx-file-input');
        const generateBtn = document.getElementById('blender-generate-btn');
        const settingsForm = document.getElementById('blender-settings');

        if (dropZone) {
            dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
            dropZone.addEventListener('drop', this.handleDrop.bind(this));
            dropZone.addEventListener('click', () => fileInput?.click());
        }

        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }

        if (generateBtn) {
            generateBtn.addEventListener('click', this.regeneratePreview.bind(this));
        }
    }

    updateUI() {
        const blenderSection = document.getElementById('blender-preview-section');
        const statusElement = document.getElementById('blender-status');
        
        if (statusElement) {
            if (this.blenderAvailable) {
                statusElement.innerHTML = '🎨 Blender rendering available';
                statusElement.className = 'blender-status available';
            } else {
                statusElement.innerHTML = '⚠️ Blender rendering unavailable (using fallback)';
                statusElement.className = 'blender-status unavailable';
            }
        }

        if (blenderSection) {
            blenderSection.style.display = this.blenderAvailable ? 'block' : 'none';
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    async processFile(file) {
        console.log('Processing file:', file.name, 'Size:', file.size, 'Type:', file.type);
        
        if (!file.name.toLowerCase().endsWith('.gpx')) {
            this.showError('Please select a GPX file');
            return;
        }

        // Debug: Check if file has content
        if (file.size === 0) {
            this.showError('Selected file is empty');
            return;
        }

        this.showLoading('Processing GPX file...');

        try {
            // If Blender is available, use it; otherwise fall back to Three.js
            if (this.blenderAvailable) {
                await this.processWithBlender(file);
            } else if (this.fallbackToThreeJS) {
                await this.processWithThreeJS(file);
            } else {
                throw new Error('No rendering backend available');
            }

        } catch (error) {
            console.error('Error processing file:', error);
            this.showError(`Error: ${error.message}`);
            
            // If Blender fails and fallback is enabled, try Three.js
            if (this.blenderAvailable && this.fallbackToThreeJS) {
                console.log('Falling back to Three.js rendering...');
                try {
                    await this.processWithThreeJS(file);
                } catch (fallbackError) {
                    this.showError(`Fallback also failed: ${fallbackError.message}`);
                }
            }
        }
    }

    async processWithBlender(file) {
        console.log('Processing with Blender:', file.name, file.size);
        this.showLoading('Generating high-quality preview with Blender...');

        const settings = this.getBlenderSettings();
        console.log('Blender settings:', settings);
        
        const result = await this.blenderPreview.uploadAndGeneratePreview(file, settings);
        console.log('Blender result:', result);

        this.currentFileId = result.file_id;

        // Display stats
        this.displayStats(result.stats);

        // Display preview if available
        if (result.preview_url) {
            this.displayBlenderPreview(result.file_id);
            this.hideLoading();
        } else if (result.preview_error) {
            throw new Error(result.preview_error);
        } else {
            this.showLoading('Preview is being generated...');
            // Could poll for completion or show progress
        }
    }

    async processWithThreeJS(file) {
        this.showLoading('Generating preview...');
        
        // Use existing Three.js implementation
        const text = await file.text();
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(text, "text/xml");
        
        // Extract coordinates (existing logic)
        const coordinates = this.extractCoordinatesFromGPX(xmlDoc);
        
        if (coordinates.length === 0) {
            throw new Error('No track points found in GPX file');
        }

        // Calculate stats
        const stats = this.calculateStats(coordinates);
        this.displayStats(stats);

        // Create Three.js visualization
        this.createThreeJSVisualization(coordinates);
        this.hideLoading();
    }

    getBlenderSettings() {
        const settingsForm = document.getElementById('blender-settings');
        if (!settingsForm) return {};

        const formData = new FormData(settingsForm);
        const settings = {};
        
        for (const [key, value] of formData.entries()) {
            if (value !== '') {
                settings[key] = value;
            }
        }

        return settings;
    }

    displayBlenderPreview(fileId) {
        const previewContainer = document.getElementById('preview-container');
        if (!previewContainer) return;

        const imageUrl = this.blenderPreview.getPreviewUrl(fileId);
        
        previewContainer.innerHTML = `
            <div class="blender-preview">
                <img src="${imageUrl}" alt="3D Trail Preview" class="preview-image" />
                <div class="preview-controls">
                    <button id="regenerate-btn" class="btn-secondary">
                        🎨 Regenerate with Different Settings
                    </button>
                    <button id="download-btn" class="btn-secondary">
                        💾 Download Preview
                    </button>
                </div>
            </div>
        `;

        // Add event listeners
        document.getElementById('regenerate-btn')?.addEventListener('click', 
            () => this.regeneratePreview());
        
        document.getElementById('download-btn')?.addEventListener('click', 
            () => this.downloadPreview(imageUrl));
    }

    async regeneratePreview() {
        if (!this.currentFileId) return;

        this.showLoading('Regenerating preview...');

        try {
            const settings = this.getBlenderSettings();
            await this.blenderPreview.regeneratePreview(this.currentFileId, settings);
            
            // Refresh the preview image
            this.displayBlenderPreview(this.currentFileId);
            this.hideLoading();
            
        } catch (error) {
            this.showError(`Regeneration failed: ${error.message}`);
        }
    }

    downloadPreview(imageUrl) {
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = 'trail-preview.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    displayStats(stats) {
        const statsContainer = document.getElementById('gpx-stats');
        if (!statsContainer || !stats) return;

        statsContainer.innerHTML = `
            <div class="gpx-stats">
                <div class="stat-item">
                    <span class="stat-label">Distance:</span>
                    <span class="stat-value">${stats.distance_km} km</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Elevation Gain:</span>
                    <span class="stat-value">${stats.elevation_gain_m} m</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Max Elevation:</span>
                    <span class="stat-value">${stats.max_elevation_m} m</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Data Points:</span>
                    <span class="stat-value">${stats.points_count}</span>
                </div>
                ${stats.duration_hours ? `
                <div class="stat-item">
                    <span class="stat-label">Duration:</span>
                    <span class="stat-value">${stats.duration_hours} hours</span>
                </div>
                ` : ''}
            </div>
        `;
    }

    showLoading(message) {
        const loadingElement = document.getElementById('loading-message');
        if (loadingElement) {
            loadingElement.textContent = message;
            loadingElement.style.display = 'block';
        }
    }

    hideLoading() {
        const loadingElement = document.getElementById('loading-message');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    showError(message) {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
        this.hideLoading();
    }

    // Cleanup when page unloads
    cleanup() {
        if (this.currentFileId) {
            this.blenderPreview.cleanup(this.currentFileId);
        }
    }

    // Existing Three.js methods would go here...
    extractCoordinatesFromGPX(xmlDoc) {
        const coordinates = [];
        
        // Try to find track points with namespace
        const namespaceURI = 'http://www.topografix.com/GPX/1/1';
        let trkpts = xmlDoc.getElementsByTagNameNS(namespaceURI, 'trkpt');
        
        // If no namespaced elements found, try without namespace
        if (trkpts.length === 0) {
            trkpts = xmlDoc.getElementsByTagName('trkpt');
        }
        
        // Convert NodeList to Array and extract coordinates
        Array.from(trkpts).forEach(trkpt => {
            const lat = parseFloat(trkpt.getAttribute('lat'));
            const lon = parseFloat(trkpt.getAttribute('lon'));
            
            // Try to get elevation
            let ele = 0;
            let eleElem = trkpt.getElementsByTagNameNS(namespaceURI, 'ele')[0];
            if (!eleElem) {
                eleElem = trkpt.getElementsByTagName('ele')[0];
            }
            if (eleElem) {
                ele = parseFloat(eleElem.textContent) || 0;
            }
            
            coordinates.push({ lat, lon, ele });
        });
        
        // If no track points found, try route points
        if (coordinates.length === 0) {
            let rtepts = xmlDoc.getElementsByTagNameNS(namespaceURI, 'rtept');
            if (rtepts.length === 0) {
                rtepts = xmlDoc.getElementsByTagName('rtept');
            }
            
            Array.from(rtepts).forEach(rtept => {
                const lat = parseFloat(rtept.getAttribute('lat'));
                const lon = parseFloat(rtept.getAttribute('lon'));
                
                let ele = 0;
                let eleElem = rtept.getElementsByTagNameNS(namespaceURI, 'ele')[0];
                if (!eleElem) {
                    eleElem = rtept.getElementsByTagName('ele')[0];
                }
                if (eleElem) {
                    ele = parseFloat(eleElem.textContent) || 0;
                }
                
                coordinates.push({ lat, lon, ele });
            });
        }
        
        console.log(`Extracted ${coordinates.length} coordinates from GPX`);
        return coordinates;
    }

    calculateStats(coordinates) {
        if (coordinates.length === 0) {
            return {};
        }
        
        let minLat = coordinates[0].lat;
        let maxLat = coordinates[0].lat;
        let minLon = coordinates[0].lon;
        let maxLon = coordinates[0].lon;
        let minEle = coordinates[0].ele;
        let maxEle = coordinates[0].ele;
        let totalDistance = 0;
        
        // Calculate bounds and elevation stats
        coordinates.forEach((coord, index) => {
            minLat = Math.min(minLat, coord.lat);
            maxLat = Math.max(maxLat, coord.lat);
            minLon = Math.min(minLon, coord.lon);
            maxLon = Math.max(maxLon, coord.lon);
            minEle = Math.min(minEle, coord.ele);
            maxEle = Math.max(maxEle, coord.ele);
            
            // Calculate distance between consecutive points
            if (index > 0) {
                const prev = coordinates[index - 1];
                const distance = this.calculateDistance(prev.lat, prev.lon, coord.lat, coord.lon);
                totalDistance += distance;
            }
        });
        
        return {
            total_points: coordinates.length,
            total_distance: totalDistance.toFixed(2),
            elevation_gain: (maxEle - minEle).toFixed(2),
            min_elevation: minEle.toFixed(2),
            max_elevation: maxEle.toFixed(2),
            bounds: {
                min_lat: minLat,
                max_lat: maxLat,
                min_lon: minLon,
                max_lon: maxLon
            }
        };
    }
    
    calculateDistance(lat1, lon1, lat2, lon2) {
        // Haversine formula for calculating distance between two points
        const R = 6371; // Earth's radius in kilometers
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    createThreeJSVisualization(coordinates) {
        // Create a simple Three.js visualization
        const previewContainer = document.getElementById('preview-container');
        if (!previewContainer) return;
        
        previewContainer.innerHTML = `
            <div class="threejs-preview">
                <div class="preview-placeholder">
                    <h3>🌄 3D Trail Preview</h3>
                    <p>${coordinates.length} track points loaded</p>
                    <p><em>Three.js visualization coming soon...</em></p>
                    <div class="fallback-info">
                        <p>This is the fallback mode. For high-quality 3D renders, ensure Blender backend is running.</p>
                    </div>
                </div>
            </div>
        `;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.gpxUpload = new EnhancedGPXUpload();
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (window.gpxUpload) {
            window.gpxUpload.cleanup();
        }
    });
});

// CSS styles for Blender integration
const blenderStyles = `
.blender-preview {
    text-align: center;
    margin: 20px 0;
}

.preview-image {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.preview-controls {
    margin-top: 15px;
    display: flex;
    gap: 10px;
    justify-content: center;
    flex-wrap: wrap;
}

.blender-status {
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 14px;
    margin: 10px 0;
}

.blender-status.available {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.blender-status.unavailable {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

.blender-settings {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
}

.settings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
}

.setting-group {
    display: flex;
    flex-direction: column;
}

.setting-group label {
    font-weight: 500;
    margin-bottom: 5px;
    color: #333;
}

.setting-group input,
.setting-group select {
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

#loading-message {
    text-align: center;
    padding: 20px;
    font-style: italic;
    color: #666;
}

#error-message {
    text-align: center;
    padding: 20px;
    color: #dc3545;
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    margin: 20px 0;
}
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = blenderStyles;
document.head.appendChild(styleSheet);
