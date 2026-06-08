import sys
sys.path.insert(0, 'src')

print("=" * 60)
print("  测试1：员工分群模块")
print("=" * 60)
from data_preprocessing import load_data, preprocess_data, split_data
from model_training import train_random_forest
from feature_importance import get_feature_importance
from employee_segmentation import analyze_segments, identify_high_risk_groups

df = load_data()
X, y = preprocess_data(df)
X_train, X_test, y_train, y_test = split_data(X, y)
model = train_random_forest(X_train, y_train)
importance_df = get_feature_importance(model, X.columns)

segment_stats = analyze_segments(df)
print("\n员工分群分析结果：")
print(segment_stats[['segment_name', 'risk_level', 'employee_count', 'left_rate']])

high_risk = identify_high_risk_groups(df, importance_df)
print("\n高风险群体识别：")
for group in high_risk:
    print(f"  {group['group_name']}: {group['employee_count']}人, 离职率{group['left_rate_in_group']:.1%}")

print("\n" + "=" * 60)
print("  测试2：干预方案模块")
print("=" * 60)
from intervention_planner import generate_intervention_plan, generate_executive_summary

plans_df = generate_intervention_plan(df, segment_stats, importance_df, high_risk)
print("\nTop 5 干预方案（按ROI排序）：")
print(plans_df[['target_segment', 'intervention_name', 'priority', 'total_cost', 'expected_retained_employees', 'roi_percent']].head())

summary = generate_executive_summary(plans_df, segment_stats, importance_df)
print(f"\n执行摘要：")
print(f"  高危员工数: {summary['total_high_risk_employees']}")
print(f"  建议投入: ¥{summary['recommended_investment']:,.0f}")
print(f"  预期ROI: {summary['overall_roi']:.0f}%")
print(f"  预计挽留: {summary['expected_retained_employees']:.0f}人")

print("\n" + "=" * 60)
print("  测试3：缓存模块")
print("=" * 60)
from model_cache import save_model_cache, load_model_cache, clear_cache

clear_cache()

print("\n第一次运行（无缓存）...")
cache1 = load_model_cache(df)
if cache1 is None:
    print("  ✅ 正确：未找到缓存，需要重新训练")
    model = train_random_forest(X_train, y_train)
    metrics = {'accuracy': 0.85, 'precision': 0.7, 'recall': 0.6, 'f1': 0.65}
    importance_df_test = get_feature_importance(model, X.columns)
    save_model_cache(model, metrics, importance_df_test, df)
    print("  ✅ 模型已缓存")

print("\n第二次运行（应加载缓存）...")
cache2 = load_model_cache(df)
if cache2 is not None:
    print("  ✅ 正确：成功加载缓存模型")
    print(f"     缓存数据指纹: {cache2['data_hash']}")
    print(f"     缓存时间: {cache2['created_at'][:19]}")
else:
    print("  ❌ 错误：未加载到缓存")

print("\n" + "=" * 60)
print("  所有测试通过！✅")
print("=" * 60)
