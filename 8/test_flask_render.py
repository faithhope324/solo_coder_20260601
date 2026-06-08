import sys
import os
sys.path.insert(0, 'src')
os.chdir('d:/y/project/20260601/8')

from flask import Flask, render_template
import traceback

app = Flask(__name__, template_folder='templates')

from app import run_analysis
from model_cache import clear_cache

clear_cache()

print("=" * 60)
print("  测试Flask模板渲染")
print("=" * 60)

try:
    print("\n1. 运行分析...")
    results = run_analysis()
    print("   分析完成，结果字段:")
    for k in results.keys():
        print(f"   - {k}")
    
    print("\n2. 测试模板渲染...")
    with app.app_context():
        html = render_template('index.html', results=results)
        print(f"   ✅ 模板渲染成功！HTML长度: {len(html)} 字符")
        print(f"   包含'执行摘要': {'执行摘要' in html}")
        print(f"   包含'员工分群': {'员工分群' in html}")
        print(f"   包含'干预方案': {'干预方案' in html}")
        print(f"   包含'缓存使用': {'缓存使用' in html}")
        
    print("\n3. 检查关键数据...")
    if 'intervention_plans' in results:
        print(f"   干预方案数量: {len(results['intervention_plans'])}")
        if len(results['intervention_plans']) > 0:
            plan = results['intervention_plans'].iloc[0]
            print(f"   Top 1方案: {plan['intervention_name']}")
            print(f"   ROI: {plan['roi_percent']:.0f}%")
            print(f"   投入: ¥{plan['total_cost']:,.0f}")
    
    print("\n" + "=" * 60)
    print("  模板渲染测试通过！✅")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    traceback.print_exc()
