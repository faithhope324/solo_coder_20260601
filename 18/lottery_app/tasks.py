import logging
from celery import shared_task
from django.db import models
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import LotteryRecord, UserProfile, Prize

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def save_lottery_record(self, user_id, prize_id, prize_name, prize_type, 
                        is_win, ip_address, user_agent, created_at=None):
    try:
        if created_at is None:
            created_at = timezone.now()
        
        prize = None
        if prize_id:
            try:
                prize = Prize.objects.get(id=prize_id)
            except Prize.DoesNotExist:
                pass
        
        record = LotteryRecord.objects.create(
            user_id=user_id,
            prize=prize,
            prize_name=prize_name,
            prize_type=prize_type,
            is_win=is_win,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=created_at
        )
        
        if is_win and prize and prize.points_value > 0:
            UserProfile.objects.filter(id=user_id).update(
                total_points=models.F('total_points') + prize.points_value
            )
        
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{user_id}',
                {
                    'type': 'lottery_result',
                    'record_id': record.id,
                    'prize_name': prize_name,
                    'prize_type': prize_type,
                    'is_win': is_win,
                    'created_at': created_at.isoformat()
                }
            )
        except Exception as e:
            logger.warning(f'WebSocket notification failed: {e}')
        
        return {
            'success': True,
            'record_id': record.id,
            'user_id': user_id,
            'prize_name': prize_name
        }
        
    except Exception as e:
        logger.error(f'Failed to save lottery record: {e}', exc_info=True)
        self.retry(exc=e, countdown=60)
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def send_remaining_chances_update(user_id, remaining_chances):
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}',
            {
                'type': 'chances_update',
                'remaining_chances': remaining_chances
            }
        )
        return True
    except Exception as e:
        logger.warning(f'Failed to send chances update: {e}')
        return False


@shared_task
def sync_prize_stock_to_redis(prize_id):
    from .lottery_algorithm import LotteryAlgorithm
    algorithm = LotteryAlgorithm()
    algorithm.sync_stock_to_redis(prize_id)
    return True


@shared_task
def sync_all_prize_stock_to_redis():
    from .lottery_algorithm import LotteryAlgorithm
    algorithm = LotteryAlgorithm()
    algorithm.sync_all_stock_to_redis()
    return True


@shared_task
def clear_lottery_cache():
    from .lottery_algorithm import LotteryAlgorithm
    algorithm = LotteryAlgorithm()
    algorithm.clear_cache()
    return True
