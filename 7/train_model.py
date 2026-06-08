import os
import json
import numpy as np
from PIL import Image

CLASS_NAMES = ['可回收', '厨余', '有害', '其他']
IMG_SIZE = (224, 224)

def extract_features(img_path):
    try:
        img = Image.open(img_path).convert('RGB')
        img = img.resize(IMG_SIZE)
        img_array = np.array(img, dtype=np.float64)
        
        features = []
        
        hist_r = np.histogram(img_array[:,:,0], bins=32, range=(0,256))[0]
        hist_g = np.histogram(img_array[:,:,1], bins=32, range=(0,256))[0]
        hist_b = np.histogram(img_array[:,:,2], bins=32, range=(0,256))[0]
        
        hist_r = hist_r / (hist_r.sum() + 1e-7)
        hist_g = hist_g / (hist_g.sum() + 1e-7)
        hist_b = hist_b / (hist_b.sum() + 1e-7)
        
        features.extend(hist_r)
        features.extend(hist_g)
        features.extend(hist_b)
        
        gray = np.mean(img_array, axis=2)
        dx = np.diff(gray, axis=1)
        dy = np.diff(gray, axis=0)
        edge_density = (np.abs(dx).sum() + np.abs(dy).sum()) / (dx.size + dy.size + 1e-7)
        features.append(edge_density)
        
        mean_r = np.mean(img_array[:,:,0])
        mean_g = np.mean(img_array[:,:,1])
        mean_b = np.mean(img_array[:,:,2])
        std_r = np.std(img_array[:,:,0])
        std_g = np.std(img_array[:,:,1])
        std_b = np.std(img_array[:,:,2])
        features.extend([mean_r, mean_g, mean_b, std_r, std_g, std_b])
        
        h, w = gray.shape
        quadrants = [
            gray[:h//2, :w//2],
            gray[:h//2, w//2:],
            gray[h//2:, :w//2],
            gray[h//2:, w//2:]
        ]
        for q in quadrants:
            features.append(np.mean(q))
            features.append(np.std(q))
        
        features = np.array(features, dtype=np.float64)
        norm = np.linalg.norm(features)
        if norm > 0:
            features = features / norm
        
        return features
    except Exception as e:
        print(f"特征提取失败 {img_path}: {e}")
        return None

def train_model():
    train_dir = 'data/train'
    
    if not os.path.exists(train_dir):
        print(f"训练数据目录不存在: {train_dir}")
        return None
    
    all_features = []
    all_labels = []
    class_centroids = {}
    class_feature_lists = {}
    
    for class_name in CLASS_NAMES:
        class_dir = os.path.join(train_dir, class_name)
        if not os.path.isdir(class_dir):
            print(f"警告: 类别目录不存在: {class_dir}")
            class_centroids[class_name] = np.zeros(118)
            class_feature_lists[class_name] = []
            continue
        
        class_features = []
        img_files = [f for f in os.listdir(class_dir) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        for img_name in img_files:
            img_path = os.path.join(class_dir, img_name)
            feat = extract_features(img_path)
            if feat is not None:
                all_features.append(feat)
                all_labels.append(class_name)
                class_features.append(feat)
                print(f"  已处理: {img_path}")
        
        if class_features:
            class_centroids[class_name] = np.mean(class_features, axis=0)
            class_feature_lists[class_name] = class_features
        else:
            class_centroids[class_name] = np.zeros(118)
            class_feature_lists[class_name] = []
    
    if not all_features:
        print("没有找到训练数据，创建默认模型")
        for class_name in CLASS_NAMES:
            class_centroids[class_name] = np.zeros(118)
    
    for name, centroid in class_centroids.items():
        norm = np.linalg.norm(centroid)
        if norm > 0:
            class_centroids[name] = centroid / norm
    
    os.makedirs('models', exist_ok=True)
    
    model_data = {
        'class_centroids': {k: v.tolist() for k, v in class_centroids.items()},
        'class_names': CLASS_NAMES
    }
    
    with open('models/garbage_classifier.json', 'w', encoding='utf-8') as f:
        json.dump(model_data, f, ensure_ascii=False, indent=2)
    
    print(f"模型训练完成，共 {len(all_features)} 张图片")
    print(f"模型已保存到 models/garbage_classifier.json")
    
    return model_data

if __name__ == '__main__':
    print("开始训练垃圾分类模型...")
    result = train_model()
    print("训练完成!")
