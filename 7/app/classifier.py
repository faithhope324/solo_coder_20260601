import os
import json
import numpy as np
from PIL import Image

CLASS_NAMES = ['可回收', '厨余', '有害', '其他']
CLASS_DESCRIPTIONS = {
    '可回收': '可回收物是指适宜回收利用和资源化利用的生活废弃物，如废纸、塑料、玻璃、金属和布料等。',
    '厨余': '厨余垃圾是指居民日常生活及食品加工、饮食服务、单位供餐等活动中产生的垃圾，包括丢弃不用的菜叶、剩菜、剩饭、果皮、蛋壳、茶渣、骨头等。',
    '有害': '有害垃圾是指对人体健康或者自然环境造成直接或潜在危害的废弃物，需要特殊安全处理，包括废电池、废荧光灯管、废灯泡、废水银温度计、废油漆桶、过期药品等。',
    '其他': '其他垃圾是指除上述几类垃圾之外的难以回收的废弃物，如砖瓦陶瓷、渣土、卫生间废纸、纸巾等。'
}
CLASS_COLORS = {
    '可回收': '#2196F3',
    '厨余': '#4CAF50',
    '有害': '#f44336',
    '其他': '#9E9E9E'
}

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
        print(f"特征提取失败: {e}")
        return None

class GarbageClassifier:
    def __init__(self, model_path='models/garbage_classifier.json'):
        self.model_path = model_path
        self.class_centroids = {}
        self.class_names = CLASS_NAMES
        self.load_model()
    
    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'r', encoding='utf-8') as f:
                    model_data = json.load(f)
                
                self.class_centroids = {}
                for k, v in model_data.get('class_centroids', {}).items():
                    self.class_centroids[k] = np.array(v)
                self.class_names = model_data.get('class_names', CLASS_NAMES)
                print(f"模型加载成功: {self.model_path}")
            except Exception as e:
                print(f"模型加载失败: {e}")
                self._init_default_centroids()
        else:
            print(f"模型文件不存在: {self.model_path}")
            self._init_default_centroids()
    
    def _init_default_centroids(self):
        for name in CLASS_NAMES:
            self.class_centroids[name] = np.zeros(118)
    
    def predict(self, img_path):
        features = extract_features(img_path)
        if features is None:
            return None
        
        if not self.class_centroids:
            return None
        
        similarities = {}
        for class_name, centroid in self.class_centroids.items():
            centroid_norm = np.linalg.norm(centroid)
            feat_norm = np.linalg.norm(features)
            if centroid_norm > 0 and feat_norm > 0:
                sim = np.dot(features, centroid) / (feat_norm * centroid_norm)
            else:
                sim = 0.0
            similarities[class_name] = sim
        
        min_sim = min(similarities.values())
        shifted = {k: v - min_sim for k, v in similarities.items()}
        total = sum(shifted.values())
        
        if total > 0:
            probs = {k: v / total for k, v in shifted.items()}
        else:
            probs = {k: 0.25 for k in CLASS_NAMES}
        
        sorted_classes = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for class_name, confidence in sorted_classes:
            results.append({
                'class': class_name,
                'confidence': round(confidence, 4),
                'description': CLASS_DESCRIPTIONS[class_name],
                'color': CLASS_COLORS[class_name]
            })
        
        return results
    
    def predict_top1(self, img_path):
        results = self.predict(img_path)
        if results:
            return results[0]
        return None

if __name__ == '__main__':
    classifier = GarbageClassifier()
    print("分类器初始化完成")
