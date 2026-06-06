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

from imagenet_mapping import IMAGENET_DOG_CLASS_TO_BREED

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

imagenet_normalize = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])

basic_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    imagenet_normalize,
])

tta_transforms = [
    transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        imagenet_normalize,
    ]),
    transforms.Compose([
        transforms.Resize(288),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        imagenet_normalize,
    ]),
    transforms.Compose([
        transforms.Resize(256),
        transforms.FiveCrop(224),
        transforms.Lambda(lambda crops: crops[0]),
        transforms.ToTensor(),
        imagenet_normalize,
    ]),
    transforms.Compose([
        transforms.Resize(256),
        transforms.FiveCrop(224),
        transforms.Lambda(lambda crops: crops[2]),
        transforms.ToTensor(),
        imagenet_normalize,
    ]),
    transforms.Compose([
        transforms.Resize(256),
        transforms.FiveCrop(224),
        transforms.Lambda(lambda crops: crops[4]),
        transforms.ToTensor(),
        imagenet_normalize,
    ]),
    transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.RandomHorizontalFlip(p=1.0),
        transforms.ToTensor(),
        imagenet_normalize,
    ]),
]


def check_trained_model_exists():
    for p in ['./models/dog_breed_resnet18_finetuned.pth', './models/dog_breed_resnet18.pth']:
        if os.path.exists(p):
            return p
    return None


def load_custom_model(model_path):
    model = models.resnet18(weights=ResNet18_Weights.DEFAULT)
    num_ftrs = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(num_ftrs, 512),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(512, NUM_CLASSES)
    )
    print(f'Loading trained 10-class model from: {model_path}')
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model = model.to(device)
    model.eval()
    return model, 'custom'


def load_imagenet_model():
    print('Using ImageNet pre-trained ResNet18 (1000 classes) with dog breed mapping.')
    model = models.resnet18(weights=ResNet18_Weights.DEFAULT)
    model = model.to(device)
    model.eval()
    return model, 'imagenet'


def load_model():
    model_path = check_trained_model_exists()
    if model_path:
        return load_custom_model(model_path)
    else:
        return load_imagenet_model()


MODEL, MODEL_MODE = load_model()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img_tensor = basic_transform(img).unsqueeze(0)
    return img_tensor


def preprocess_tta(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    tensors = []
    for t in tta_transforms:
        tensors.append(t(img).unsqueeze(0))
    return torch.cat(tensors, dim=0)


def aggregate_imagenet_probs(imagenet_probs):
    breed_probs = torch.zeros(NUM_CLASSES, device=imagenet_probs.device)
    for imagenet_idx, breed_id in IMAGENET_DOG_CLASS_TO_BREED.items():
        if imagenet_idx < imagenet_probs.shape[-1]:
            breed_probs[breed_id] += imagenet_probs[imagenet_idx]

    dog_total = breed_probs.sum()
    if dog_total > 0:
        breed_probs = breed_probs / dog_total

    return breed_probs


def predict_breed(image_bytes, top_k=3, use_tta=True):
    with torch.no_grad():
        if MODEL_MODE == 'imagenet':
            if use_tta:
                batch = preprocess_tta(image_bytes).to(device)
                outputs = MODEL(batch)
                probs = F.softmax(outputs, dim=1)
                avg_probs = probs.mean(dim=0)
                breed_probs = aggregate_imagenet_probs(avg_probs)
            else:
                img_tensor = preprocess_image(image_bytes).to(device)
                outputs = MODEL(img_tensor)
                probs = F.softmax(outputs, dim=1)[0]
                breed_probs = aggregate_imagenet_probs(probs)
        else:
            if use_tta:
                batch = preprocess_tta(image_bytes).to(device)
                outputs = MODEL(batch)
                probs = F.softmax(outputs, dim=1)
                breed_probs = probs.mean(dim=0)
            else:
                img_tensor = preprocess_image(image_bytes).to(device)
                outputs = MODEL(img_tensor)
                breed_probs = F.softmax(outputs, dim=1)[0]

    top_probs, top_indices = torch.topk(breed_probs, min(top_k, NUM_CLASSES))

    results = []
    for i in range(len(top_indices)):
        idx = top_indices[i].item()
        prob = top_probs[i].item()

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
            'image_url': image_url,
            'model_mode': MODEL_MODE
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
        use_tta = request.form.get('tta', 'true').lower() == 'true'
        predictions = predict_breed(img_bytes, top_k=3, use_tta=use_tta)

        return jsonify({
            'success': True,
            'predictions': predictions,
            'model_mode': MODEL_MODE
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/breeds', methods=['GET'])
def api_breeds():
    return jsonify({'success': True, 'breeds': BREEDS_DATA})


if __name__ == '__main__':
    print(f'Model mode: {MODEL_MODE}')
    app.run(debug=True, host='0.0.0.0', port=5000)
