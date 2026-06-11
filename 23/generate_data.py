import csv
import random
import uuid
from datetime import datetime, timedelta

random.seed(42)

categories = [
    '电子产品', '服装鞋帽', '家居用品', '食品饮料', '美妆护肤',
    '母婴用品', '运动户外', '图书文具', '汽车用品', '宠物用品'
]

products = []
for i in range(500):
    product_id = f'P{i+1:04d}'
    category = random.choice(categories)
    price = round(random.uniform(10, 5000), 2)
    product_name = f'{category}商品{i+1}'
    products.append({
        'product_id': product_id,
        'product_name': product_name,
        'category': category,
        'price': price
    })

with open('data/products.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['product_id', 'product_name', 'category', 'price'])
    writer.writeheader()
    writer.writerows(products)

print(f'Generated {len(products)} products')

num_sessions = 11000
rows = []
base_time = datetime(2026, 6, 1, 0, 0, 0)

for s in range(num_sessions):
    session_id = f'S{s+1:06d}'
    user_id = f'U{random.randint(1, 8000):05d}'
    device = random.choice(['mobile', 'pc'])
    
    hour_weights = [2, 1, 1, 1, 1, 2, 4, 6, 7, 6, 5, 5, 6, 5, 5, 6, 7, 8, 9, 10, 8, 6, 4, 3]
    total_weight = sum(hour_weights)
    r = random.randint(1, total_weight)
    hour = 0
    cum = 0
    for h, w in enumerate(hour_weights):
        cum += w
        if r <= cum:
            hour = h
            break
    
    session_start = base_time + timedelta(
        days=random.randint(0, 29),
        hours=hour,
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    
    num_cart_items = random.randint(1, 15)
    cart_products = random.sample([p['product_id'] for p in products], min(num_cart_items, len(products)))
    
    current_time = session_start
    for pid in cart_products:
        rows.append({
            'session_id': session_id,
            'user_id': user_id,
            'action': 'add_cart',
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'device': device,
            'product_id': pid
        })
        current_time += timedelta(seconds=random.randint(10, 120))
    
    if device == 'mobile':
        checkout_prob = 0.55
        payment_prob_given_checkout = 0.65
    else:
        checkout_prob = 0.65
        payment_prob_given_checkout = 0.75
    
    entered_checkout = False
    if random.random() < checkout_prob:
        entered_checkout = True
        rows.append({
            'session_id': session_id,
            'user_id': user_id,
            'action': 'enter_checkout',
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'device': device,
            'product_id': ''
        })
        current_time += timedelta(seconds=random.randint(30, 300))
    
    if entered_checkout and random.random() < payment_prob_given_checkout:
        rows.append({
            'session_id': session_id,
            'user_id': user_id,
            'action': 'payment_success',
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'device': device,
            'product_id': ''
        })

rows.sort(key=lambda x: x['timestamp'])

with open('data/user_behavior.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['session_id', 'user_id', 'action', 'timestamp', 'device', 'product_id'])
    writer.writeheader()
    writer.writerows(rows)

print(f'Generated {len(rows)} behavior log rows')
print(f'Generated {num_sessions} sessions')
