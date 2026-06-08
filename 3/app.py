import os
import uuid
import csv
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import cv2
import traceback

from plate_detector import PlateDetector
from ocr_recognizer import OCRRecognizer

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULT_FOLDER'] = 'static/results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'bmp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

try:
    detector = PlateDetector()
    recognizer = OCRRecognizer()
    print("✓ Models loaded successfully")
except Exception as e:
    print(f"Error loading models: {e}")
    detector = None
    recognizer = None


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {e}")
    app.logger.error(traceback.format_exc())
    return jsonify({'error': str(e)}), 500


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def generate_unique_filename(original_filename):
    ext = original_filename.rsplit('.', 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"


def process_single_image(image_path):
    try:
        if detector is None or recognizer is None:
            return {
                'success': False,
                'plate_number': '',
                'confidence': 0,
                'original_image': image_path,
                'result_image': image_path,
                'plate_box': None,
                'error': 'Models not loaded'
            }
        
        plate_region, plate_box, original_image = detector.detect_plate(image_path)
        
        if original_image is None:
            return {
                'success': False,
                'plate_number': '',
                'confidence': 0,
                'original_image': image_path,
                'result_image': image_path,
                'plate_box': None,
                'error': 'Cannot read image'
            }
        
        if plate_region is not None and plate_box is not None:
            plate_text, confidence = recognizer.recognize(plate_region)
            
            result_image = detector.draw_plate_box(original_image, plate_box, plate_text if confidence > 0.5 else "")
            
            result_filename = generate_unique_filename(os.path.basename(image_path))
            result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
            cv2.imwrite(result_path, result_image)
            
            return {
                'success': True,
                'plate_number': plate_text,
                'confidence': round(confidence * 100, 2),
                'original_image': image_path,
                'result_image': result_path,
                'plate_box': plate_box
            }
        else:
            return {
                'success': False,
                'plate_number': '',
                'confidence': 0,
                'original_image': image_path,
                'result_image': image_path,
                'plate_box': None
            }
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        traceback.print_exc()
        return {
            'success': False,
            'plate_number': '',
            'confidence': 0,
            'original_image': image_path,
            'result_image': image_path,
            'plate_box': None,
            'error': str(e)
        }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        results = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = generate_unique_filename(filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                
                result = process_single_image(filepath)
                result['filename'] = filename
                results.append(result)
        
        success_count = sum(1 for r in results if r['success'])
        failed_count = len(results) - success_count
        csv_filename = None
        
        if len(results) > 1:
            csv_filename = save_results_to_csv(results)
        
        return render_template('result.html', 
                             results=results, 
                             is_batch=(len(results) > 1), 
                             csv_file=csv_filename,
                             total_count=len(results),
                             success_count=success_count,
                             failed_count=failed_count)
    except Exception as e:
        print(f"Upload error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def save_results_to_csv(results):
    csv_filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = os.path.join(app.config['RESULT_FOLDER'], csv_filename)
    
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['序号', '文件名', '车牌号码', '置信度(%)', '识别状态'])
        
        for idx, result in enumerate(results, 1):
            writer.writerow([
                idx,
                result['filename'],
                result['plate_number'],
                result['confidence'],
                '成功' if result['success'] else '未识别'
            ])
    
    return csv_filename


@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(app.config['RESULT_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/recognize', methods=['POST'])
def api_recognize():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        result = process_single_image(filepath)
        return jsonify(result)
    
    return jsonify({'error': 'Invalid file type'}), 400


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
