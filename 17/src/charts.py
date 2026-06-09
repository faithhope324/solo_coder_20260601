import plotly.graph_objects as go
import plotly.io as pio
from .time_utils import SLOT_NAME_MAP, SLOT_COLOR_MAP, SLOT_ORDER
from .analytics import (
    analyze_time_slots,
    analyze_top_dishes,
    analyze_table_heatmap,
    analyze_daily_trend,
)

pio.templates.default = "plotly_white"


def _base_layout(title, height=450):
    return dict(
        title=dict(text=title, x=0.5, font=dict(size=16)),
        margin=dict(l=50, r=30, t=60, b=50),
        height=height,
        hovermode="x unified",
        font=dict(family="Microsoft YaHei, sans-serif"),
    )


def create_time_slot_chart(slot_analysis, selected_slot=None):
    slot_names = [SLOT_NAME_MAP[s] for s in slot_analysis["时段"]]
    colors = [
        SLOT_COLOR_MAP[s] if s != selected_slot else "#FFD93D"
        for s in slot_analysis["时段"]
    ]
    line_widths = [3 if s == selected_slot else 0 for s in slot_analysis["时段"]]

    trace1 = go.Bar(
        x=slot_names,
        y=slot_analysis["占比"] * 100,
        name="订单量占比 (%)",
        marker=dict(color=colors, line=dict(color="#333", width=line_widths)),
        customdata=slot_analysis["时段"],
        hovertemplate="时段: %{x}<br>占比: %{y:.1f}%<br>订单数: %{customdata}",
    )

    trace2 = go.Scatter(
        x=slot_names,
        y=slot_analysis["平均消费"],
        name="平均消费金额 (元)",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="#2E86DE", width=3),
        marker=dict(size=10, color="#2E86DE", line=dict(color="white", width=2)),
        hovertemplate="时段: %{x}<br>平均消费: ¥%{y:.2f}",
    )

    layout = _base_layout("各时段订单量占比与平均消费")
    layout.update(
        barmode="group",
        yaxis=dict(title="订单量占比 (%)", side="left", range=[0, 100]),
        yaxis2=dict(
            title="平均消费金额 (元)",
            side="right",
            overlaying="y",
            showgrid=False,
        ),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
    )

    fig = go.Figure(data=[trace1, trace2], layout=layout)
    return pio.to_json(fig)


def create_top_dishes_chart(dish_sales, selected_slot=None):
    dish_sales_sorted = dish_sales.sort_values("总销量", ascending=True)

    category_colors = {"主食": "#54A0FF", "小吃": "#FF9F43", "饮品": "#10AC84", "甜点": "#F368E0"}
    colors = [category_colors.get(cat, "#888") for cat in dish_sales_sorted["类别"]]

    trace = go.Bar(
        y=dish_sales_sorted["菜品名称"],
        x=dish_sales_sorted["总销量"],
        orientation="h",
        marker=dict(color=colors, line=dict(color="#333", width=1)),
        customdata=dish_sales_sorted[["销售额", "类别"]],
        hovertemplate="菜品: %{y}<br>销量: %{x} 份<br>销售额: ¥%{customdata[0]:.2f}<br>类别: %{customdata[1]}",
    )

    title = "Top 10 菜品销量"
    if selected_slot:
        title += f" ({SLOT_NAME_MAP[selected_slot]})"

    layout = _base_layout(title, height=500)
    layout.update(
        xaxis=dict(title="销售数量 (份)"),
        yaxis=dict(title=""),
        showlegend=False,
    )

    fig = go.Figure(data=[trace], layout=layout)
    return pio.to_json(fig)


