import time
from datetime import date
from typing import Tuple
from django.core.cache import cache
from django.conf import settings
from .models import UserDailyChance

RATE_LIMIT_KEY_PREFIX = 'rate_limit:user:'
DAILY_CHANCE_KEY_PREFIX = 'daily_chance:user:'


class RedisService:
    def __init__(self):
        self.rate_limit_window = 1
        self.rate_limit_max_requests = 1

    def check_rate_limit(self, user_id: int) -> Tuple[bool, int]:
        key = f'{RATE_LIMIT_KEY_PREFIX}{user_id}'
        current = cache.get(key)
        
        if current is None:
            cache.set(key, 1, timeout=self.rate_limit_window)
            return True, 0
        
        if int(current) >= self.rate_limit_max_requests:
            ttl = cache.ttl(key)
            return False, ttl if ttl > 0 else 1
        
        cache.incr(key)
        return True, 0

    def get_remaining_chances(self, user_id: int, today: date = None) -> int:
        if today is None:
            today = date.today()
        
        key = f'{DAILY_CHANCE_KEY_PREFIX}{user_id}:{today.isoformat()}'
        used = cache.get(key)
        
        if used is None:
            try:
                daily_chance = UserDailyChance.objects.get(user_id=user_id, date=today)
                used = daily_chance.free_chances_used
                cache.set(key, used, timeout=86400)
            except UserDailyChance.DoesNotExist:
                used = 0
                cache.set(key, 0, timeout=86400)
        
        return max(0, settings.DAILY_FREE_CHANCES - int(used))

    def consume_chance(self, user_id: int, today: date = None) -> Tuple[bool, int]:
        if today is None:
            today = date.today()
        
        remaining = self.get_remaining_chances(user_id, today)
        if remaining <= 0:
            return False, 0
        
        key = f'{DAILY_CHANCE_KEY_PREFIX}{user_id}:{today.isoformat()}'
        new_used = cache.incr(key)
        
        daily_chance, created = UserDailyChance.objects.get_or_create(
            user_id=user_id,
            date=today,
            defaults={'free_chances_used': 1}
        )
        
        if not created:
            daily_chance.free_chances_used += 1
            daily_chance.save(update_fields=['free_chances_used', 'updated_at'])
        
        return True, settings.DAILY_FREE_CHANCES - int(new_used)

    def reset_daily_chances(self, user_id: int, today: date = None):
        if today is None:
            today = date.today()
        
        key = f'{DAILY_CHANCE_KEY_PREFIX}{user_id}:{today.isoformat()}'
        cache.delete(key)
        
        UserDailyChance.objects.filter(user_id=user_id, date=today).update(
            free_chances_used=0,
            paid_chances_used=0
        )

    def get_client_ip(self, request) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def clear_rate_limit(self, user_id: int):
        key = f'{RATE_LIMIT_KEY_PREFIX}{user_id}'
        cache.delete(key)

    def clear_all_user_cache(self, user_id: int):
        today = date.today()
        chance_key = f'{DAILY_CHANCE_KEY_PREFIX}{user_id}:{today.isoformat()}'
        rate_key = f'{RATE_LIMIT_KEY_PREFIX}{user_id}'
        cache.delete_many([chance_key, rate_key])
