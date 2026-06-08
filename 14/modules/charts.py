import plotly.graph_objects as go
import plotly.io as pio
import json


def create_region_bar_chart(stats_df):
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=stats_df['区域'],
        y=stats_df['平均车费'],
        name='平均车费（元）',
        marker_color='#e74c3c',
        yaxis='y',
        text=stats_df['平均车费'],
        textposition='auto'
    ))

    fig.add_trace(go.Bar(
        x=stats_df['区域'],
        y=stats_df['平均距离'],
        name='平均距离（公里）',
        marker_color='#3498db',
        yaxis='y2',
        text=stats_df['平均距离'],
        textposition='auto'
    ))

    fig.update_layout(
        title='各区域平均车费与平均距离',
        barmode='group',
        xaxis=dict(title='区域'),
        yaxis=dict(
            title='平均车费（元）',
            side='left'
        ),
        yaxis2=dict(
            title='平均距离（公里）',
            side='right',
            overlaying='y',
            showgrid=False
        ),
        legend=dict(x=0.01, y=0.99),
        template='plotly_white',
        height=500,
        margin=dict(l=60, r=60, t=60, b=40)
    )

    graph_json = pio.to_json(fig)
    return json.loads(graph_json)


def create_distance_histogram(dist_df):
    fig = go.Figure()

    colors = ['#2ecc71', '#27ae60', '#f39c12', '#e67e22', '#e74c3c']

    fig.add_trace(go.Bar(
        x=dist_df['距离区间'],
        y=dist_df['订单数'],
        marker_color=colors,
        text=dist_df['订单数'],
        textposition='auto'
    ))

    fig.update_layout(
        title='订单距离分布',
        xaxis=dict(title='距离区间'),
        yaxis=dict(title='订单数'),
        template='plotly_white',
        height=500,
        showlegend=False,
        margin=dict(l=60, r=60, t=60, b=40)
    )

    graph_json = pio.to_json(fig)
    return json.loads(graph_json)
