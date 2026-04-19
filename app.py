import os
import io
import sys
import webbrowser
from flask import Flask, render_template, request, send_file, url_for
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageOps 
from threading import Timer

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

app = Flask(__name__, 
            template_folder=get_resource_path('templates'),
            static_folder=get_resource_path('static'))

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

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
            # Open image with PIL
            img = Image.open(file)
            
            # Fix orientation based on EXIF (prevents sideways photos from phones)
            img = ImageOps.exif_transpose(img)
            
            # Convert to RGB if necessary (e.g. for PNG or RGBA)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save to temporary buffer for ReportLab
            img_temp = io.BytesIO()
            img.save(img_temp, format='JPEG', quality=85)
            img_temp.seek(0)
            
            # Place on canvas
            x, y = positions[page_pos]
            c.drawImage(ImageReader(img_temp), x, y, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error processing image {i}: {e}")

    c.showPage()
    c.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='Photo_to_PDF.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    # Local application settings
    host = '127.0.0.1'
    port = 5000
    
    # Auto-open browser
    url = f"http://{host}:{port}"
    Timer(1.5, lambda: webbrowser.open(url)).start()
    
    print(f"Aplikasi berjalan di {url}")
    print("Silahkan tutup jendela hitam ini untuk mematikan aplikasi.")
    
    app.run(host=host, port=port, debug=False)
