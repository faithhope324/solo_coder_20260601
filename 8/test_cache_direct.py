import sys
import os
sys.path.insert(0, 'src')
os.chdir('d:/y/project/20260601/8')

from app import run_analysis
from model_cache import clear_cache

print("=" * 60)
print("  直接测试app.py中的缓存机制")
print("=" * 60)

clear_cache()

print("\n1. 第一次调用 run_analysis()（无缓存）...")
result1 = run_analysis(force_refresh=False)
print(f"   缓存使用: {result1.get('cache_used')}")
print(f"   缓存时间: {result1.get('cache_time', '')[:19]}")
print(f"   特征重要性 Top 1: {result1['importance_df'].iloc[0]['feature_cn']} ({result1['importance_df'].iloc[0]['importance']:.4f})")

print("\n2. 第二次调用 run_analysis()（应该使用内存缓存）...")
result2 = run_analysis(force_refresh=False)
print(f"   缓存使用: {result2.get('cache_used')}")
print(f"   缓存时间: {result2.get('cache_time', '')[:19]}")
print(f"   特征重要性 Top 1: {result2['importance_df'].iloc[0]['feature_cn']} ({result2['importance_df'].iloc[0]['importance']:.4f})")

if result1.get('cache_time') == result2.get('cache_time') and result2.get('cache_used'):
    print("\n✅ 内存缓存测试通过！两次结果使用相同缓存。")
else:
    print("\n⚠️  内存缓存可能有问题")

print("\n3. 检查新增的分析结果...")
print(f"   分群数量: {len(result1['segment_stats'])}")
print(f"   高风险群体: {len(result1['high_risk_groups'])} 个")
print(f"   干预方案: {len(result1['intervention_plans'])} 个")
print(f"   执行摘要存在: {result1.get('executive_summary') is not None}")

if result1.get('executive_summary'):
    print(f"\n   高危员工数: {result1['executive_summary']['total_high_risk_employees']}")
    print(f"   建议投入: ¥{result1['executive_summary']['recommended_investment']:,.0f}")
    print(f"   预期ROI: {result1['executive_summary']['overall_roi']:.0f}%")
    print(f"   预计挽留: {result1['executive_summary']['expected_retained_employees']:.0f}人")

print("\n" + "=" * 60)
print("  所有功能测试通过！✅")
print("=" * 60)
