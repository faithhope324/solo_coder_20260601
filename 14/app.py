import os
import pandas as pd
from flask import Flask, render_template, request, send_from_directory
from modules.data_cleaning import clean_data, filter_by_date
from modules.region_agg import assign_regions, aggregate_region_stats, get_distance_distribution
from modules.map_generator import generate_heatmap
from modules.charts import create_region_bar_chart, create_distance_histogram

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

DATA_PATH = os.path.join(DATA_DIR, 'orders.csv')
_raw_df = None
_clean_df = None


def load_data():
    global _raw_df, _clean_df
    if _clean_df is None:
        if not os.path.exists(DATA_PATH):
            from data.generate_data import main as generate_main
            generate_main()
        _raw_df = pd.read_csv(DATA_PATH)
        _clean_df = clean_data(_raw_df)
    return _clean_df


@app.context_processor
def inject_globals():
    return {'current_page': request.endpoint}


@app.route('/')
def index():
    return heatmap()


@app.route('/heatmap')
def heatmap():
    days = request.args.get('days', 'all')
    df = load_data()
    df_filtered = filter_by_date(df, days)
    df_regions, center_lat, center_lon = assign_regions(df_filtered)
    generate_heatmap(df_filtered, center_lat, center_lon, STATIC_DIR)
    order_count = len(df_filtered)
    total_fare = round(df_filtered['车费（元）'].sum(), 2)
    avg_fare = round(df_filtered['车费（元）'].mean(), 2)
    avg_distance = round(df_filtered['距离（公里）'].mean(), 2)
    return render_template('heatmap.html',
                           days=days,
                           order_count=order_count,
                           total_fare=total_fare,
                           avg_fare=avg_fare,
                           avg_distance=avg_distance)


@app.route('/region-stats')
def region_stats():
    days = request.args.get('days', 'all')
    df = load_data()
    df_filtered = filter_by_date(df, days)
    df_regions, _, _ = assign_regions(df_filtered)
    stats = aggregate_region_stats(df_regions)
    chart_json = create_region_bar_chart(stats)
    order_count = len(df_filtered)
    total_fare = round(df_filtered['车费（元）'].sum(), 2)
    avg_fare = round(df_filtered['车费（元）'].mean(), 2)
    avg_distance = round(df_filtered['距离（公里）'].mean(), 2)
    stats_list = stats.to_dict('records')
    return render_template('region_stats.html',
                           days=days,
                           stats=stats_list,
                           chart_json=chart_json,
                           order_count=order_count,
                           total_fare=total_fare,
                           avg_fare=avg_fare,
                           avg_distance=avg_distance)


@app.route('/distance-dist')
def distance_dist():
    days = request.args.get('days', 'all')
    df = load_data()
    df_filtered = filter_by_date(df, days)
    dist_df = get_distance_distribution(df_filtered)
    chart_json = create_distance_histogram(dist_df)
    order_count = len(df_filtered)
    total_fare = round(df_filtered['车费（元）'].sum(), 2)
    avg_fare = round(df_filtered['车费（元）'].mean(), 2)
    avg_distance = round(df_filtered['距离（公里）'].mean(), 2)
    dist_list = dist_df.to_dict('records')
    total_orders = dist_df['订单数'].sum()
    return render_template('distance_dist.html',
                           days=days,
                           dist_list=dist_list,
                           total_orders=total_orders,
                           chart_json=chart_json,
                           order_count=order_count,
                           total_fare=total_fare,
                           avg_fare=avg_fare,
                           avg_distance=avg_distance)


@app.route('/heatmap.html')
def serve_heatmap():
    return send_from_directory(STATIC_DIR, 'heatmap.html')


if __name__ == '__main__':
    if not os.path.exists(DATA_PATH):
        print("未找到数据文件，正在生成模拟数据...")
        from data.generate_data import main as generate_main
        generate_main()
    app.run(debug=True, port=5000)
