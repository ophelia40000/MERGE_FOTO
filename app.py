import os
from flask import Flask, render_template, request, send_file, url_for
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'photos' not in request.files:
        return "No files part", 400
    
    files = request.files.getlist('photos')
    if not files or files[0].filename == '':
        return "No selected files", 400

    # Create PDF in memory
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Grid settings (2x2)
    margin = 40
    padding = 20
    img_width = (width - 2 * margin - padding) / 2
    img_height = (height - 2 * margin - padding) / 2

    positions = [
        (margin, height - margin - img_height), # Top Left
        (margin + img_width + padding, height - margin - img_height), # Top Right
        (margin, height - margin - 2 * img_height - padding), # Bottom Left
        (margin + img_width + padding, height - margin - 2 * img_height - padding) # Bottom Right
    ]

    for i, file in enumerate(files):
        # New page every 4 images
        page_pos = i % 4
        if i > 0 and page_pos == 0:
            c.showPage()
        
        try:
            # Open image with PIL to handle rotation and conversion
            img = Image.open(file)
            
            # Save to temp bytes to use with reportlab
            img_temp = io.BytesIO()
            img.save(img_temp, format='JPEG')
            img_temp.seek(0)
            
            # Place on canvas
            x, y = positions[page_pos]
            c.drawImage(ImageReader(img_temp), x, y, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error processing image {i}: {e}")

    c.showPage()
    c.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='result.pdf', mimetype='application/pdf')

from reportlab.lib.utils import ImageReader

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