def create_table_heatmap(heatmap_df, slots, selected_slot=None):
    slot_names = [SLOT_NAME_MAP[s] for s in slots]
    table_labels = [f"{t}号" for t in heatmap_df["桌号"]]

    z_values = []
    for slot in slots:
        row = heatmap_df[slot].values.tolist()
        z_values.append(row)

    trace = go.Heatmap(
        z=z_values,
        x=table_labels,
        y=slot_names,
        colorscale="Reds",
        showscale=True,
        colorbar=dict(title="订单数", thickness=15),
        hovertemplate="桌号: %{x}<br>时段: %{y}<br>订单数: %{z}",
    )

    title = "各桌号不同时段订单频次热力图"
    if selected_slot:
        title += f" ({SLOT_NAME_MAP[selected_slot]})"

    layout = _base_layout(title, height=400)
    layout.update(
        xaxis=dict(title="桌号", type="category"),
        yaxis=dict(title="时段", type="category"),
    )

    fig = go.Figure(data=[trace], layout=layout)
    return pio.to_json(fig)


def create_trend_chart(daily_trend, selected_slot=None):
    weekend_mask = daily_trend["是否周末"]
    weekday_data = daily_trend[~weekend_mask]
    weekend_data = daily_trend[weekend_mask]

    traces = []

    traces.append(
        go.Scatter(
            x=weekday_data["日期标签"],
            y=weekday_data["营业额"],
            name="周中",
            mode="lines+markers",
            line=dict(color="#54A0FF", width=2),
            marker=dict(size=8, color="#54A0FF"),
            customdata=weekday_data[["周几", "订单数"]],
            hovertemplate="日期: %{x}<br>周几: %{customdata[0]}<br>营业额: ¥%{y:.2f}<br>订单数: %{customdata[1]}",
        )
    )

    traces.append(
        go.Scatter(
            x=weekend_data["日期标签"],
            y=weekend_data["营业额"],
            name="周末",
            mode="lines+markers",
            line=dict(color="#FF6B6B", width=2),
            marker=dict(size=10, color="#FF6B6B", symbol="diamond"),
            customdata=weekend_data[["周几", "订单数"]],
            hovertemplate="日期: %{x}<br>周几: %{customdata[0]}<br>营业额: ¥%{y:.2f}<br>订单数: %{customdata[1]}",
        )
    )

    title = "过去 30 天每日营业额趋势"
    if selected_slot:
        title += f" ({SLOT_NAME_MAP[selected_slot]})"

    layout = _base_layout(title, height=400)
    layout.update(
        xaxis=dict(title="日期", tickangle=-45),
        yaxis=dict(title="营业额 (元)"),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        shapes=[
            dict(
                type="line",
                x0=-0.5,
                x1=len(daily_trend) - 0.5,
                y0=daily_trend["营业额"].mean(),
                y1=daily_trend["营业额"].mean(),
                line=dict(color="#888", width=1, dash="dash"),
                name="均值",
            )
        ],
        annotations=[
            dict(
                x=len(daily_trend) - 1,
                y=daily_trend["营业额"].mean(),
                text=f"均值: ¥{daily_trend['营业额'].mean():.0f}",
                showarrow=False,
                xanchor="right",
                yanchor="bottom",
                font=dict(color="#888"),
            )
        ],
    )

    fig = go.Figure(data=traces, layout=layout)
    return pio.to_json(fig)


def generate_all_charts(merged_df, selected_slot=None):
    slot_analysis = analyze_time_slots(merged_df, slot_filter=selected_slot)
    top_dishes = analyze_top_dishes(merged_df, slot_filter=selected_slot)
    heatmap_df, slots = analyze_table_heatmap(merged_df, slot_filter=selected_slot)
    daily_trend = analyze_daily_trend(merged_df, slot_filter=selected_slot)

    return {
        "time_slot": create_time_slot_chart(slot_analysis, selected_slot),
        "top_dishes": create_top_dishes_chart(top_dishes, selected_slot),
        "heatmap": create_table_heatmap(heatmap_df, slots, selected_slot),
        "trend": create_trend_chart(daily_trend, selected_slot),
    }
