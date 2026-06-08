import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

STATIC_DIR = 'd:/y/project/20260601/8/static'
os.makedirs(STATIC_DIR, exist_ok=True)

sns.set_style("whitegrid")
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

FEATURE_NAMES_CN = {
    'satisfaction': '满意度',
    'evaluation': '绩效评分',
    'project_count': '项目数',
    'tenure': '工龄(年)'
}

def plot_feature_importance(importance_df, filename='feature_importance.png'):
    plt.figure(figsize=(10, 6))
    colors = sns.color_palette("viridis", len(importance_df))
    bars = plt.barh(importance_df['feature_cn'], importance_df['importance'], color=colors)
    
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2,
                f'{width:.3f}', ha='left', va='center', fontsize=10)
    
    plt.xlabel('重要性分数', fontsize=12)
    plt.ylabel('特征', fontsize=12)
    plt.title('员工离职因素 - 特征重要性排序', fontsize=14, fontweight='bold')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    
    filepath = os.path.join(STATIC_DIR, filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    return filepath

def plot_boxplot_comparison(df, filename='boxplot_comparison.png'):
    features = ['satisfaction', 'evaluation', 'project_count', 'tenure']
    feature_titles = ['满意度', '绩效评分', '项目数', '工龄(年)']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    colors = {0: '#4CAF50', 1: '#F44336'}
    
    for idx, (feature, title) in enumerate(zip(features, feature_titles)):
        ax = axes[idx]
        sns.boxplot(x='left', y=feature, data=df, palette=colors, ax=ax, hue='left', legend=False)
        ax.set_xlabel('')
        ax.set_ylabel(title, fontsize=11)
        ax.set_title(f'{title} - 离职vs未离职', fontsize=12, fontweight='bold')
        ax.set_xticks([0, 1])
        ax.set_xticklabels(['未离职', '离职'])
        
        for i, label in enumerate(['未离职', '离职']):
            median_val = df[df['left'] == i][feature].median()
            ax.text(i, median_val, f'{median_val:.2f}', 
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.suptitle('离职与未离职人群的特征分布对比', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    filepath = os.path.join(STATIC_DIR, filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    return filepath

def generate_all_visualizations(df, importance_df):
    imp_path = plot_feature_importance(importance_df)
    box_path = plot_boxplot_comparison(df)
    return {'importance_plot': imp_path, 'boxplot_plot': box_path}

if __name__ == '__main__':
    from data_preprocessing import load_data, preprocess_data, split_data
    from model_training import train_random_forest
    from feature_importance import get_feature_importance
    
    df = load_data()
    X, y = preprocess_data(df)
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    rf_model = train_random_forest(X_train, y_train)
    importance_df = get_feature_importance(rf_model, X.columns)
    
    print("生成可视化图表...")
    paths = generate_all_visualizations(df, importance_df)
    print(f"特征重要性图: {paths['importance_plot']}")
    print(f"箱线图对比: {paths['boxplot_plot']}")
