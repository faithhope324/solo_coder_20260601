import pandas as pd
import numpy as np
from datetime import datetime


def load_and_clean_data(file_path):
    df = pd.read_csv(file_path)
    
    required_columns = ['pickup_datetime', 'dropoff_datetime', 
                        'pickup_region', 'dropoff_region',
                        'fare_amount']
    
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"缺少必要列: {col}")
    
    df['pickup_datetime'] = pd.to_datetime(df['pickup_datetime'], errors='coerce')
    df['dropoff_datetime'] = pd.to_datetime(df['dropoff_datetime'], errors='coerce')
    
    df = df.dropna(subset=['pickup_datetime', 'dropoff_datetime'])
    
    df['trip_duration'] = (df['dropoff_datetime'] - df['pickup_datetime']).dt.total_seconds() / 60
    
    df = df[df['trip_duration'] > 0]
    
    df['fare_amount'] = pd.to_numeric(df['fare_amount'], errors='coerce')
    
    df = df[(df['fare_amount'] > 0) & (df['fare_amount'] < 1000)]
    
    df['pickup_hour'] = df['pickup_datetime'].dt.hour
    df['pickup_day'] = df['pickup_datetime'].dt.day_name()
    df['pickup_month'] = df['pickup_datetime'].dt.month
    
    if 'trip_distance' in df.columns:
        df['trip_distance'] = pd.to_numeric(df['trip_distance'], errors='coerce')
        df = df[(df['trip_distance'] >= 0) & (df['trip_distance'] < 200)]
    else:
        df['trip_distance'] = df['fare_amount'] * 0.4
    
    return df


def filter_by_date_range(df, start_date, end_date):
    mask = (df['pickup_datetime'] >= start_date) & (df['pickup_datetime'] <= end_date)
    return df.loc[mask]


def get_basic_stats(df):
    stats = {
        'total_trips': len(df),
        'total_fare': df['fare_amount'].sum(),
        'avg_fare': df['fare_amount'].mean(),
        'avg_duration': df['trip_duration'].mean(),
        'avg_distance': df['trip_distance'].mean()
    }
    return stats
