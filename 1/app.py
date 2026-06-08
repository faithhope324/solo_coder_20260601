from flask import Flask, render_template, request, jsonify
import os

from data_cleaning import load_and_clean_data, get_basic_stats
from region_aggregation import aggregate_by_pickup_region, get_region_heatmap_data, get_top_regions
from map_generator import generate_heatmap
from charts import (
    create_fare_vs_distance_scatter,
    create_fare_distribution_histogram,
    create_peak_hours_line_chart,
    create_region_bar_chart,
    create_duration_distribution_pie_chart
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

DATA_FILE_PATH = os.path.join(app.config['UPLOAD_FOLDER'], 'taxi_data.csv')
CLEANED_DF = None


def load_data_if_needed():
    global CLEANED_DF
    if CLEANED_DF is None and os.path.exists(DATA_FILE_PATH):
        CLEANED_DF = load_and_clean_data(DATA_FILE_PATH)
    return CLEANED_DF


@app.route('/')
def index():
    df = load_data_if_needed()
    
    if df is None:
        return render_template('upload.html')
    
    stats = get_basic_stats(df)
    region_stats = aggregate_by_pickup_region(df)
    heatmap_data = get_region_heatmap_data(df)
    
    generate_heatmap(heatmap_data, 'static/heatmap.html')
    
    scatter_chart = create_fare_vs_distance_scatter(df)
    histogram_chart = create_fare_distribution_histogram(df)
    line_chart = create_peak_hours_line_chart(df)
    bar_chart = create_region_bar_chart(region_stats)
    pie_chart = create_duration_distribution_pie_chart(df)
    
    top_regions = get_top_regions(df, 10)
    
    return render_template('dashboard.html',
                           stats=stats,
                           top_regions=top_regions.to_dict('records'),
                           scatter_chart=scatter_chart,
                           histogram_chart=histogram_chart,
                           line_chart=line_chart,
                           bar_chart=bar_chart,
                           pie_chart=pie_chart)


@app.route('/upload', methods=['POST'])
def upload_file():
    global CLEANED_DF
    
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and file.filename.endswith('.csv'):
        file.save(DATA_FILE_PATH)
        try:
            CLEANED_DF = load_and_clean_data(DATA_FILE_PATH)
            return jsonify({'success': True, 'message': '文件上传成功'})
        except Exception as e:
            CLEANED_DF = None
            return jsonify({'error': f'数据处理失败: {str(e)}'}), 400
    
    return jsonify({'error': '只支持CSV文件'}), 400


@app.route('/api/refresh')
def refresh_data():
    global CLEANED_DF
    if os.path.exists(DATA_FILE_PATH):
        CLEANED_DF = load_and_clean_data(DATA_FILE_PATH)
        return jsonify({'success': True})
    return jsonify({'error': '数据文件不存在'}), 400


@app.route('/api/stats')
def api_stats():
    df = load_data_if_needed()
    if df is None:
        return jsonify({'error': '无数据'}), 404
    return jsonify(get_basic_stats(df))


if __name__ == '__main__':
    if os.path.exists(DATA_FILE_PATH):
        CLEANED_DF = load_and_clean_data(DATA_FILE_PATH)
    app.run(debug=True, host='0.0.0.0', port=5001)
