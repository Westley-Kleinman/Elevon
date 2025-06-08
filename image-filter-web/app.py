from flask import Flask, render_template, request, send_file
from PIL import Image
import numpy as np
import io
import os

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable Flask static file caching

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

if __name__ == '__main__':
    app.run(debug=True)