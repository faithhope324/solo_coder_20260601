import pandas as pd
import numpy as np


def clean_data(df):
    df_clean = df.copy()

    valid_lat_mask = (df_clean['上车纬度'] >= -90) & (df_clean['上车纬度'] <= 90) & \
                     (df_clean['下车纬度'] >= -90) & (df_clean['下车纬度'] <= 90)
    valid_lon_mask = (df_clean['上车经度'] >= -180) & (df_clean['上车经度'] <= 180) & \
                     (df_clean['下车经度'] >= -180) & (df_clean['下车经度'] <= 180)

    df_clean = df_clean[valid_lat_mask & valid_lon_mask]

    df_clean['车费（元）'] = pd.to_numeric(df_clean['车费（元）'], errors='coerce')
    df_clean['距离（公里）'] = pd.to_numeric(df_clean['距离（公里）'], errors='coerce')
    df_clean = df_clean[df_clean['车费（元）'] > 0]
    df_clean = df_clean[df_clean['距离（公里）'] > 0]

    df_clean['时间戳'] = pd.to_datetime(df_clean['时间戳'], errors='coerce')
    df_clean = df_clean.dropna(subset=['时间戳'])

    df_clean = df_clean.reset_index(drop=True)
    return df_clean


def filter_by_date(df, days):
    if days == 'all':
        return df
    days = int(days)
    latest = df['时间戳'].max()
    start_date = latest - pd.Timedelta(days=days)
    return df[df['时间戳'] >= start_date].reset_index(drop=True)
