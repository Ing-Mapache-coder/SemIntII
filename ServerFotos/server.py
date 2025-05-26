# server.py
from flask import Flask, request, jsonify
import base64
import os
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'imagenes_recibidas'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        content = request.json
        if not content or 'image' not in content:
            return jsonify({'error': 'No se encontró la imagen en la solicitud'}), 400

        image_data = content['image']
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(UPLOAD_FOLDER, f'imagen_{timestamp}.jpg')
        
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        return jsonify({'success': True, 'file_path': file_path}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    print(f"Servidor iniciado en http://0.0.0.0:5000")