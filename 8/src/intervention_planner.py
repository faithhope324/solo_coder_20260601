import pandas as pd
import numpy as np

AVERAGE_SALARY = 15000
AVERAGE_RECRUIT_COST = 30000
AVERAGE_TRAINING_COST = 5000
SATISFACTION_LIFT_PER_DOLLAR = 0.0001

INTERVENTION_LIBRARY = {
    'one_on_one_meeting': {
        'name': '1对1深度沟通',
        'description': '直属领导与高风险员工进行1对1沟通，了解问题并制定改进计划',
        'target_group': '低满意度员工、老员工',
        'cost_per_employee': 200,
        'duration_weeks': 2,
        'expected_satisfaction_lift': 0.08,
        'expected_retention_rate': 0.25,
        'effort_level': '低',
        'priority': '🔴 最高',
        'actions': [
            '每周1次30分钟1对1沟通，持续1个月',
            '建立个人发展计划(IDP)',
            '明确职业发展路径'
        ]
    },
    'salary_adjustment': {
        'name': '薪资调整',
        'description': '对高价值高风险员工进行薪资调整，匹配市场水平',
        'target_group': '低满意度高绩效老员工',
        'cost_per_employee': 24000,
        'duration_weeks': 4,
        'expected_satisfaction_lift': 0.25,
        'expected_retention_rate': 0.45,
        'effort_level': '中',
        'priority': '🔴 最高',
        'actions': [
            '进行市场薪酬调研',
            '评估员工绩效和贡献',
            '制定调薪方案，调薪幅度5-15%'
        ]
    },
    'workload_reduction': {
        'name': '工作量优化',
        'description': '减少高负载员工的项目数量，优化工作分配',
        'target_group': '项目数>5的超负荷员工',
        'cost_per_employee': 500,
        'duration_weeks': 3,
        'expected_satisfaction_lift': 0.15,
        'expected_retention_rate': 0.35,
        'effort_level': '中',
        'priority': '🟠 高',
        'actions': [
            '盘点当前项目优先级',
            '暂停或转移非核心项目',
            '招聘新人或重新分配资源'
        ]
    },
    'training_development': {
        'name': '培训与发展支持',
        'description': '提供技能培训和晋升机会，增强员工归属感',
        'target_group': '工龄3-5年的资深员工',
        'cost_per_employee': 8000,
        'duration_weeks': 12,
        'expected_satisfaction_lift': 0.18,
        'expected_retention_rate': 0.38,
        'effort_level': '高',
        'priority': '🟠 高',
        'actions': [
            '提供外部培训课程（每人每年5000元预算）',
            '建立导师制，配对资深员工作为导师',
            '每季度评估晋升可能性'
        ]
    },
    'team_building': {
        'name': '团队建设活动',
        'description': '组织团建活动，改善团队氛围和归属感',
        'target_group': '全公司，重点是低满意度群体',
        'cost_per_employee': 500,
        'duration_weeks': 1,
        'expected_satisfaction_lift': 0.05,
        'expected_retention_rate': 0.10,
        'effort_level': '低',
        'priority': '🟡 中',
        'actions': [
            '每月1次团队聚餐（人均200元）',
            '每季度1次户外活动（人均300元）',
            '设立员工关怀基金'
        ]
    },
    'flexible_work': {
        'name': '弹性工作制',
        'description': '实行弹性上下班时间和远程办公政策',
        'target_group': '工龄2年以上员工',
        'cost_per_employee': 100,
        'duration_weeks': 4,
        'expected_satisfaction_lift': 0.12,
        'expected_retention_rate': 0.22,
        'effort_level': '低',
        'priority': '🟠 高',
        'actions': [
            '弹性上下班时间（核心工作时间10:00-16:00）',
            '每周2天可远程办公',
            '建立远程协作规范'
        ]
    },
    'recognition_program': {
        'name': '认可与激励计划',
        'description': '建立及时认可机制，表彰优秀表现',
        'target_group': '高绩效但低满意度员工',
        'cost_per_employee': 1000,
        'duration_weeks': 6,
        'expected_satisfaction_lift': 0.10,
        'expected_retention_rate': 0.18,
        'effort_level': '低',
        'priority': '🟡 中',
        'actions': [
            '月度之星评选（奖金500元）',
            '季度优秀团队奖励（团队活动基金2000元）',
            '建立即时认可平台（电子表扬卡）'
        ]
    },
    'mentorship_program': {
        'name': '导师计划',
        'description': '为新员工和老员工配对导师，提供职业指导',
        'target_group': '新员工(1-3年)和老员工(5年以上)',
        'cost_per_employee': 300,
        'duration_weeks': 8,
        'expected_satisfaction_lift': 0.08,
        'expected_retention_rate': 0.15,
        'effort_level': '中',
        'priority': '🟡 中',
        'actions': [
            '选拔和培训导师',
            '建立导师-学员匹配机制',
            '每月1次正式辅导会议'
        ]
    }
}

