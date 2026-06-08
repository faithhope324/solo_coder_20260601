import sys
import os
sys.path.insert(0, 'src')
os.chdir('d:/y/project/20260601/8')

from app import run_analysis
from model_cache import clear_cache
import importlib
import app

clear_cache()
app.cached_results = None
app.cache_timestamp = None

print("=" * 60)
print("  测试文件缓存加载 + 数据类型转换")
print("=" * 60)

print("\n1. 第一次调用（生成缓存文件）...")
result1 = run_analysis()
print("   缓存使用:", result1.get('cache_used'))

print("\n2. 清空内存缓存...")
app.cached_results = None
app.cache_timestamp = None
importlib.reload(app)

print("\n3. 第二次调用（从文件缓存加载）...")
result2 = run_analysis()
print("   缓存使用:", result2.get('cache_used'))

print("\n4. 验证数据类型...")
errors = []

segment_stats = result2['segment_stats']
for col in ['employee_count', 'left_rate', 'avg_satisfaction']:
    val = segment_stats.iloc[0][col]
    if isinstance(val, str):
        errors.append(f"  ❌ segment_stats[{col}] 是字符串: '{val}'")
    else:
        print(f"  ✅ segment_stats[{col}] = {val} ({type(val).__name__})")

plans = result2['intervention_plans']
for col in ['total_cost', 'roi_percent', 'expected_retained_employees']:
    val = plans.iloc[0][col]
    if isinstance(val, str):
        errors.append(f"  ❌ intervention_plans[{col}] 是字符串: '{val}'")
    else:
        print(f"  ✅ intervention_plans[{col}] = {val} ({type(val).__name__})")

high_risk = result2['high_risk_groups']
for key in ['employee_count', 'left_rate_in_group']:
    val = high_risk[0][key]
    if isinstance(val, str):
        errors.append(f"  ❌ high_risk_groups[0][{key}] 是字符串: '{val}'")
    else:
        print(f"  ✅ high_risk_groups[0][{key}] = {val} ({type(val).__name__})")

exec_summary = result2['executive_summary']
for key in ['recommended_investment', 'overall_roi', 'expected_retained_employees']:
    val = exec_summary.get(key)
    if isinstance(val, str):
        errors.append(f"  ❌ executive_summary[{key}] 是字符串: '{val}'")
    else:
        print(f"  ✅ executive_summary[{key}] = {val} ({type(val).__name__})")

print("\n5. 测试数值格式化（模拟模板操作）...")
try:
    test_str = f"{plans.iloc[0]['roi_percent']:.0f}%"
    print(f"  ✅ ROI格式化成功: {test_str}")
except Exception as e:
    errors.append(f"  ❌ ROI格式化失败: {e}")

try:
    test_str = f"¥{plans.iloc[0]['total_cost']:,.0f}"
    print(f"  ✅ 成本格式化成功: {test_str}")
except Exception as e:
    errors.append(f"  ❌ 成本格式化失败: {e}")

try:
    test_str = f"{segment_stats.iloc[0]['left_rate']:.1%}"
    print(f"  ✅ 离职率格式化成功: {test_str}")
except Exception as e:
    errors.append(f"  ❌ 离职率格式化失败: {e}")

print("\n" + "=" * 60)
if errors:
    print("  ❌ 发现错误:")
    for e in errors:
        print(e)
else:
    print("  ✅ 所有数据类型转换测试通过！")
print("=" * 60)
