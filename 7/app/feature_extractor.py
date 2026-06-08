import os
import json
import numpy as np
from PIL import Image

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

class ImageRetrieval:
    def __init__(self, index_path='models/feature_index.json'):
        self.index_path = index_path
        self.features = np.array([])
        self.image_paths = []
        self.labels = []
        self.load_index()
    
    def build_index(self, image_dir):
        all_features = []
        self.image_paths = []
        self.labels = []
        
        for class_name in os.listdir(image_dir):
            class_path = os.path.join(image_dir, class_name)
            if not os.path.isdir(class_path):
                continue
            
            for img_name in os.listdir(class_path):
                if not img_name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    continue
                
                img_path = os.path.join(class_path, img_name)
                feature = extract_features(img_path)
                
                if feature is not None:
                    all_features.append(feature.tolist())
                    self.image_paths.append(img_path)
                    self.labels.append(class_name)
                    print(f"已索引: {img_path}")
        
        self.features = np.array(all_features) if all_features else np.array([])
        self.save_index()
        print(f"索引构建完成，共 {len(self.features)} 张图片")
    
    def save_index(self):
        index_data = {
            'features': self.features.tolist() if len(self.features) > 0 else [],
            'image_paths': self.image_paths,
            'labels': self.labels
        }
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False)
    
    def load_index(self):
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                
                features_list = index_data.get('features', [])
                self.features = np.array(features_list) if features_list else np.array([])
                self.image_paths = index_data.get('image_paths', [])
                self.labels = index_data.get('labels', [])
                print(f"加载索引成功，共 {len(self.features)} 张图片")
            except Exception as e:
                print(f"加载索引失败: {e}")
                self.features = np.array([])
                self.image_paths = []
                self.labels = []
        else:
            print("索引文件不存在，需要先构建索引")
    
    def search(self, query_img_path, top_k=5):
        if len(self.features) == 0:
            return []
        
        query_feature = extract_features(query_img_path)
        if query_feature is None:
            return []
        
        query_norm = np.linalg.norm(query_feature)
        if query_norm == 0:
            return []
        
        similarities = []
        for i in range(len(self.features)):
            feat = self.features[i]
            feat_norm = np.linalg.norm(feat)
            if feat_norm > 0:
                sim = np.dot(query_feature, feat) / (query_norm * feat_norm)
            else:
                sim = 0.0
            similarities.append(float(sim))
        
        similarities = np.array(similarities)
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'image_path': self.image_paths[idx],
                'similarity': float(similarities[idx]),
                'label': self.labels[idx] if idx < len(self.labels) else 'unknown'
            })
        
        return results

if __name__ == '__main__':
    retrieval = ImageRetrieval()
    
    if os.path.exists('data/train'):
        retrieval.build_index('data/train')
