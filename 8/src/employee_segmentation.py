import pandas as pd
import numpy as np

SATISFACTION_THRESHOLD_LOW = 0.4
SATISFACTION_THRESHOLD_MID = 0.6
TENURE_THRESHOLD = 5
PROJECT_THRESHOLD = 5
EVALUATION_THRESHOLD = 0.7

FEATURE_NAMES_CN = {
    'satisfaction': '满意度',
    'evaluation': '绩效评分',
    'project_count': '项目数',
    'tenure': '工龄(年)'
}

def segment_employees(df):
    df = df.copy()
    
    conditions = [
        (df['satisfaction'] < SATISFACTION_THRESHOLD_LOW) & (df['tenure'] >= TENURE_THRESHOLD),
        (df['satisfaction'] < SATISFACTION_THRESHOLD_LOW) & (df['project_count'] >= PROJECT_THRESHOLD),
        (df['satisfaction'] >= SATISFACTION_THRESHOLD_LOW) & (df['satisfaction'] < SATISFACTION_THRESHOLD_MID) & (df['tenure'] >= TENURE_THRESHOLD),
        (df['satisfaction'] < SATISFACTION_THRESHOLD_LOW) & (df['evaluation'] < EVALUATION_THRESHOLD),
        (df['satisfaction'] >= SATISFACTION_THRESHOLD_MID) & (df['tenure'] >= TENURE_THRESHOLD) & (df['project_count'] >= PROJECT_THRESHOLD),
    ]
    
    segments = [
        '高危群：低满意度老员工',
        '高危群：低满意度超负荷员工',
        '中危群：中等满意度老员工',
        '中危群：低满意度低绩效员工',
        '关注群：高工龄高负载员工',
    ]
    
    df['segment'] = '普通群：其他员工'
    for condition, segment in zip(reversed(conditions), reversed(segments)):
        df.loc[condition, 'segment'] = segment
    
    return df

def analyze_segments(df):
    df_seg = segment_employees(df)
    
    segment_stats = []
    for segment_name in df_seg['segment'].unique():
        seg_data = df_seg[df_seg['segment'] == segment_name]
        left_count = seg_data['left'].sum()
        total_count = len(seg_data)
        left_rate = left_count / total_count if total_count > 0 else 0
        
        stats = {
            'segment_name': segment_name,
            'risk_level': '🔴 高危' if '高危' in segment_name else '🟡 中危' if '中危' in segment_name else '🟢 关注' if '关注' in segment_name else '⚪ 普通',
            'employee_count': total_count,
            'left_count': left_count,
            'left_rate': left_rate,
            'avg_satisfaction': seg_data['satisfaction'].mean(),
            'avg_evaluation': seg_data['evaluation'].mean(),
            'avg_project_count': seg_data['project_count'].mean(),
            'avg_tenure': seg_data['tenure'].mean(),
        }
        segment_stats.append(stats)
    
    segment_stats.sort(key=lambda x: x['left_rate'], reverse=True)
    return pd.DataFrame(segment_stats)

def identify_high_risk_groups(df, importance_df):
    top_feature = importance_df.iloc[0]['feature']
    
    df_left = df[df['left'] == 1]
    df_stay = df[df['left'] == 0]
    
    high_risk_analysis = []
    
    if top_feature == 'satisfaction':
        df_left_low_sat = df_left[df_left['satisfaction'] < SATISFACTION_THRESHOLD_LOW]
        percent_low_sat = len(df_left_low_sat) / len(df_left) * 100
        
        high_risk_analysis.append({
            'group_name': '低满意度员工',
            'description': f'满意度低于 {SATISFACTION_THRESHOLD_LOW}',
            'employee_count': len(df[df['satisfaction'] < SATISFACTION_THRESHOLD_LOW]),
            'left_count_in_group': len(df_left_low_sat),
            'left_rate_in_group': len(df_left_low_sat) / len(df[df['satisfaction'] < SATISFACTION_THRESHOLD_LOW]),
            'percent_of_all_left': percent_low_sat,
            'avg_satisfaction': df_left_low_sat['satisfaction'].mean(),
            'avg_tenure': df_left_low_sat['tenure'].mean(),
        })
    
    tenure_groups = [
        {'name': '老员工(5年以上)', 'min_tenure': 5},
        {'name': '资深员工(3-5年)', 'min_tenure': 3, 'max_tenure': 5},
        {'name': '新员工(1-3年)', 'min_tenure': 1, 'max_tenure': 3},
    ]
    
    for tg in tenure_groups:
        mask = df['tenure'] >= tg['min_tenure']
        if 'max_tenure' in tg:
            mask = mask & (df['tenure'] < tg['max_tenure'])
        
        group_data = df[mask]
        group_left = group_data[group_data['left'] == 1]
        if len(group_data) > 0:
            high_risk_analysis.append({
                'group_name': tg['name'],
                'description': f'工龄 {tg["min_tenure"]}-{tg.get("max_tenure", "+")} 年',
                'employee_count': len(group_data),
                'left_count_in_group': len(group_left),
                'left_rate_in_group': len(group_left) / len(group_data),
                'percent_of_all_left': len(group_left) / len(df_left) * 100,
                'avg_satisfaction': group_left['satisfaction'].mean(),
                'avg_tenure': group_left['tenure'].mean(),
            })
    
    high_risk_analysis.sort(key=lambda x: x['left_rate_in_group'], reverse=True)
    return high_risk_analysis

def get_segment_statistics(df):
    df_seg = segment_employees(df)
    
    segment_summary = []
    for segment in df_seg['segment'].unique():
        seg_df = df_seg[df_seg['segment'] == segment]
        segment_summary.append({
            'segment': segment,
            'count': len(seg_df),
            'avg_satisfaction': seg_df['satisfaction'].mean(),
            'avg_evaluation': seg_df['evaluation'].mean(),
            'avg_projects': seg_df['project_count'].mean(),
            'avg_tenure': seg_df['tenure'].mean(),
            'left_rate': seg_df['left'].mean()
        })
    
    return pd.DataFrame(segment_summary).sort_values('left_rate', ascending=False)

if __name__ == '__main__':
    from data_preprocessing import load_data
    
    df = load_data()
    print("员工分群分析:")
    segment_stats = analyze_segments(df)
    print(segment_stats[['segment_name', 'risk_level', 'employee_count', 'left_rate']])
    
    print("\n高风险群体识别:")
    from data_preprocessing import load_data, preprocess_data, split_data
    from model_training import train_random_forest
    from feature_importance import get_feature_importance
    
    X, y = preprocess_data(df)
    X_train, X_test, y_train, y_test = split_data(X, y)
    model = train_random_forest(X_train, y_train)
    importance_df = get_feature_importance(model, X.columns)
    
    high_risk = identify_high_risk_groups(df, importance_df)
    for group in high_risk[:3]:
        print(f"\n{group['group_name']}:")
        print(f"  人数: {group['employee_count']}, 组内离职率: {group['left_rate_in_group']:.1%}")
        print(f"  占所有离职员工: {group['percent_of_all_left']:.1f}%")
