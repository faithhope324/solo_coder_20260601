from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os

MODEL_DIR = 'd:/y/project/20260601/8/models'
os.makedirs(MODEL_DIR, exist_ok=True)

def train_decision_tree(X_train, y_train, random_state=42, max_depth=None):
    model = DecisionTreeClassifier(random_state=random_state, max_depth=max_depth)
    model.fit(X_train, y_train)
    return model

def train_random_forest(X_train, y_train, n_estimators=100, random_state=42, max_depth=None):
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=random_state,
        max_depth=max_depth,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred)
    }
    return metrics

def save_model(model, model_name):
    path = os.path.join(MODEL_DIR, f'{model_name}.pkl')
    joblib.dump(model, path)
    return path

def load_model(model_name):
    path = os.path.join(MODEL_DIR, f'{model_name}.pkl')
    return joblib.load(path)

if __name__ == '__main__':
    from data_preprocessing import load_data, preprocess_data, split_data
    
    df = load_data()
    X, y = preprocess_data(df)
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    print("训练决策树...")
    dt_model = train_decision_tree(X_train, y_train)
    dt_metrics = evaluate_model(dt_model, X_test, y_test)
    print("决策树指标:", dt_metrics)
    
    print("\n训练随机森林...")
    rf_model = train_random_forest(X_train, y_train)
    rf_metrics = evaluate_model(rf_model, X_test, y_test)
    print("随机森林指标:", rf_metrics)
