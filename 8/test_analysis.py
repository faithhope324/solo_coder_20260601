import sys
sys.path.insert(0, 'src')

from data_preprocessing import load_data, preprocess_data, split_data
from model_training import train_random_forest, evaluate_model
from feature_importance import get_feature_importance
from visualization import generate_all_visualizations

print('1. 加载数据...')
df = load_data()
print(f'   数据行数: {len(df)}')

print('2. 数据预处理...')
X, y = preprocess_data(df)
X_train, X_test, y_train, y_test = split_data(X, y)

print('3. 训练随机森林模型...')
model = train_random_forest(X_train, y_train)
print('   模型训练完成')

print('4. 模型评估...')
metrics = evaluate_model(model, X_test, y_test)
print(f'   准确率: {metrics["accuracy"]:.2%}')
print(f'   精确率: {metrics["precision"]:.2%}')
print(f'   召回率: {metrics["recall"]:.2%}')
print(f'   F1分数: {metrics["f1"]:.2%}')

print('5. 计算特征重要性...')
importance_df = get_feature_importance(model, X.columns)
print(importance_df)

print('6. 生成可视化图表...')
paths = generate_all_visualizations(df, importance_df)
print('   特征重要性图已生成')
print('   箱线图对比已生成')
print('全部完成！')
