import pandas as pd
import numpy as np


def get_region(lat, lon, center_lat, center_lon):
    dlat = lat - center_lat
    dlon = lon - center_lon

    threshold_lat = 0.015
    threshold_lon = 0.015

    if abs(dlat) < threshold_lat and abs(dlon) < threshold_lon:
        return '中'
    elif abs(dlat) >= abs(dlon):
        return '北' if dlat > 0 else '南'
    else:
        return '东' if dlon > 0 else '西'


def assign_regions(df, center_lat=None, center_lon=None):
    if center_lat is None:
        center_lat = df['上车纬度'].median()
    if center_lon is None:
        center_lon = df['上车经度'].median()

    df = df.copy()
    df['区域'] = df.apply(
        lambda row: get_region(row['上车纬度'], row['上车经度'], center_lat, center_lon),
        axis=1
    )
    return df, center_lat, center_lon


def aggregate_region_stats(df):
    region_order = ['东', '南', '西', '北', '中']
    stats = df.groupby('区域').agg(
        平均车费=('车费（元）', 'mean'),
        平均距离=('距离（公里）', 'mean'),
        订单数=('车费（元）', 'count')
    ).reset_index()

    stats['平均车费'] = stats['平均车费'].round(2)
    stats['平均距离'] = stats['平均距离'].round(2)

    for region in region_order:
        if region not in stats['区域'].values:
            stats = pd.concat([stats, pd.DataFrame([{
                '区域': region, '平均车费': 0, '平均距离': 0, '订单数': 0
            }])], ignore_index=True)

    stats['区域'] = pd.Categorical(stats['区域'], categories=region_order, ordered=True)
    stats = stats.sort_values('区域').reset_index(drop=True)
    return stats


def get_distance_distribution(df):
    bins = [0, 5, 10, 15, 20, float('inf')]
    labels = ['0-5km', '5-10km', '10-15km', '15-20km', '20km+']
    df = df.copy()
    df['距离区间'] = pd.cut(df['距离（公里）'], bins=bins, labels=labels, right=False)
    dist = df['距离区间'].value_counts().reindex(labels, fill_value=0).reset_index()
    dist.columns = ['距离区间', '订单数']
    return dist
