import pandas as pd
from .time_utils import SLOT_ORDER, assign_time_slots


def analyze_time_slots(merged_df, slot_filter=None):
    df = merged_df.copy()
    if slot_filter:
        df = df[df["时段"] == slot_filter]

    order_counts = df.groupby("时段")["订单ID"].nunique().reindex(SLOT_ORDER)
    total_amount = df.groupby("时段")["订单金额"].sum().reindex(SLOT_ORDER)
    avg_amount = total_amount / order_counts.replace(0, pd.NA)

    result = pd.DataFrame(
        {
            "订单数": order_counts,
            "总金额": total_amount,
            "平均消费": avg_amount,
        }
    ).reset_index()
    result["占比"] = result["订单数"] / result["订单数"].sum()
    return result


def analyze_top_dishes(merged_df, top_n=10, slot_filter=None):
    df = merged_df.copy()
    if slot_filter:
        df = df[df["时段"] == slot_filter]

    dish_sales = (
        df.groupby(["菜品ID", "菜品名称", "类别"])
        .agg(
            总销量=("菜品数量", "sum"),
            销售额=("订单金额", "sum"),
            订单数=("订单ID", "nunique"),
        )
        .reset_index()
        .sort_values("总销量", ascending=False)
        .head(top_n)
    )
    return dish_sales


def analyze_table_heatmap(merged_df, slot_filter=None):
    df = merged_df.copy()
    if slot_filter:
        df = df[df["时段"] == slot_filter]

    table_order_counts = (
        df.groupby(["桌号", "时段"])["订单ID"].nunique().reset_index()
    )

    all_tables = list(range(1, 21))
    all_slots = [slot_filter] if slot_filter else SLOT_ORDER

    heatmap_data = []
    for table in all_tables:
        row = {"桌号": table}
        for slot in all_slots:
            val = table_order_counts[
                (table_order_counts["桌号"] == table)
                & (table_order_counts["时段"] == slot)
            ]["订单ID"].sum()
            row[slot] = int(val)
        heatmap_data.append(row)

    result_df = pd.DataFrame(heatmap_data)
    return result_df, all_slots


def analyze_daily_trend(merged_df, slot_filter=None):
    df = merged_df.copy()
    if slot_filter:
        df = df[df["时段"] == slot_filter]

    daily_sales = (
        df.groupby(["日期", "是否周末"])
        .agg(
            营业额=("订单金额", "sum"),
            订单数=("订单ID", "nunique"),
        )
        .reset_index()
        .sort_values("日期")
    )

    daily_sales["日期标签"] = pd.to_datetime(daily_sales["日期"]).dt.strftime(
        "%m-%d"
    )
    daily_sales["周几"] = pd.to_datetime(daily_sales["日期"]).dt.day_name()
    daily_sales["类型"] = daily_sales["是否周末"].map({True: "周末", False: "周中"})

    return daily_sales


def get_summary_stats(merged_df, slot_filter=None):
    df = merged_df.copy()
    if slot_filter:
        df = df[df["时段"] == slot_filter]

    total_orders = df["订单ID"].nunique()
    total_revenue = df["订单金额"].sum()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    total_items = df["菜品数量"].sum()

    return {
        "总订单数": int(total_orders),
        "总营业额": float(round(total_revenue, 2)),
        "平均客单价": float(round(avg_order_value, 2)),
        "总菜品数": int(total_items),
    }
