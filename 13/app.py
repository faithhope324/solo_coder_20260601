import os
import io
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from torchvision.models import ResNet18_Weights
from PIL import Image
from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'static/uploads'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

with open('breeds.json', 'r', encoding='utf-8') as f:
    BREEDS_DATA = json.load(f)['breeds']

BREEDS_MAP = {breed['id']: breed for breed in BREEDS_DATA}
NUM_CLASSES = len(BREEDS_DATA)

data_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])


def load_model():
    model = models.resnet18(weights=ResNet18_Weights.DEFAULT)
    num_ftrs = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(num_ftrs, 512),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(512, NUM_CLASSES)
    )

    model_path = None
    for p in ['./models/dog_breed_resnet18_finetuned.pth', './models/dog_breed_resnet18.pth']:
        if os.path.exists(p):
            model_path = p
            break

    if model_path:
        print(f'Loading model from: {model_path}')
        state_dict = torch.load(model_path, map_location=device)
        model.load_state_dict(state_dict)
    else:
        print('Warning: No trained model found. Using pre-trained weights with random classifier.')
        print('Run train.py first to train the model for better accuracy.')

    model = model.to(device)
    model.eval()
    return model


MODEL = load_model()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img_tensor = data_transform(img).unsqueeze(0)
    return img_tensor


def predict_breed(image_bytes, top_k=3):
    img_tensor = preprocess_image(image_bytes).to(device)

    with torch.no_grad():
        outputs = MODEL(img_tensor)
        probabilities = F.softmax(outputs, dim=1)
        top_probs, top_indices = torch.topk(probabilities, top_k, dim=1)

    results = []
    for i in range(top_k):
        idx = top_indices[0][i].item()
        prob = top_probs[0][i].item()

        breed_info = BREEDS_MAP.get(idx, {
            'name': f'Unknown_{idx}',
            'name_en': f'Unknown_{idx}',
            'description': '未知品种',
            'origin': '未知',
            'lifespan': '未知',
            'temperament': '未知'
        })

        results.append({
            'rank': i + 1,
            'breed_id': idx,
            'name': breed_info['name'],
            'name_en': breed_info['name_en'],
            'confidence': round(prob * 100, 2),
            'origin': breed_info.get('origin', ''),
            'lifespan': breed_info.get('lifespan', ''),
            'temperament': breed_info.get('temperament', ''),
            'description': breed_info.get('description', '')
        })

    return results


@app.route('/')
def index():
    return render_template('index.html', breeds=BREEDS_DATA)


@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    try:
        img_bytes = file.read()
        predictions = predict_breed(img_bytes, top_k=3)

        file.seek(0)
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        image_url = url_for('static', filename=f'uploads/{filename}')

        return jsonify({
            'success': True,
            'predictions': predictions,
            'image_url': image_url
        })

    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


@app.route('/api/predict', methods=['POST'])
def api_predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        img_bytes = file.read()
        predictions = predict_breed(img_bytes, top_k=3)

        return jsonify({
            'success': True,
            'predictions': predictions
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/breeds', methods=['GET'])
def api_breeds():
    return jsonify({'success': True, 'breeds': BREEDS_DATA})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
