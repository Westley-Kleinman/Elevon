// Web Worker for heavy image processing tasks
// This runs in a separate thread to prevent blocking the UI

// Import the same helper functions (simplified versions)
function drawThickPixel(data, x, y, width, height, thickness) {
    const radius = Math.floor(thickness / 2);
    for (let dy = -radius; dy <= radius; dy++) {
        for (let dx = -radius; dx <= radius; dx++) {
            const nx = x + dx;
            const ny = y + dy;
            if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist <= radius) {
                    const index = (ny * width + nx) * 4;
                    data[index] = 0;     // R
                    data[index + 1] = 0; // G
                    data[index + 2] = 0; // B
                    data[index + 3] = 255; // A
                }
            }
        }
    }
}

// Enhanced thick pixel drawing with overlap detection
function drawThickPixelWithOverlapDetection(data, x, y, width, height, thickness, overlapMap) {
    const radius = Math.floor(thickness / 2);
    let hasOverlap = false;
    
    for (let dy = -radius; dy <= radius; dy++) {
        for (let dx = -radius; dx <= radius; dx++) {
            const nx = x + dx;
            const ny = y + dy;
            if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist <= radius) {
                    const index = (ny * width + nx) * 4;
                    const coord = `${nx},${ny}`;
                    
                    // Check for overlap
                    if (overlapMap.has(coord)) {
                        hasOverlap = true;
                    } else {
                        overlapMap.add(coord);
                    }
                    
                    data[index] = 0;     // R
                    data[index + 1] = 0; // G
                    data[index + 2] = 0; // B
                    data[index + 3] = 255; // A
                }
            }
        }
    }
    return hasOverlap;
}

// Simplified Zhang-Suen thinning for worker
function zhangSuenThinning(trailPixels, width, height) {
    if (trailPixels.size === 0) return new Set();
    
    const binary = Array(height).fill().map(() => Array(width).fill(0));
    for (const coord of trailPixels) {
        const [x, y] = coord.split(',').map(Number);
        if (x >= 0 && x < width && y >= 0 && y < height) {
            binary[y][x] = 1;
        }
    }
    
    let changed = true;
    let iteration = 0;
    const maxIterations = 50; // Reduced for worker performance
    
    while (changed && iteration < maxIterations) {
        changed = false;
        const toDelete = [];
        
        for (let step = 0; step < 2; step++) {
            for (let y = 1; y < height - 1; y++) {
                for (let x = 1; x < width - 1; x++) {
                    if (binary[y][x] === 1) {
                        const neighbors = [
                            binary[y-1][x], binary[y-1][x+1], binary[y][x+1], binary[y+1][x+1],
                            binary[y+1][x], binary[y+1][x-1], binary[y][x-1], binary[y-1][x-1]
                        ];
                        
                        const blackNeighbors = neighbors.reduce((sum, val) => sum + val, 0);
                        
                        let transitions = 0;
                        for (let i = 0; i < 8; i++) {
                            if (neighbors[i] === 0 && neighbors[(i + 1) % 8] === 1) {
                                transitions++;
                            }
                        }
                        
                        const cond1 = blackNeighbors >= 2 && blackNeighbors <= 6;
                        const cond2 = transitions === 1;
                        
                        let cond3, cond4;
                        if (step === 0) {
                            cond3 = neighbors[0] * neighbors[2] * neighbors[4] === 0;
                            cond4 = neighbors[2] * neighbors[4] * neighbors[6] === 0;
                        } else {
                            cond3 = neighbors[0] * neighbors[2] * neighbors[6] === 0;
                            cond4 = neighbors[0] * neighbors[4] * neighbors[6] === 0;
                        }
                        
                        if (cond1 && cond2 && cond3 && cond4) {
                            toDelete.push([x, y]);
                            changed = true;
                        }
                    }
                }
            }
            
            for (const [x, y] of toDelete) {
                binary[y][x] = 0;
            }
            toDelete.length = 0;
        }
        iteration++;
    }
    
    const result = new Set();
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            if (binary[y][x] === 1) {
                result.add(`${x},${y}`);
            }
        }
    }
    
    return result;
}

