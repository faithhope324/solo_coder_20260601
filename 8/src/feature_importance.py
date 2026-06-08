import pandas as pd
import numpy as np

FEATURE_NAMES_CN = {
    'satisfaction': '满意度',
    'evaluation': '绩效评分',
    'project_count': '项目数',
    'tenure': '工龄(年)'
}

def get_feature_importance(model, feature_names):
    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'feature_cn': [FEATURE_NAMES_CN.get(f, f) for f in feature_names],
        'importance': importances
    })
    importance_df = importance_df.sort_values('importance', ascending=False).reset_index(drop=True)
    return importance_df

def get_top_features(importance_df, top_n=3):
    return importance_df.head(top_n)

if __name__ == '__main__':
    from data_preprocessing import load_data, preprocess_data, split_data
    from model_training import train_random_forest
    
    df = load_data()
    X, y = preprocess_data(df)
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    rf_model = train_random_forest(X_train, y_train)
    importance_df = get_feature_importance(rf_model, X.columns)
    
    print("特征重要性:")
    print(importance_df)
    print("\nTop 3 重要特征:")
    print(get_top_features(importance_df, 3))
