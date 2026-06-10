import random
from decimal import Decimal
from typing import Optional, List, Tuple, Dict
from django.core.cache import cache
from django.db import transaction
from .models import Prize

PRIZE_STOCK_KEY_PREFIX = 'prize:stock:'
PROBABILITY_VALIDATION_KEY = 'probability:validation:status'


class LotteryAlgorithm:
    def __init__(self):
        self.max_retry_attempts = 5
        self.tolerance = Decimal('0.01')

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

    def increase_stock(self, prize_id: int) -> Tuple[bool, int]:
        key = f'{PRIZE_STOCK_KEY_PREFIX}{prize_id}'
        new_stock = cache.incr(key, 1)
        try:
            Prize.objects.filter(id=prize_id).update(current_stock=new_stock)
        except Exception:
            pass
        return True, int(new_stock)

    def validate_probability_sum(self, prizes: List[Prize] = None) -> Tuple[bool, Decimal, str]:
        if prizes is None:
            prizes = Prize.objects.filter(is_active=True).all()
        
        total_prob = sum(p.probability for p in prizes)
        diff = abs(total_prob - Decimal('100'))
        
        if diff <= self.tolerance:
            cache.set(PROBABILITY_VALIDATION_KEY, {'valid': True, 'total': float(total_prob)}, timeout=3600)
            return True, total_prob, '概率总和校验通过'
        
        message = f'概率总和为 {total_prob}%，不等于 100%，差值为 {diff}%'
        cache.set(PROBABILITY_VALIDATION_KEY, {'valid': False, 'total': float(total_prob)}, timeout=3600)
        return False, total_prob, message

    def get_probability_validation_status(self) -> Dict:
        status = cache.get(PROBABILITY_VALIDATION_KEY)
        if status is None:
            valid, total, message = self.validate_probability_sum()
            return {
                'valid': valid,
                'total': float(total),
                'message': message
            }
        return {
            'valid': status.get('valid', False),
            'total': status.get('total', 0),
            'message': '概率校验状态已缓存'
        }

    def get_active_prizes(self) -> List[Prize]:
        prizes = cache.get('active_prizes')
        if prizes is None:
            prizes = list(Prize.objects.filter(is_active=True).order_by('sort_order', 'id'))
            cache.set('active_prizes', prizes, timeout=300)
        return prizes

    def calculate_probability_ranges(self, prizes: List[Prize]) -> Tuple[List[Tuple[Prize, Decimal, Decimal]], bool]:
        valid, total_prob, message = self.validate_probability_sum(prizes)
        
        if not valid:
            raise ValueError(message)
        
        ranges = []
        current = Decimal('0')
        
        for prize in prizes:
            prob = prize.probability
            if prob > 0:
                ranges.append((prize, current, current + prob))
                current += prob
        
        if abs(current - Decimal('100')) > self.tolerance:
            raise ValueError(f'计算区间错误，累计概率: {current}%')
        
        return ranges, valid

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
        
        valid, total_prob, msg = self.validate_probability_sum(prizes)
        if not valid:
            return None, f'奖品概率配置错误：{msg}'
        
        available_prizes = [p for p in prizes if self.get_prize_stock(p.id) > 0]
        if not available_prizes:
            return None, '所有奖品已抽完'
        
        tried_prize_ids = set()
        
        for attempt in range(self.max_retry_attempts):
            try:
                ranges, valid = self.calculate_probability_ranges(available_prizes)
            except ValueError as e:
                return None, str(e)
            
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
                with transaction.atomic():
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
        cache.delete(PROBABILITY_VALIDATION_KEY)
        keys = cache.keys(f'{PRIZE_STOCK_KEY_PREFIX}*')
        if keys:
            cache.delete_many(keys)
