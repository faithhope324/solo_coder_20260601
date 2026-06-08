import os
import uuid
import shutil
from flask import render_template, request, jsonify, send_from_directory
from app import app, basedir
from app.classifier import GarbageClassifier
from app.feature_extractor import ImageRetrieval

classifier = GarbageClassifier(model_path=os.path.join(basedir, 'models', 'garbage_classifier.json'))
retrieval = ImageRetrieval(index_path=os.path.join(basedir, 'models', 'feature_index.json'))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_extension(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/classify', methods=['POST'])
def classify_image():
    if 'image' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        ext = get_extension(file.filename)
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        results = classifier.predict(filepath)
        
        if results is None:
            return jsonify({'error': '分类失败'}), 500
        
        return jsonify({
            'success': True,
            'image_url': f'/static/uploads/{filename}',
            'predictions': results
        })
    
    return jsonify({'error': '不支持的文件格式'}), 400

@app.route('/api/search', methods=['POST'])
def search_similar():
    if 'image' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        ext = get_extension(file.filename)
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        top_k = int(request.form.get('top_k', 5))
        similar_results = retrieval.search(filepath, top_k=top_k)
        
        similar_images = []
        for idx, result in enumerate(similar_results):
            src_path = result['image_path']
            if os.path.exists(src_path):
                dst_filename = f"{uuid.uuid4().hex}_{idx}.{get_extension(src_path)}"
                dst_path = os.path.join(app.config['SIMILAR_FOLDER'], dst_filename)
                try:
                    shutil.copy2(src_path, dst_path)
                    similar_images.append({
                        'url': f'/static/similar/{dst_filename}',
                        'similarity': result['similarity'],
                        'label': result['label']
                    })
                except:
                    pass
        
        return jsonify({
            'success': True,
            'query_image': f'/static/uploads/{filename}',
            'similar_images': similar_images
        })
    
    return jsonify({'error': '不支持的文件格式'}), 400

@app.route('/api/classify_and_search', methods=['POST'])
def classify_and_search():
    if 'image' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        ext = get_extension(file.filename)
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        top_k = int(request.form.get('top_k', 5))
        
        predictions = classifier.predict(filepath)
        similar_results = retrieval.search(filepath, top_k=top_k)
        
        similar_images = []
        for idx, result in enumerate(similar_results):
            src_path = result['image_path']
            if os.path.exists(src_path):
                dst_filename = f"{uuid.uuid4().hex}_{idx}.{get_extension(src_path)}"
                dst_path = os.path.join(app.config['SIMILAR_FOLDER'], dst_filename)
                try:
                    shutil.copy2(src_path, dst_path)
                    similar_images.append({
                        'url': f'/static/similar/{dst_filename}',
                        'similarity': result['similarity'],
                        'label': result['label']
                    })
                except:
                    pass
        
        return jsonify({
            'success': True,
            'image_url': f'/static/uploads/{filename}',
            'predictions': predictions,
            'similar_images': similar_images
        })
    
    return jsonify({'error': '不支持的文件格式'}), 400

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': len(classifier.class_centroids) > 0,
        'index_size': len(retrieval.features)
    })

