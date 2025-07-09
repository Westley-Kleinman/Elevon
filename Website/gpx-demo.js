// Mock GPX upload functionality for Netlify (static hosting)
// This replaces the Flask backend calls with demo data

document.addEventListener('DOMContentLoaded', function() {
  // ... existing slideshow code ...
  
  // Initialize GPX upload functionality with demo mode
  initializeGPXUploadDemo();
  
  function initializeGPXUploadDemo() {
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('gpx-file-input');
    const uploadProgress = document.getElementById('upload-progress');
    const trailStats = document.getElementById('trail-stats');
    const previewContainer = document.getElementById('preview-container');
    const previewPlaceholder = document.getElementById('preview-placeholder');
    const trailCanvas = document.getElementById('trail-canvas');
    const previewControls = document.getElementById('preview-controls');
    
    if (!uploadZone || !fileInput) {
      console.warn('GPX upload elements not found');
      return;
    }
    
    // Demo trail data (simulates a processed GPX file)
    const demoTrailData = {
      points: [
        [0.1, 0.1, 0.2], [0.15, 0.12, 0.25], [0.2, 0.15, 0.3], [0.25, 0.18, 0.35],
        [0.3, 0.22, 0.4], [0.35, 0.25, 0.45], [0.4, 0.28, 0.5], [0.45, 0.32, 0.55],
        [0.5, 0.35, 0.6], [0.55, 0.38, 0.65], [0.6, 0.42, 0.7], [0.65, 0.45, 0.75],
        [0.7, 0.48, 0.8], [0.75, 0.52, 0.85], [0.8, 0.55, 0.9], [0.85, 0.58, 0.95],
        [0.9, 0.62, 1.0]
      ],
      bounds: {
        lat: [35.7796, 35.7986],
        lon: [-78.6572, -78.6382],
        ele: [100, 480]
      },
      stats: {
        total_points: 17,
        distance_km: 2.3,
        elevation_gain: 380
      }
    };
    
    let currentTrailData = null;
    let renderer = null;
    let scene = null;
    let camera = null;
    let controls = null;
    let animationId = null;
    
    // File upload handling
    uploadZone.addEventListener('click', () => fileInput.click());
    
    uploadZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
      uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadZone.classList.remove('dragover');
      
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFileUploadDemo(files[0]);
      }
    });
    
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleFileUploadDemo(e.target.files[0]);
      }
    });
    
    function handleFileUploadDemo(file) {
      if (!file.name.toLowerCase().endsWith('.gpx')) {
        showError('Please upload a .gpx file');
        return;
      }
      
      // Show demo message
      if (!confirm('Demo Mode: This will show a sample trail preview. In the full version, your actual GPX file would be processed. Continue?')) {
        return;
      }
      
      // Show progress
      uploadZone.style.display = 'none';
      uploadProgress.style.display = 'block';
      
      // Simulate progress
      const progressFill = document.getElementById('progress-fill');
      const progressText = document.getElementById('progress-text');
      
      let progress = 0;
      const progressInterval = setInterval(() => {
        progress += Math.random() * 20;
        if (progress > 90) {
          clearInterval(progressInterval);
          progress = 100;
          progressFill.style.width = '100%';
          
          // Show demo results
          setTimeout(() => {
            currentTrailData = demoTrailData;
            displayTrailStats(demoTrailData.stats);
            create3DPreview(demoTrailData);
            
            uploadProgress.style.display = 'none';
            trailStats.style.display = 'block';
            previewPlaceholder.style.display = 'none';
            trailCanvas.style.display = 'block';
            previewControls.style.display = 'flex';
          }, 500);
        } else {
          progressFill.style.width = progress + '%';
        }
      }, 100);
    }
    
    function displayTrailStats(stats) {
      document.getElementById('distance-value').textContent = stats.distance_km;
      document.getElementById('elevation-value').textContent = stats.elevation_gain;
      document.getElementById('points-value').textContent = stats.total_points.toLocaleString();
    }
    
    function showError(message) {
      uploadProgress.style.display = 'none';
      uploadZone.style.display = 'block';
      alert(message);
    }
    
    // 3D Visualization (same as before)
    function create3DPreview(trailData) {
      if (!window.THREE) {
        create2DPreview(trailData);
        return;
      }
      
      // Initialize Three.js scene
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0xf8f9fa);
      
      // Camera setup
      camera = new THREE.PerspectiveCamera(75, trailCanvas.offsetWidth / trailCanvas.offsetHeight, 0.1, 1000);
      camera.position.set(0.5, 1, 0.5);
      camera.lookAt(0.5, 0, 0.5);
      
      // Renderer setup
      renderer = new THREE.WebGLRenderer({ canvas: trailCanvas, antialias: true });
      renderer.setSize(trailCanvas.offsetWidth, trailCanvas.offsetHeight);
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      
      // Lighting
      const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
      scene.add(ambientLight);
      
      const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
      directionalLight.position.set(1, 1, 0.5);
      directionalLight.castShadow = true;
      scene.add(directionalLight);
      
      // Create trail geometry
      createTrailMesh(trailData.points);
      
      // Add controls
      if (window.THREE.OrbitControls) {
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.1;
      }
      
      // Start animation loop
      animate();
      
      // Setup control buttons
      setupPreviewControls();
    }
    
    // ... (rest of the 3D functions remain the same as in the original code)
    function createTrailMesh(points) {
      const geometry = new THREE.BufferGeometry();
      const positions = [];
      
      points.forEach(point => {
        positions.push(point[0], point[2], point[1]);
      });
      
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      
      const material = new THREE.LineBasicMaterial({ 
        color: 0x2d5a3d, 
        linewidth: 3 
      });
      
      const line = new THREE.Line(geometry, material);
      scene.add(line);
      
      if (points.length > 2) {
        createElevationSurface(points);
      }
      
      addTrailMarkers(points);
    }
    
    function createElevationSurface(points) {
      const surfaceGeometry = new THREE.PlaneGeometry(1, 1, 32, 32);
      const surfaceMaterial = new THREE.MeshLambertMaterial({ 
        color: 0xe5e5e5,
        transparent: true,
        opacity: 0.7,
        side: THREE.DoubleSide
      });
      
      const surface = new THREE.Mesh(surfaceGeometry, surfaceMaterial);
      surface.rotation.x = -Math.PI / 2;
      surface.position.y = -0.1;
      scene.add(surface);
    }
    
    function addTrailMarkers(points) {
      const startGeometry = new THREE.SphereGeometry(0.02, 8, 6);
      const startMaterial = new THREE.MeshLambertMaterial({ color: 0x2d5a3d });
      const startMarker = new THREE.Mesh(startGeometry, startMaterial);
      
      if (points.length > 0) {
        startMarker.position.set(points[0][0], points[0][2] + 0.02, points[0][1]);
        scene.add(startMarker);
      }
      
      const endGeometry = new THREE.SphereGeometry(0.02, 8, 6);
      const endMaterial = new THREE.MeshLambertMaterial({ color: 0xd4621a });
      const endMarker = new THREE.Mesh(endGeometry, endMaterial);
      
      if (points.length > 1) {
        const lastPoint = points[points.length - 1];
        endMarker.position.set(lastPoint[0], lastPoint[2] + 0.02, lastPoint[1]);
        scene.add(endMarker);
      }
    }
    
    function animate() {
      animationId = requestAnimationFrame(animate);
      
      if (controls) {
        controls.update();
      }
      
      if (renderer && scene && camera) {
        renderer.render(scene, camera);
      }
    }
    
    function setupPreviewControls() {
      const rotateBtn = document.getElementById('rotate-btn');
      const resetViewBtn = document.getElementById('reset-view-btn');
      const modeButtons = document.querySelectorAll('.mode-btn');
      
      let autoRotate = false;
      
      if (rotateBtn) {
        rotateBtn.addEventListener('click', () => {
          autoRotate = !autoRotate;
          if (controls) {
            controls.autoRotate = autoRotate;
            rotateBtn.textContent = autoRotate ? '⏸️ Stop Rotate' : '🔄 Auto Rotate';
          }
        });
      }
      
      if (resetViewBtn) {
        resetViewBtn.addEventListener('click', () => {
          if (camera && controls) {
            camera.position.set(0.5, 1, 0.5);
            camera.lookAt(0.5, 0, 0.5);
            controls.reset();
          }
        });
      }
      
      modeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          modeButtons.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          
          if (btn.dataset.mode === 'topdown' && camera) {
            camera.position.set(0.5, 2, 0.5);
            camera.lookAt(0.5, 0, 0.5);
          } else if (btn.dataset.mode === '3d' && camera) {
            camera.position.set(0.5, 1, 0.5);
            camera.lookAt(0.5, 0, 0.5);
          }
        });
      });
    }
    
    function create2DPreview(trailData) {
      const ctx = trailCanvas.getContext('2d');
      const width = trailCanvas.offsetWidth;
      const height = trailCanvas.offsetHeight;
      
      trailCanvas.width = width;
      trailCanvas.height = height;
      
      ctx.fillStyle = '#f8f9fa';
      ctx.fillRect(0, 0, width, height);
      
      const points = trailData.points;
      if (points.length < 2) return;
      
      ctx.strokeStyle = '#2d5a3d';
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      
      ctx.beginPath();
      ctx.moveTo(points[0][0] * width, points[0][1] * height);
      
      for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i][0] * width, points[i][1] * height);
      }
      
      ctx.stroke();
      
      ctx.fillStyle = '#2d5a3d';
      ctx.beginPath();
      ctx.arc(points[0][0] * width, points[0][1] * height, 6, 0, Math.PI * 2);
      ctx.fill();
      
      ctx.fillStyle = '#d4621a';
      ctx.beginPath();
      const lastPoint = points[points.length - 1];
      ctx.arc(lastPoint[0] * width, lastPoint[1] * height, 6, 0, Math.PI * 2);
      ctx.fill();
    }
    
    window.addEventListener('resize', () => {
      if (renderer && camera) {
        camera.aspect = trailCanvas.offsetWidth / trailCanvas.offsetHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(trailCanvas.offsetWidth, trailCanvas.offsetHeight);
      }
    });
    
    window.addEventListener('beforeunload', () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
      if (renderer) {
        renderer.dispose();
      }
    });
  }
});
