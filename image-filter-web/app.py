from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image
import numpy as np
import io
import os

app = Flask(__name__)

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

def get_top_colors(image, num_colors=5):
    arr = np.array(image.convert('RGBA'))
    mask = arr[..., 3] != 0
    pixels = arr[..., :3][mask]
    if len(pixels) == 0:
        return []
    unique, counts = np.unique(pixels.reshape(-1, 3), axis=0, return_counts=True)
    top = unique[np.argsort(-counts)][:num_colors]
    return [tuple(map(int, c)) for c in top]

@app.route('/top_colors', methods=['POST'])
def top_colors():
    file = request.files['image']
    image = Image.open(file.stream)
    top = get_top_colors(image)
    return jsonify({'top_colors': top})

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['image']
        output_configs = []
        for out in range(3):
            filename = request.form.get(f'filename_{out}', '').strip()
            if not filename:
                continue
            filename = os.path.splitext(filename)[0] + '.png'
            color_tolerance_list = []
            for slot in range(3):
                try:
                    r = request.form.get(f'r_{out}_{slot}')
                    g = request.form.get(f'g_{out}_{slot}')
                    b = request.form.get(f'b_{out}_{slot}')
                    t = request.form.get(f't_{out}_{slot}')
                    if r and g and b and t:
                        color = (int(r), int(g), int(b))
                        tol = float(t)
                        color_tolerance_list.append((color, tol))
                except Exception:
                    continue
            if color_tolerance_list:
                output_configs.append((filename, color_tolerance_list))
        if not output_configs:
            return 'Please enter at least one output filename and color.', 400
        image = Image.open(file.stream)
        arr = np.array(image.convert('RGBA'))
        rgb_arr = arr[..., :3]
        height, width = arr.shape[:2]
        output_images = []
        for _ in output_configs:
            output_images.append(np.ones((height, width, 4), dtype=np.uint8) * 255)
        flat_rgb = rgb_arr.reshape(-1, 3)
        for i, (filename, color_tolerance_list) in enumerate(output_configs):
            mask = np.zeros(flat_rgb.shape[0], dtype=bool)
            for color, tol in color_tolerance_list:
                color = np.array(color)
                dist = np.linalg.norm(flat_rgb - color, axis=1)
                mask |= dist <= tol
            out_img = output_images[i].reshape(-1, 4)
            out_img[mask, :3] = 0
            out_img[~mask, :3] = 255
            out_img[:, 3] = 255
        import zipfile
        import tempfile
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, 'w') as zf:
            for (filename, _), out_img in zip(output_configs, output_images):
                img_io = io.BytesIO()
                Image.fromarray(out_img).save(img_io, 'PNG')
                img_io.seek(0)
                zf.writestr(filename, img_io.read())
        zip_io.seek(0)
        return send_file(zip_io, mimetype='application/zip', as_attachment=True, download_name='outputs.zip')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
