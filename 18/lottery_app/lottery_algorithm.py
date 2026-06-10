import random
from decimal import Decimal
from typing import Optional, List, Tuple
from django.core.cache import cache
from .models import Prize

PRIZE_STOCK_KEY_PREFIX = 'prize:stock:'


class LotteryAlgorithm:
    def __init__(self):
        self.max_retry_attempts = 5

    def get_prize_stock(self, prize_id: int) -> int:
        key = f'{PRIZE_STOCK_KEY_PREFIX}{prize_id}'
        stock = cache.get(key)
        if stock is None:
            try:
                prize = Prize.objects.get(id=prize_id)
                stock = prize.current_stock
                cache.set(key, stock, timeout=3600)
            except Prize.DoesNotExist:
                stock = 0
        return int(stock) if stock else 0

    def decrease_stock(self, prize_id: int) -> Tuple[bool, int]:
        key = f'{PRIZE_STOCK_KEY_PREFIX}{prize_id}'
        stock = cache.decr(key, 1)
        if stock < 0:
            cache.incr(key, 1)
            return False, 0
        return True, stock

    def get_active_prizes(self) -> List[Prize]:
        prizes = cache.get('active_prizes')
        if prizes is None:
            prizes = list(Prize.objects.filter(is_active=True).order_by('sort_order', 'id'))
            cache.set('active_prizes', prizes, timeout=300)
        return prizes

    def calculate_probability_ranges(self, prizes: List[Prize]) -> List[Tuple[Prize, Decimal, Decimal]]:
        ranges = []
        current = Decimal('0')
        
        for prize in prizes:
            prob = prize.probability
            if prob > 0:
                ranges.append((prize, current, current + prob))
                current += prob
        
        if current != Decimal('100'):
            if ranges:
                last_prize, start, end = ranges[-1]
                ranges[-1] = (last_prize, start, Decimal('100'))
        
        return ranges

    def select_prize_by_probability(self, ranges: List[Tuple[Prize, Decimal, Decimal]]) -> Optional[Prize]:
        if not ranges:
            return None
        
        rand_value = Decimal(str(random.uniform(0, 100)))
        
        for prize, start, end in ranges:
            if start <= rand_value < end:
                return prize
        
        if ranges:
            return ranges[-1][0]
        
        return None

    def draw_prize(self) -> Tuple[Optional[Prize], str]:
        prizes = self.get_active_prizes()
        if not prizes:
            return None, '暂无可用奖品'
        
        available_prizes = [p for p in prizes if self.get_prize_stock(p.id) > 0]
        if not available_prizes:
            return None, '所有奖品已抽完'
        
        tried_prize_ids = set()
        
        for attempt in range(self.max_retry_attempts):
            ranges = self.calculate_probability_ranges(available_prizes)
            selected_prize = self.select_prize_by_probability(ranges)
            
            if selected_prize is None:
                return None, '抽奖失败，请重试'
            
            if selected_prize.id in tried_prize_ids:
                continue
            
            stock = self.get_prize_stock(selected_prize.id)
            if stock <= 0:
                tried_prize_ids.add(selected_prize.id)
                available_prizes = [p for p in available_prizes if p.id not in tried_prize_ids]
                if not available_prizes:
                    return None, '所有奖品已抽完'
                continue
            
            success, new_stock = self.decrease_stock(selected_prize.id)
            if success:
                Prize.objects.filter(id=selected_prize.id).update(current_stock=new_stock)
                return selected_prize, 'success'
            else:
                tried_prize_ids.add(selected_prize.id)
                available_prizes = [p for p in available_prizes if p.id not in tried_prize_ids]
                if not available_prizes:
                    return None, '所有奖品已抽完'
        
        return self._get_fallback_prize(available_prizes)

    def _get_fallback_prize(self, available_prizes: List[Prize]) -> Tuple[Optional[Prize], str]:
        for prize in sorted(available_prizes, key=lambda p: p.prize_type, reverse=True):
            stock = self.get_prize_stock(prize.id)
            if stock > 0:
                success, new_stock = self.decrease_stock(prize.id)
                if success:
                    Prize.objects.filter(id=prize.id).update(current_stock=new_stock)
                    return prize, 'success'
        
        return None, '所有奖品已抽完'

    def sync_stock_to_redis(self, prize_id: int):
        try:
            prize = Prize.objects.get(id=prize_id)
            key = f'{PRIZE_STOCK_KEY_PREFIX}{prize_id}'
            cache.set(key, prize.current_stock, timeout=None)
        except Prize.DoesNotExist:
            pass

    def sync_all_stock_to_redis(self):
        prizes = Prize.objects.all()
        for prize in prizes:
            self.sync_stock_to_redis(prize.id)

    def clear_cache(self):
        cache.delete('active_prizes')
        keys = cache.keys(f'{PRIZE_STOCK_KEY_PREFIX}*')
        if keys:
            cache.delete_many(keys)
