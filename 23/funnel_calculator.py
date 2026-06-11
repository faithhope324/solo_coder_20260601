from collections import defaultdict


class FunnelCalculator:
    STAGES = ['add_cart', 'enter_checkout', 'payment_success']
    STAGE_LABELS = ['加购', '进入结算', '支付成功']

    def __init__(self, log_parser):
        self.parser = log_parser
        self.overall_funnel = self._calc_overall_funnel()
        self.device_funnel = self._calc_device_funnel()
        self.hourly_abandonment = self._calc_hourly_abandonment()
        self.category_abandonment = self._calc_category_abandonment()

    def _calc_overall_funnel(self):
        sessions = self.parser.sessions.values()
        counts = {stage: 0 for stage in self.STAGES}
        for s in sessions:
            if s['has_add_cart']:
                counts['add_cart'] += 1
            if s['has_enter_checkout']:
                counts['enter_checkout'] += 1
            if s['has_payment_success']:
                counts['payment_success'] += 1
        
        result = []
        prev_count = None
        for stage, label in zip(self.STAGES, self.STAGE_LABELS):
            count = counts[stage]
            conversion_rate = count / counts['add_cart'] if counts['add_cart'] > 0 else 0
            step_rate = count / prev_count if prev_count and prev_count > 0 else 1.0
            drop_off_rate = 1 - step_rate
            result.append({
                'stage': stage,
                'label': label,
                'count': count,
                'conversion_rate': conversion_rate,
                'step_rate': step_rate,
                'drop_off_rate': drop_off_rate
            })
            prev_count = count
        
        return result

    def _calc_device_funnel(self):
        device_counts = defaultdict(lambda: {stage: 0 for stage in self.STAGES})
        for s in self.parser.sessions.values():
            device = s['device']
            if s['has_add_cart']:
                device_counts[device]['add_cart'] += 1
            if s['has_enter_checkout']:
                device_counts[device]['enter_checkout'] += 1
            if s['has_payment_success']:
                device_counts[device]['payment_success'] += 1
        
        result = {}
        for device, counts in device_counts.items():
            funnel = []
            prev_count = None
            for stage, label in zip(self.STAGES, self.STAGE_LABELS):
                count = counts[stage]
                conversion_rate = count / counts['add_cart'] if counts['add_cart'] > 0 else 0
                step_rate = count / prev_count if prev_count and prev_count > 0 else 1.0
                drop_off_rate = 1 - step_rate
                funnel.append({
                    'stage': stage,
                    'label': label,
                    'count': count,
                    'conversion_rate': conversion_rate,
                    'step_rate': step_rate,
                    'drop_off_rate': drop_off_rate
                })
                prev_count = count
            result[device] = funnel
        return result

    def _calc_hourly_abandonment(self):
        hourly = {h: {'add_cart': 0, 'payment_success': 0} for h in range(24)}
        for s in self.parser.sessions.values():
            hour = s['first_hour']
            if hour is None:
                continue
            if s['has_add_cart']:
                hourly[hour]['add_cart'] += 1
            if s['has_payment_success']:
                hourly[hour]['payment_success'] += 1
        
        result = []
        for h in range(24):
            add_cart = hourly[h]['add_cart']
            payment = hourly[h]['payment_success']
            abandon_rate = 1 - (payment / add_cart) if add_cart > 0 else 0
            result.append({
                'hour': h,
                'hour_label': f'{h:02d}:00',
                'add_cart': add_cart,
                'payment_success': payment,
                'abandonment_rate': abandon_rate
            })
        return result

    def _calc_category_abandonment(self):
        category_stats = defaultdict(lambda: {'cart_sessions': set(), 'payment_sessions': set()})
        
        for s in self.parser.sessions.values():
            if not s['has_add_cart']:
                continue
            
            categories = set()
            for pid in s['cart_products']:
                cat = self.parser.get_product_category(pid)
                if cat:
                    categories.add(cat)
            
            for cat in categories:
                category_stats[cat]['cart_sessions'].add(s['session_id'])
                if s['has_payment_success']:
                    category_stats[cat]['payment_sessions'].add(s['session_id'])
        
        result = []
        for cat, stats in category_stats.items():
            cart_count = len(stats['cart_sessions'])
            payment_count = len(stats['payment_sessions'])
            abandon_rate = 1 - (payment_count / cart_count) if cart_count > 0 else 0
            result.append({
                'category': cat,
                'cart_sessions': cart_count,
                'payment_sessions': payment_count,
                'abandonment_rate': abandon_rate
            })
        
        result.sort(key=lambda x: x['abandonment_rate'], reverse=True)
        return result

    def get_overall_abandonment_rate(self):
        add_cart = self.overall_funnel[0]['count']
        payment = self.overall_funnel[2]['count']
        return 1 - (payment / add_cart) if add_cart > 0 else 0

    def get_top_abandon_categories(self, top_n=10):
        return self.category_abandonment[:top_n]

    def get_peak_abandon_hours(self, top_n=3):
        sorted_hours = sorted(self.hourly_abandonment, key=lambda x: x['abandonment_rate'], reverse=True)
        return sorted_hours[:top_n]
