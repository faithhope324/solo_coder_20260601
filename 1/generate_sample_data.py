import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

REGIONS = [
    '朝阳区', '海淀区', '西城区', '东城区',
    '丰台区', '石景山区', '通州区', '昌平区',
    '大兴区', '顺义区', '房山区', '门头沟区'
]

REGION_WEIGHTS = [3.0, 2.5, 2.0, 2.0, 1.5, 0.8, 1.2, 1.0, 1.0, 0.9, 0.7, 0.5]


def generate_sample_data(num_records=15000):
    data = []
    
    base_date = datetime(2024, 6, 1)
    
    for i in range(num_records):
        day_offset = random.randint(0, 30)
        hour = int(np.random.normal(14, 5))
        hour = max(0, min(23, hour))
        
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            multiplier = 2.5
        elif 11 <= hour <= 13:
            multiplier = 1.8
        else:
            multiplier = 1.0
        
        if random.random() < 0.35 * multiplier:
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            pickup_datetime = base_date + timedelta(
                days=day_offset, hours=hour, minutes=minute, seconds=second
            )
            
            distance = max(1.0, np.random.normal(8, 5))
            distance = round(distance, 1)
            
            base_fare = 13.0
            distance_fare = max(0, distance - 3) * 2.3
            low_speed_fare = random.uniform(0, 5)
            fare_amount = round(base_fare + distance_fare + low_speed_fare, 1)
            
            avg_speed = max(10, np.random.normal(30, 10))
            duration = max(3, round(distance / avg_speed * 60, 0))
            duration = int(duration)
            
            dropoff_datetime = pickup_datetime + timedelta(minutes=duration)
            
            pickup_region = random.choices(REGIONS, weights=REGION_WEIGHTS, k=1)[0]
            dropoff_region = random.choice(REGIONS)
            
            data.append({
                'pickup_datetime': pickup_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'dropoff_datetime': dropoff_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'pickup_region': pickup_region,
                'dropoff_region': dropoff_region,
                'fare_amount': fare_amount,
                'trip_distance': distance
            })
    
    df = pd.DataFrame(data)
    return df


if __name__ == '__main__':
    print('正在生成北京出租车示例数据...')
    df = generate_sample_data(15000)
    df.to_csv('data/taxi_data.csv', index=False)
    print(f'已生成 {len(df)} 条记录，保存至 data/taxi_data.csv')
    print('\n数据预览:')
    print(df.head(10))
    print('\n数据统计:')
    print(df.describe())
