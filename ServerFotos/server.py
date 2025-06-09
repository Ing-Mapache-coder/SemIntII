from flask import Flask, request, jsonify
import base64
import os
import cv2
import numpy as np
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'imagenes_recibidas'
REFERENCE_FOLDER = 'imagenes_referencia'
RESULTS_FOLDER = 'resultados_comparacion'

# Crear carpetas si no existen
for folder in [UPLOAD_FOLDER, REFERENCE_FOLDER, RESULTS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Cargar clasificador de rostros de OpenCV
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def extract_face_features(image_path):
    """Extrae características del rostro usando OpenCV"""
    try:
        # Leer imagen
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detectar rostros
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return None
        
        # Tomar el primer rostro detectado
        (x, y, w, h) = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        
        # Redimensionar a tamaño estándar
        face_resized = cv2.resize(face_roi, (100, 100))
        
        return face_resized
        
    except Exception as e:
        print(f"Error extrayendo características: {str(e)}")
        return None

def compare_faces_opencv(uploaded_image_path, reference_folder, threshold=0.5):
    """Compara rostros usando OpenCV (método más básico)"""
    try:
        # Extraer características de la imagen subida
        uploaded_features = extract_face_features(uploaded_image_path)
        
        if uploaded_features is None:
            return {"error": "No se detectó ningún rostro en la imagen subida"}
        
        results = []
        
        # Comparar con cada imagen de referencia
        for filename in os.listdir(reference_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                reference_path = os.path.join(reference_folder, filename)
                person_name = os.path.splitext(filename)[0]
                
                # Extraer características de la referencia
                reference_features = extract_face_features(reference_path)
                
                if reference_features is not None:
                    # Calcular similitud usando correlación
                    correlation = cv2.matchTemplate(uploaded_features, reference_features, cv2.TM_CCOEFF_NORMED)[0][0]
                    
                    # Convertir a porcentaje de similitud
                    similarity = max(0, correlation) * 100
                    is_match = correlation > threshold
                    
                    results.append({
                        "persona": person_name,
                        "es_la_misma_persona": is_match,
                        "similitud_porcentaje": round(similarity, 2),
                        "confianza": round(correlation, 3)
                    })
        
        # Ordenar por similitud (mayor a menor)
        results.sort(key=lambda x: x["similitud_porcentaje"], reverse=True)
        
        return {"resultados": results}
        
    except Exception as e:
        return {"error": f"Error en la comparación: {str(e)}"}

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
        
        # Guardar imagen
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(UPLOAD_FOLDER, f'imagen_{timestamp}.jpg')
        
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        # Verificar si hay imágenes de referencia
        reference_files = [f for f in os.listdir(REFERENCE_FOLDER) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not reference_files:
            return "⚠️ No hay imágenes de referencia para comparar.\nColoca imágenes en la carpeta 'imagenes_referencia'", 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
        # Realizar comparación facial
        comparison_result = compare_faces_opencv(file_path, REFERENCE_FOLDER)
        
        # Guardar resultado en archivo
        result_filename = f'resultado_{timestamp}.txt'
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(f"ANÁLISIS FACIAL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Imagen analizada: {file_path}\n")
            f.write(f"Método: OpenCV + Correlación\n\n")
            
            if 'error' in comparison_result:
                f.write(f"ERROR: {comparison_result['error']}\n")
            else:
                f.write("RESULTADOS DE COMPARACIÓN:\n\n")
                
                for i, resultado in enumerate(comparison_result['resultados'], 1):
                    f.write(f"{i}. Persona: {resultado['persona']}\n")
                    f.write(f"   ¿Es la misma persona?: {'SÍ' if resultado['es_la_misma_persona'] else 'NO'}\n")
                    f.write(f"   Similitud: {resultado['similitud_porcentaje']}%\n")
                    f.write(f"   Confianza: {resultado['confianza']}\n\n")
                
                # Mejor resultado
                if comparison_result['resultados']:
                    mejor = comparison_result['resultados'][0]
                    f.write("CONCLUSIÓN:\n")
                    if mejor['es_la_misma_persona']:
                        f.write(f"✅ La persona en la imagen PODRÍA SER {mejor['persona']}\n")
                        f.write(f"   Similitud: {mejor['similitud_porcentaje']}%\n")
                    else:
                        f.write("❌ La persona NO coincide claramente con ninguna referencia\n")
                        f.write(f"   Mayor similitud: {mejor['persona']} ({mejor['similitud_porcentaje']}%)\n")
        
        # Generar respuesta en texto plano
        response_text = f"✅ Análisis completado\n\n"
        response_text += f"📁 Imagen guardada: {file_path}\n"
        response_text += f"📄 Resultado guardado: {result_path}\n\n"
        
        if 'error' in comparison_result:
            response_text += f"❌ Error: {comparison_result['error']}"
        elif comparison_result['resultados']:
            mejor_resultado = comparison_result['resultados'][0]
            if mejor_resultado['es_la_misma_persona']:
                response_text += f"🎯 RESULTADO: Podría ser {mejor_resultado['persona']} (similitud: {mejor_resultado['similitud_porcentaje']}%)\n"
            else:
                response_text += f"❌ RESULTADO: No hay coincidencia clara\n"
                response_text += f"📊 Mayor similitud: {mejor_resultado['persona']} ({mejor_resultado['similitud_porcentaje']}%)"
        else:
            response_text += "❌ No se pudieron procesar las imágenes de referencia"
        
        return response_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    except Exception as e:
        return f"❌ Error: {str(e)}", 500, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/add_reference', methods=['POST'])
def add_reference():
    """Endpoint para agregar nuevas imágenes de referencia"""
    try:
        content = request.json
        if not content or 'image' not in content or 'name' not in content:
            return "❌ Error: Se requiere imagen y nombre", 400, {'Content-Type': 'text/plain; charset=utf-8'}

        image_data = content['image']
        person_name = content['name']
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Guardar como imagen de referencia
        file_path = os.path.join(REFERENCE_FOLDER, f'{person_name}.jpg')
        
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        # Verificar que se puede detectar un rostro
        features = extract_face_features(file_path)
        if features is None:
            os.remove(file_path)
            return "❌ Error: No se detectó ningún rostro en la imagen de referencia", 400, {'Content-Type': 'text/plain; charset=utf-8'}
        
        return f"✅ Imagen de referencia para '{person_name}' agregada correctamente", 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        return f"❌ Error: {str(e)}", 500, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/list_references', methods=['GET'])
def list_references():
    """Lista todas las imágenes de referencia disponibles"""
    try:
        references = []
        for filename in os.listdir(REFERENCE_FOLDER):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                person_name = os.path.splitext(filename)[0]
                references.append(person_name)
        
        if references:
            response_text = f"📋 Personas de referencia ({len(references)}):\n\n"
            for i, name in enumerate(references, 1):
                response_text += f"{i}. {name}\n"
        else:
            response_text = "📋 No hay imágenes de referencia registradas"
        
        return response_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        return f"❌ Error: {str(e)}", 500, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    print("=== Servidor de Reconocimiento Facial (OpenCV) ===")
    print("\nEndpoints disponibles:")
    print("- POST /upload: Subir imagen y comparar con referencias")
    print("- POST /add_reference: Agregar nueva imagen de referencia")
    print("- GET /list_references: Listar imágenes de referencia")
    print(f"\nCarpetas:")
    print(f"- Imágenes recibidas: {UPLOAD_FOLDER}")
    print(f"- Imágenes de referencia: {REFERENCE_FOLDER}")
    print(f"- Resultados guardados: {RESULTS_FOLDER}")
    print("\nPara usar, coloca imágenes de referencia en 'imagenes_referencia'")
    
    app.run(host='0.0.0.0', port=5000, debug=True)