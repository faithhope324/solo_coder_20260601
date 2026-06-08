import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, render_template, jsonify, request
import pandas as pd
from datetime import datetime

from data_preprocessing import load_data, preprocess_data, split_data, get_data_summary
from model_training import train_random_forest, evaluate_model
from feature_importance import get_feature_importance, get_top_features
from visualization import generate_all_visualizations
from model_cache import load_model_cache, save_model_cache, load_results_cache, clear_cache
from employee_segmentation import analyze_segments, identify_high_risk_groups
from intervention_planner import generate_intervention_plan, generate_executive_summary

app = Flask(__name__)

cached_results = None
cache_timestamp = None
CACHE_DURATION = 3600

def _convert_to_numeric(value):
    if value is None:
        return value
    try:
        if isinstance(value, str) and '.' in value:
            return float(value)
        return int(value) if isinstance(value, str) and value.isdigit() else value
    except (ValueError, TypeError):
        return value

def _convert_df_numeric(df, numeric_cols):
    if df.empty:
        return df
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(_convert_to_numeric)
    return df

def _convert_list_numeric(lst, numeric_keys):
    for item in lst:
        for key in numeric_keys:
            if key in item:
                item[key] = _convert_to_numeric(item[key])
    return lst

def _convert_dict_numeric(d, numeric_keys):
    for key in numeric_keys:
        if key in d:
            d[key] = _convert_to_numeric(d[key])
    if 'priority_actions' in d:
        for action in d['priority_actions']:
            for k in ['cost', 'roi']:
                if k in action:
                    action[k] = _convert_to_numeric(action[k])
    return d

def run_analysis(force_refresh=False):
    global cached_results, cache_timestamp
    
    df = load_data()
    
    if not force_refresh:
        if cached_results is not None and cache_timestamp is not None:
            if (datetime.now() - cache_timestamp).total_seconds() < CACHE_DURATION:
                print("[内存缓存] 使用内存缓存的分析结果")
                cached_results['cache_used'] = True
                return cached_results
        
        cache_data = load_model_cache(df)
        if cache_data is not None:
            print("[文件缓存] 从文件缓存加载模型和结果")
            model = cache_data['model']
            metrics = cache_data['metrics']
            importance_df = cache_data['importance_df']
            
            X, y = preprocess_data(df)
            X_train, X_test, y_train, y_test = split_data(X, y)
            
            results_cache = load_results_cache(df)
            if results_cache:
                print("[文件缓存] 从文件缓存加载完整分析结果")
                segment_stats = pd.DataFrame(results_cache.get('segment_stats', []))
                high_risk_groups = results_cache.get('high_risk_groups', [])
                intervention_plans = pd.DataFrame(results_cache.get('intervention_plans', []))
                executive_summary = results_cache.get('executive_summary', {})
                
                segment_stats = _convert_df_numeric(segment_stats, [
                    'employee_count', 'left_count', 'left_rate', 'avg_satisfaction',
                    'avg_evaluation', 'avg_project_count', 'avg_tenure'
                ])
                intervention_plans = _convert_df_numeric(intervention_plans, [
                    'target_employee_count', 'baseline_left_rate', 'duration_weeks',
                    'expected_satisfaction_lift', 'expected_retention_rate',
                    'total_cost', 'expected_retained_employees', 'expected_savings',
                    'net_benefit', 'roi_percent', 'cost_per_retention'
                ])
                high_risk_groups = _convert_list_numeric(high_risk_groups, [
                    'employee_count', 'left_count_in_group', 'left_rate_in_group',
                    'percent_of_all_left', 'avg_satisfaction', 'avg_tenure'
                ])
                executive_summary = _convert_dict_numeric(executive_summary, [
                    'total_high_risk_employees', 'total_at_risk_employees',
                    'top_feature_importance', 'recommended_investment',
                    'expected_savings', 'expected_net_benefit',
                    'expected_retained_employees', 'overall_roi'
                ])
                
                top_features = get_top_features(importance_df)
                generate_all_visualizations(df, importance_df)
                summary = get_data_summary(df)
                
                cached_results = {
                    'summary': summary,
                    'metrics': metrics,
                    'importance_df': importance_df,
                    'top_features': top_features,
                    'feature_stats': get_feature_stats(df),
                    'segment_stats': segment_stats,
                    'high_risk_groups': high_risk_groups,
                    'intervention_plans': intervention_plans,
                    'executive_summary': executive_summary,
                    'cache_time': cache_data.get('created_at', datetime.now().isoformat()),
                    'cache_used': True
                }
                cache_timestamp = datetime.now()
                return cached_results
    
    print("[缓存] 未找到有效缓存，重新执行完整分析...")
    X, y = preprocess_data(df)
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    model = train_random_forest(X_train, y_train)
    metrics = evaluate_model(model, X_test, y_test)
    
    importance_df = get_feature_importance(model, X.columns)
    top_features = get_top_features(importance_df)
    
    generate_all_visualizations(df, importance_df)
    
    segment_stats = analyze_segments(df)
    high_risk_groups = identify_high_risk_groups(df, importance_df)
    intervention_plans = generate_intervention_plan(df, segment_stats, importance_df, high_risk_groups)
    executive_summary = generate_executive_summary(intervention_plans, segment_stats, importance_df)
    
    summary = get_data_summary(df)
    
    extra_data = {
        'segment_stats': segment_stats.to_dict('records'),
        'high_risk_groups': high_risk_groups,
        'intervention_plans': intervention_plans.to_dict('records'),
        'executive_summary': executive_summary
    }
    save_model_cache(model, metrics, importance_df, df, extra_data)
    
    cached_results = {
        'summary': summary,
        'metrics': metrics,
        'importance_df': importance_df,
        'top_features': top_features,
        'feature_stats': get_feature_stats(df),
        'segment_stats': segment_stats,
        'high_risk_groups': high_risk_groups,
        'intervention_plans': intervention_plans,
        'executive_summary': executive_summary,
        'cache_time': datetime.now().isoformat(),
        'cache_used': False
    }
    cache_timestamp = datetime.now()
    
    return cached_results

def get_feature_stats(df):
    stats = {}
    features = ['satisfaction', 'evaluation', 'project_count', 'tenure']
    feature_names = ['满意度', '绩效评分', '项目数', '工龄(年)']
    
    for feat, name in zip(features, feature_names):
        stats[name] = {
            'left_mean': df[df['left'] == 1][feat].mean(),
            'stayed_mean': df[df['left'] == 0][feat].mean(),
            'left_median': df[df['left'] == 1][feat].median(),
            'stayed_median': df[df['left'] == 0][feat].median(),
            'diff': df[df['left'] == 0][feat].mean() - df[df['left'] == 1][feat].mean()
        }
    return stats

@app.route('/')
def index():
    results = run_analysis()
    return render_template('index.html', results=results)

@app.route('/refresh')
def refresh():
    global cached_results, cache_timestamp
    cached_results = None
    cache_timestamp = None
    clear_cache()
    return jsonify({'status': 'success', 'message': '缓存已清空，下次访问将重新分析'})

@app.route('/api/analysis')
def api_analysis():
    force = request.args.get('force', 'false').lower() == 'true'
    results = run_analysis(force_refresh=force)
    
    response = {
        'summary': results['summary'],
        'metrics': results['metrics'],
        'importance': results['importance_df'].to_dict('records'),
        'cache_used': results.get('cache_used', False),
        'cache_time': results.get('cache_time')
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
