import os
import pickle
import hashlib
import json
from datetime import datetime, timedelta

CACHE_DIR = 'd:/y/project/20260601/8/cache'
CACHE_EXPIRE_HOURS = 24
os.makedirs(CACHE_DIR, exist_ok=True)

def _get_data_hash(df):
    data_str = df.to_csv(index=False)
    return hashlib.md5(data_str.encode()).hexdigest()[:16]

def _get_cache_path(data_hash, suffix='pkl'):
    return os.path.join(CACHE_DIR, f'cache_{data_hash}.{suffix}')

def _cache_exists(data_hash, suffix='pkl'):
    path = _get_cache_path(data_hash, suffix)
    if not os.path.exists(path):
        return False
    mtime = datetime.fromtimestamp(os.path.getmtime(path))
    if datetime.now() - mtime > timedelta(hours=CACHE_EXPIRE_HOURS):
        return False
    return True

def save_model_cache(model, metrics, importance_df, df, extra_data=None):
    data_hash = _get_data_hash(df)
    model_path = _get_cache_path(data_hash, 'pkl')
    results_path = _get_cache_path(data_hash, 'json')
    
    with open(model_path, 'wb') as f:
        pickle.dump({
            'model': model,
            'importance_df': importance_df,
            'metrics': metrics,
            'data_hash': data_hash,
            'created_at': datetime.now().isoformat()
        }, f)
    
    results_data = {
        'metrics': metrics,
        'importance': importance_df.to_dict('records'),
        'data_hash': data_hash,
        'created_at': datetime.now().isoformat()
    }
    if extra_data:
        results_data.update(extra_data)
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"[缓存] 模型和结果已保存，数据指纹: {data_hash}")
    return data_hash

def load_model_cache(df):
    data_hash = _get_data_hash(df)
    
    if not _cache_exists(data_hash, 'pkl'):
        print(f"[缓存] 未找到有效缓存，数据指纹: {data_hash}")
        return None
    
    model_path = _get_cache_path(data_hash, 'pkl')
    try:
        with open(model_path, 'rb') as f:
            cache_data = pickle.load(f)
        print(f"[缓存] 成功加载缓存模型，数据指纹: {data_hash}")
        return cache_data
    except Exception as e:
        print(f"[缓存] 加载失败: {e}")
        return None

def load_results_cache(df):
    data_hash = _get_data_hash(df)
    
    if not _cache_exists(data_hash, 'json'):
        return None
    
    results_path = _get_cache_path(data_hash, 'json')
    try:
        with open(results_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[缓存] 结果加载失败: {e}")
        return None

def clear_cache():
    import shutil
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
        os.makedirs(CACHE_DIR)
        print("[缓存] 已清空所有缓存")

if __name__ == '__main__':
    from data_preprocessing import load_data, preprocess_data, split_data
    from model_training import train_random_forest, evaluate_model
    from feature_importance import get_feature_importance
    
    df = load_data()
    X, y = preprocess_data(df)
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    print("第一次运行（应该重新训练）...")
    cache = load_model_cache(df)
    if cache is None:
        model = train_random_forest(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)
        importance_df = get_feature_importance(model, X.columns)
        save_model_cache(model, metrics, importance_df, df)
    else:
        print("发现缓存，跳过训练")
    
    print("\n第二次运行（应该加载缓存）...")
    cache = load_model_cache(df)
    if cache:
        print("成功加载缓存模型！")
        print(f"模型指标: {cache['metrics']}")
