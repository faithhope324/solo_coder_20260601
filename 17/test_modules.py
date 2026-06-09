from src.data_loader import load_all_data
from src.time_utils import assign_time_slots
from src.analytics import (
    analyze_time_slots,
    analyze_top_dishes,
    analyze_table_heatmap,
    analyze_daily_trend,
    get_summary_stats,
)
from src.charts import generate_all_charts

print("=" * 60)
print("测试数据加载模块...")
orders, dishes, merged = load_all_data()
merged = assign_time_slots(merged)
print(f"✓ 订单数: {len(orders)}, 菜品数: {len(dishes)}")
print(f"✓ 合并后数据: {merged.shape}")
print(f"✓ 时段分布: {merged['时段'].value_counts().to_dict()}")

print("\n" + "=" * 60)
print("测试聚合计算模块...")
slot_analysis = analyze_time_slots(merged)
print(f"✓ 时段分析:\n{slot_analysis}")

top_dishes = analyze_top_dishes(merged, top_n=5)
print(f"\n✓ Top 5 菜品:\n{top_dishes[['菜品名称', '总销量']]}")

heatmap_df, slots = analyze_table_heatmap(merged)
print(f"\n✓ 热力图数据: {heatmap_df.shape}, 时段: {slots}")

daily_trend = analyze_daily_trend(merged)
print(f"\n✓ 每日趋势: {len(daily_trend)} 天数据")

stats = get_summary_stats(merged)
print(f"\n✓ 统计摘要: {stats}")

print("\n" + "=" * 60)
print("测试图表生成模块...")
charts = generate_all_charts(merged)
print(f"✓ 图表生成成功: {list(charts.keys())}")

charts_filtered = generate_all_charts(merged, selected_slot="lunch")
print(f"✓ 筛选后图表生成成功")

print("\n" + "=" * 60)
print("所有模块测试通过！")
