import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


def main():
    np.random.seed(42)

    n = 5000

    center_lat = 39.9042
    center_lon = 116.4074

    latitudes = center_lat + np.random.normal(0, 0.03, n)
    longitudes = center_lon + np.random.normal(0, 0.03, n)
    dropoff_lat = latitudes + np.random.normal(0, 0.02, n)
    dropoff_lon = longitudes + np.random.normal(0, 0.02, n)

    distances = np.abs(np.random.exponential(4, n))
    distances = np.clip(distances, 0.5, 35)

    fares = distances * 2.5 + np.random.normal(5, 2, n)
    fares = np.round(np.clip(fares, 5, 200), 2)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    timestamps = [start_date + timedelta(seconds=np.random.randint(0, int((end_date - start_date).total_seconds()))) for _ in range(n)]

    n_outliers = 50
    outlier_idx = np.random.choice(n, n_outliers, replace=False)
    latitudes[outlier_idx[:25]] = np.random.uniform(-90, 90, 25)
    longitudes[outlier_idx[25:]] = np.random.uniform(-180, 180, 25)

    df = pd.DataFrame({
        '上车纬度': latitudes,
        '上车经度': longitudes,
        '下车纬度': dropoff_lat,
        '下车经度': dropoff_lon,
        '车费（元）': fares,
        '距离（公里）': np.round(distances, 2),
        '时间戳': timestamps
    })

    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, 'orders.csv')
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"数据已生成: {output_path}, 共 {len(df)} 条记录")


if __name__ == '__main__':
    main()