// Simplified preprocessing for worker
function preprocessTrailPixels(trailPixels, width, height) {
    const processed = new Set();
    
    // Remove isolated pixels
    for (const coord of trailPixels) {
        const [x, y] = coord.split(',').map(Number);
        let neighbors = 0;
        
        for (let dy = -1; dy <= 1; dy++) {
            for (let dx = -1; dx <= 1; dx++) {
                if (dx === 0 && dy === 0) continue;
                if (trailPixels.has(`${x + dx},${y + dy}`)) {
                    neighbors++;
                }
            }
        }
        
        if (neighbors > 0) {
            processed.add(coord);
        }
    }
    
    return processed;
}

// Main centerline processing function
function createCenterlineTrace(trailPixels, width, height) {
    if (trailPixels.size === 0) return new Set();
    
    const preprocessed = preprocessTrailPixels(trailPixels, width, height);
    const thinned = zhangSuenThinning(preprocessed, width, height);
    
    // If result is too sparse, use sampling fallback
    if (thinned.size < Math.max(10, trailPixels.size * 0.05)) {
        const fallback = new Set();
        let count = 0;
        for (const coord of preprocessed) {
            if (count % 3 === 0) { // Sample every 3rd pixel
                fallback.add(coord);
            }
            count++;
        }
        return fallback;
    }
    
    return thinned;
}

// Main worker message handler
self.onmessage = function(e) {
    const { imageData, colorTolerance, taskId, lineThickness = 4 } = e.data;
    const { data, width, height } = imageData;
    
    try {
        // Send progress update
        self.postMessage({
            type: 'progress',
            taskId,
            progress: 10,
            message: 'Identifying trail pixels...'
        });
        
        // First pass: identify trail pixels
        const trailPixels = new Set();
        for (let i = 0; i < data.length; i += 4) {
            if (data[i+3] === 0) {
                data[i] = 255; data[i+1] = 255; data[i+2] = 255; data[i+3] = 255;
                continue;
            }
            
            const originalR = data[i];
            const originalG = data[i+1];
            const originalB = data[i+2];
            let keep = false;
            
            for (const c of colorTolerance) {
                const dr = originalR - c.r;
                const dg = originalG - c.g;
                const db = originalB - c.b;
                const dist = Math.sqrt(dr*dr + dg*dg + db*db);
                if (dist <= c.tol) {
                    keep = true;
                    break;
                }
            }
            
            if (keep) {
                const pixelIndex = Math.floor(i / 4);
                const x = pixelIndex % width;
                const y = Math.floor(pixelIndex / width);
                trailPixels.add(`${x},${y}`);
            }
            
            // Set to white initially
            data[i] = 255; data[i+1] = 255; data[i+2] = 255; data[i+3] = 255;
        }
        
        // Progress update
        self.postMessage({
            type: 'progress',
            taskId,
            progress: 40,
            message: 'Processing centerlines...'
        });
        
        // Create centerline trace
        const processedTrailPixels = createCenterlineTrace(trailPixels, width, height);
        
        // Progress update
        self.postMessage({
            type: 'progress',
            taskId,
            progress: 70,
            message: 'Drawing thick lines...'
        });
          // Draw thick lines on processed pixels
        const overlapMap = new Set();
        let overlapCount = 0;
        
        for (const coordStr of processedTrailPixels) {
            const [x, y] = coordStr.split(',').map(Number);
            const hasOverlap = drawThickPixelWithOverlapDetection(data, x, y, width, height, lineThickness, overlapMap);
            if (hasOverlap) overlapCount++;
        }
        
        // Report overlap statistics
        if (overlapCount > 0) {
            self.postMessage({
                type: 'warning',
                taskId,
                message: `Detected ${overlapCount} potential trail overlaps. Consider reducing line thickness.`
            });
        }
        
        // Final progress update
        self.postMessage({
            type: 'progress',
            taskId,
            progress: 100,
            message: 'Complete!'
        });
        
        // Send result back
        self.postMessage({
            type: 'complete',
            taskId,
            imageData: { data, width, height }
        });
        
    } catch (error) {
        self.postMessage({
            type: 'error',
            taskId,
            error: error.message
        });
    }
};
