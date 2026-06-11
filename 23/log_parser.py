import csv
from datetime import datetime
from collections import defaultdict


class LogParser:
    def __init__(self, behavior_path, products_path):
        self.behavior_path = behavior_path
        self.products_path = products_path
        self.sessions = {}
        self.products = {}
        self.category_products = defaultdict(list)
        self._load_products()
        self._load_behavior()

    def _load_products(self):
        with open(self.products_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row['product_id']
                self.products[pid] = {
                    'product_id': pid,
                    'product_name': row['product_name'],
                    'category': row['category'],
                    'price': float(row['price'])
                }
                self.category_products[row['category']].append(pid)

    def _load_behavior(self):
        with open(self.behavior_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row['session_id']
                if sid not in self.sessions:
                    self.sessions[sid] = {
                        'session_id': sid,
                        'user_id': row['user_id'],
                        'device': row['device'],
                        'actions': [],
                        'cart_products': [],
                        'has_add_cart': False,
                        'has_enter_checkout': False,
                        'has_payment_success': False,
                        'first_hour': None
                    }
                
                action = row['action']
                ts = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                
                self.sessions[sid]['actions'].append({
                    'action': action,
                    'timestamp': ts,
                    'product_id': row['product_id']
                })
                
                if action == 'add_cart':
                    self.sessions[sid]['has_add_cart'] = True
                    self.sessions[sid]['cart_products'].append(row['product_id'])
                elif action == 'enter_checkout':
                    self.sessions[sid]['has_enter_checkout'] = True
                elif action == 'payment_success':
                    self.sessions[sid]['has_payment_success'] = True
                
                if self.sessions[sid]['first_hour'] is None:
                    self.sessions[sid]['first_hour'] = ts.hour

    def get_sessions_with_action(self, action_type):
        return [s for s in self.sessions.values() if s.get(f'has_{action_type}', False)]

    def get_cart_sessions(self):
        return self.get_sessions_with_action('add_cart')

    def get_checkout_sessions(self):
        return self.get_sessions_with_action('enter_checkout')

    def get_payment_sessions(self):
        return self.get_sessions_with_action('payment_success')

    def get_abandoned_sessions(self):
        return [s for s in self.sessions.values()
                if s['has_add_cart'] and not s['has_payment_success']]

    def get_anomaly_sessions(self, min_cart_items=10):
        anomalies = []
        for s in self.sessions.values():
            if s['has_add_cart'] and not s['has_payment_success']:
                cart_count = len(s['cart_products'])
                if cart_count >= min_cart_items:
                    anomalies.append({
                        'session_id': s['session_id'],
                        'user_id': s['user_id'],
                        'device': s['device'],
                        'cart_item_count': cart_count,
                        'cart_products': s['cart_products'],
                        'first_action_time': s['actions'][0]['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    })
        anomalies.sort(key=lambda x: x['cart_item_count'], reverse=True)
        return anomalies

    def get_product_category(self, product_id):
        if product_id in self.products:
            return self.products[product_id]['category']
        return None

    def get_category_product_ids(self, category):
        return self.category_products.get(category, [])

    def get_all_categories(self):
        return list(self.category_products.keys())
