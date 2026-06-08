import pandas as pd
import numpy as np


BEIJING_REGION_COORDS = {
    '朝阳区': {'lat': 39.9219, 'lon': 116.4435, 'weight': 2.0},
    '海淀区': {'lat': 39.9599, 'lon': 116.2982, 'weight': 1.8},
    '西城区': {'lat': 39.9121, 'lon': 116.3660, 'weight': 1.5},
    '东城区': {'lat': 39.9289, 'lon': 116.4160, 'weight': 1.5},
    '丰台区': {'lat': 39.8585, 'lon': 116.2870, 'weight': 1.2},
    '石景山区': {'lat': 39.9063, 'lon': 116.2220, 'weight': 0.8},
    '通州区': {'lat': 39.9020, 'lon': 116.6560, 'weight': 1.0},
    '昌平区': {'lat': 40.2206, 'lon': 116.2311, 'weight': 0.9},
    '大兴区': {'lat': 39.7266, 'lon': 116.3417, 'weight': 0.9},
    '顺义区': {'lat': 40.1301, 'lon': 116.6547, 'weight': 0.8},
    '房山区': {'lat': 39.7488, 'lon': 115.9930, 'weight': 0.7},
    '门头沟区': {'lat': 39.9371, 'lon': 116.1020, 'weight': 0.5}
}

ALL_REGIONS = BEIJING_REGION_COORDS


def aggregate_by_pickup_region(df):
    region_stats = df.groupby('pickup_region').agg({
        'fare_amount': ['count', 'sum', 'mean'],
        'trip_distance': 'mean',
        'trip_duration': 'mean'
    }).reset_index()
    
    region_stats.columns = ['region', 'trip_count', 'total_fare', 
                            'avg_fare', 'avg_distance', 'avg_duration']
    
    region_stats = region_stats.sort_values('trip_count', ascending=False)
    return region_stats


def aggregate_by_dropoff_region(df):
    region_stats = df.groupby('dropoff_region').agg({
        'fare_amount': ['count', 'sum', 'mean']
    }).reset_index()
    
    region_stats.columns = ['region', 'trip_count', 'total_fare', 'avg_fare']
    
    region_stats = region_stats.sort_values('trip_count', ascending=False)
    return region_stats


def get_region_coordinates(region_name):
    if region_name in ALL_REGIONS:
        return ALL_REGIONS[region_name]['lat'], ALL_REGIONS[region_name]['lon']
    return 39.9042, 116.4074


def get_region_heatmap_data(df):
    pickup_regions = df['pickup_region'].unique()
    heatmap_data = []
    
    for region in pickup_regions:
        count = len(df[df['pickup_region'] == region])
        lat, lon = get_region_coordinates(region)
        weight = ALL_REGIONS.get(region, {}).get('weight', 1.0)
        heatmap_data.append({
            'region': region,
            'lat': lat,
            'lon': lon,
            'count': count,
            'weight': weight
        })
    
    return sorted(heatmap_data, key=lambda x: x['count'], reverse=True)


def get_top_regions(df, n=10):
    region_stats = aggregate_by_pickup_region(df)
    return region_stats.head(n)


def get_region_hourly_pattern(df, region):
    region_df = df[df['pickup_region'] == region]
    hourly = region_df.groupby('pickup_hour').agg({
        'fare_amount': 'count'
    }).reset_index()
    hourly.columns = ['hour', 'trip_count']
    return hourly
