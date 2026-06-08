import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import json


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        return super().default(obj)


def create_fare_vs_distance_scatter(df, sample_size=5000):
    if len(df) > sample_size:
        sample_df = df.sample(n=sample_size, random_state=42)
    else:
        sample_df = df.copy()
    
    sample_df = sample_df.dropna(subset=['trip_distance', 'fare_amount'])
    sample_df = sample_df[sample_df['trip_distance'] > 0]
    sample_df = sample_df[sample_df['fare_amount'] > 0]
    
    x_vals = sample_df['trip_distance'].values
    y_vals = sample_df['fare_amount'].values
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='markers',
        marker=dict(
            size=5,
            color=y_vals,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='车费 (元)'),
            opacity=0.5
        ),
        text=[
            f"区域: {row['pickup_region']} → {row['dropoff_region']}<br>"
            f"距离: {row['trip_distance']:.1f}公里<br>"
            f"车费: ¥{row['fare_amount']:.1f}<br>"
            f"时长: {row['trip_duration']:.0f}分钟"
            for _, row in sample_df.iterrows()
        ],
        hoverinfo='text'
    ))
    
    z = np.polyfit(x_vals, y_vals, 1)
    p = np.poly1d(z)
    x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
    fig.add_trace(go.Scatter(
        x=x_line,
        y=p(x_line),
        mode='lines',
        name='趋势线',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='车费 vs 行程距离',
        xaxis=dict(title='行程距离 (公里)', gridcolor='lightgray'),
        yaxis=dict(title='车费 (元)', gridcolor='lightgray'),
        plot_bgcolor='white',
        title_x=0.5,
        height=500,
        showlegend=True
    )
    
    return json.dumps(fig.to_dict(), cls=NumpyEncoder)


def create_fare_distribution_histogram(df):
    fare_data = df['fare_amount']
    fare_data = fare_data[fare_data < 300]
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=fare_data,
        nbinsx=40,
        marker_color='#3498db',
        opacity=0.75,
        name='车费分布'
    ))
    
    avg_fare = fare_data.mean()
    median_fare = fare_data.median()
    
    fig.add_vline(
        x=avg_fare,
        line_dash='dash',
        line_color='red',
        annotation_text=f'平均值: ¥{avg_fare:.1f}',
        annotation_position='top right'
    )
    
    fig.add_vline(
        x=median_fare,
        line_dash='dash',
        line_color='green',
        annotation_text=f'中位数: ¥{median_fare:.1f}',
        annotation_position='top left'
    )
    
    fig.update_layout(
        title='车费金额分布',
        xaxis=dict(title='车费 (元)', gridcolor='lightgray'),
        yaxis=dict(title='频次', gridcolor='lightgray'),
        plot_bgcolor='white',
        title_x=0.5,
        showlegend=False,
        height=500
    )
    
    return json.dumps(fig.to_dict(), cls=NumpyEncoder)


def create_peak_hours_line_chart(df):
    hourly_stats = df.groupby('pickup_hour').agg({
        'fare_amount': ['count', 'sum', 'mean']
    }).reset_index()
    
    hourly_stats.columns = ['hour', 'trip_count', 'total_fare', 'avg_fare']
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hourly_stats['hour'],
        y=hourly_stats['trip_count'],
        mode='lines+markers',
        name='行程数量',
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(46, 134, 171, 0.1)'
    ))
    
    fig.add_trace(go.Scatter(
        x=hourly_stats['hour'],
        y=hourly_stats['avg_fare'],
        mode='lines+markers',
        name='平均车费 (元)',
        line=dict(color='#E74C3C', width=2, dash='dot'),
        marker=dict(size=6),
        yaxis='y2'
    ))
    
    peak_hours = hourly_stats.nlargest(3, 'trip_count')['hour'].tolist()
    
    fig.update_layout(
        title='24小时行程分布与车费趋势',
        xaxis=dict(
            title='时间 (小时)',
            tickmode='linear',
            tick0=0,
            dtick=1,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='行程数量',
            gridcolor='lightgray'
        ),
        yaxis2=dict(
            title='平均车费 (元)',
            overlaying='y',
            side='right',
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        title_x=0.5,
        height=500,
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    for hour in peak_hours:
        count = hourly_stats[hourly_stats['hour'] == hour]['trip_count'].values[0]
        fig.add_annotation(
            x=hour,
            y=count,
            text=f'高峰 {hour}:00',
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40,
            font=dict(color='red')
        )
    
    return json.dumps(fig.to_dict(), cls=NumpyEncoder)


def create_region_bar_chart(region_stats, n=10):
    top_regions = region_stats.head(n)
    
    fig = px.bar(
        top_regions,
        x='region',
        y='trip_count',
        color='avg_fare',
        title=f'上车热度前{n}名区域',
        labels={
            'region': '区域',
            'trip_count': '行程数量',
            'avg_fare': '平均车费 (元)'
        },
        color_continuous_scale='RdYlBu_r'
    )
    
    fig.update_layout(
        xaxis=dict(tickangle=45, gridcolor='lightgray'),
        yaxis=dict(gridcolor='lightgray'),
        plot_bgcolor='white',
        title_x=0.5,
        height=500
    )
    
    return json.dumps(fig.to_dict(), cls=NumpyEncoder)


def create_duration_distribution_pie_chart(df):
    def classify_duration(minutes):
        if minutes <= 10:
            return '短途 (≤10分钟)'
        elif minutes <= 20:
            return '中途 (10-20分钟)'
        elif minutes <= 40:
            return '中长途 (20-40分钟)'
        else:
            return '长途 (>40分钟)'
    
    df_copy = df.copy()
    df_copy['duration_category'] = df_copy['trip_duration'].apply(classify_duration)
    
    category_counts = df_copy['duration_category'].value_counts()
    
    fig = px.pie(
        values=category_counts.values,
        names=category_counts.index,
        title='行程时长分布',
        color_discrete_sequence=['#2ECC71', '#3498DB', '#F39C12', '#E74C3C']
    )
    
    fig.update_layout(
        height=400,
        title_x=0.5
    )
    
    fig.update_traces(
        textinfo='percent+label',
        hole=0.4
    )
    
    return json.dumps(fig.to_dict(), cls=NumpyEncoder)