def calculate_roi(intervention, employee_count, baseline_left_rate):
    cost = intervention['cost_per_employee'] * employee_count
    retained_employees = employee_count * baseline_left_rate * intervention['expected_retention_rate']
    savings_per_employee = AVERAGE_RECRUIT_COST + AVERAGE_TRAINING_COST + (AVERAGE_SALARY * 3)
    total_savings = retained_employees * savings_per_employee
    net_benefit = total_savings - cost
    roi = (net_benefit / cost) * 100 if cost > 0 else 0
    
    return {
        'total_cost': cost,
        'expected_retained': retained_employees,
        'total_savings': total_savings,
        'net_benefit': net_benefit,
        'roi_percent': roi,
        'cost_per_retention': cost / retained_employees if retained_employees > 0 else 0
    }

def generate_intervention_plan(df, segment_stats, importance_df, high_risk_groups):
    plans = []
    
    for _, segment in segment_stats.iterrows():
        if segment['left_rate'] < 0.1:
            continue
            
        segment_name = segment['segment_name']
        employee_count = segment['employee_count']
        left_rate = segment['left_rate']
        
        applicable_interventions = []
        
        if '低满意度' in segment_name:
            applicable_interventions.extend(['one_on_one_meeting', 'salary_adjustment', 'recognition_program'])
        if '老员工' in segment_name or '工龄' in segment_name:
            applicable_interventions.extend(['mentorship_program', 'training_development', 'salary_adjustment'])
        if '超负荷' in segment_name or '高负载' in segment_name or '项目数' in segment_name:
            applicable_interventions.append('workload_reduction')
        if '中危' in segment_name:
            applicable_interventions.extend(['team_building', 'flexible_work'])
        
        applicable_interventions = list(dict.fromkeys(applicable_interventions))
        
        for intervention_key in applicable_interventions:
            intervention = INTERVENTION_LIBRARY[intervention_key].copy()
            roi_data = calculate_roi(intervention, employee_count, left_rate)
            
            plan = {
                'target_segment': segment_name,
                'risk_level': segment['risk_level'],
                'target_employee_count': employee_count,
                'baseline_left_rate': left_rate,
                'intervention_name': intervention['name'],
                'intervention_description': intervention['description'],
                'priority': intervention['priority'],
                'effort_level': intervention['effort_level'],
                'actions': intervention['actions'],
                'duration_weeks': intervention['duration_weeks'],
                'expected_satisfaction_lift': intervention['expected_satisfaction_lift'],
                'expected_retention_rate': intervention['expected_retention_rate'],
                'total_cost': roi_data['total_cost'],
                'expected_retained_employees': roi_data['expected_retained'],
                'expected_savings': roi_data['total_savings'],
                'net_benefit': roi_data['net_benefit'],
                'roi_percent': roi_data['roi_percent'],
                'cost_per_retention': roi_data['cost_per_retention'],
            }
            plans.append(plan)
    
    plans_df = pd.DataFrame(plans)
    
    if not plans_df.empty:
        plans_df = plans_df.sort_values(['roi_percent', 'priority'], ascending=[False, True])
        plans_df = plans_df.reset_index(drop=True)
    
    return plans_df

def generate_executive_summary(plans_df, segment_stats, importance_df):
    total_high_risk = segment_stats[segment_stats['risk_level'].str.contains('高危')]['employee_count'].sum()
    total_at_risk = segment_stats[segment_stats['risk_level'].str.contains('高危|中危')]['employee_count'].sum()
    
    if plans_df.empty:
        return {}
    
    top_plans = plans_df.head(3)
    
    total_investment = top_plans['total_cost'].sum()
    total_expected_savings = top_plans['expected_savings'].sum()
    total_net_benefit = top_plans['net_benefit'].sum()
    total_expected_retained = top_plans['expected_retained_employees'].sum()
    
    summary = {
        'total_high_risk_employees': total_high_risk,
        'total_at_risk_employees': total_at_risk,
        'top_feature': importance_df.iloc[0]['feature_cn'],
        'top_feature_importance': importance_df.iloc[0]['importance'],
        'recommended_investment': total_investment,
        'expected_savings': total_expected_savings,
        'expected_net_benefit': total_net_benefit,
        'expected_retained_employees': total_expected_retained,
        'overall_roi': (total_net_benefit / total_investment) * 100 if total_investment > 0 else 0,
        'priority_actions': [
            {
                'rank': idx + 1,
                'action': row['intervention_name'],
                'target': row['target_segment'],
                'cost': row['total_cost'],
                'roi': row['roi_percent']
            }
            for idx, row in top_plans.iterrows()
        ]
    }
    
    return summary

if __name__ == '__main__':
    from data_preprocessing import load_data, preprocess_data, split_data
    from model_training import train_random_forest
    from feature_importance import get_feature_importance
    from employee_segmentation import analyze_segments, identify_high_risk_groups
    
    df = load_data()
    X, y = preprocess_data(df)
    X_train, X_test, y_train, y_test = split_data(X, y)
    model = train_random_forest(X_train, y_train)
    importance_df = get_feature_importance(model, X.columns)
    
    segment_stats = analyze_segments(df)
    high_risk_groups = identify_high_risk_groups(df, importance_df)
    
    print("生成干预方案...")
    plans_df = generate_intervention_plan(df, segment_stats, importance_df, high_risk_groups)
    print(plans_df[['target_segment', 'intervention_name', 'priority', 'total_cost', 'expected_retained_employees', 'roi_percent']].head())
    
    print("\n执行摘要:")
    summary = generate_executive_summary(plans_df, segment_stats, importance_df)
    for key, value in summary.items():
        if key != 'priority_actions':
            print(f"  {key}: {value}")
