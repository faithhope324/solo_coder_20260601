import requests
import time
import json

print("=" * 60)
print("测试Flask API缓存功能")
print("=" * 60)

try:
    print("\n第一次访问（应该重新分析）...")
    r1 = requests.get('http://127.0.0.1:5000/api/analysis')
    d1 = r1.json()
    print(f"  缓存使用: {d1.get('cache_used')}")
    print(f"  缓存时间: {d1.get('cache_time', '')[:19]}")
    print(f"  模型准确率: {d1['metrics']['accuracy']:.2%}")
    
    print("\n等待2秒后第二次访问（应该使用缓存）...")
    time.sleep(2)
    
    r2 = requests.get('http://127.0.0.1:5000/api/analysis')
    d2 = r2.json()
    print(f"  缓存使用: {d2.get('cache_used')}")
    print(f"  缓存时间: {d2.get('cache_time', '')[:19]}")
    print(f"  模型准确率: {d2['metrics']['accuracy']:.2%}")
    
    if d2.get('cache_used') == True:
        print("\n✅ 缓存测试通过！第二次访问使用了缓存。")
    else:
        print("\n⚠️  注意：第二次访问也重新分析了（可能数据变化了）")
    
    print("\n缓存时间对比:")
    print(f"  第一次: {d1.get('cache_time', '')[:19]}")
    print(f"  第二次: {d2.get('cache_time', '')[:19]}")
    if d1.get('cache_time') == d2.get('cache_time'):
        print("  ✅ 缓存时间相同，确认使用缓存")
    
    print("\n测试强制刷新...")
    r3 = requests.get('http://127.0.0.1:5000/refresh')
    print(f"  刷新结果: {r3.json()}")
    
    print("\n刷新后再次访问（应该重新分析）...")
    r4 = requests.get('http://127.0.0.1:5000/api/analysis')
    d4 = r4.json()
    print(f"  缓存使用: {d4.get('cache_used')}")
    print(f"  缓存时间: {d4.get('cache_time', '')[:19]}")
    
    if d4.get('cache_time') != d2.get('cache_time'):
        print("  ✅ 缓存已刷新，时间不同")
    
    print("\n" + "=" * 60)
    print("缓存功能测试完成！")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
