import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class LotteryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.user_group_name = f'user_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        await self.send_current_chances()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'ping')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
            elif message_type == 'get_chances':
                await self.send_current_chances()
            
        except json.JSONDecodeError:
            logger.warning('Invalid JSON received from WebSocket')
    
    @database_sync_to_async
    def get_remaining_chances(self):
        from .redis_service import RedisService
        redis_service = RedisService()
        return redis_service.get_remaining_chances(self.user.id)
    
    async def send_current_chances(self):
        remaining_chances = await self.get_remaining_chances()
        await self.send(text_data=json.dumps({
            'type': 'chances_update',
            'remaining_chances': remaining_chances
        }))
    
    async def chances_update(self, event):
        remaining_chances = event['remaining_chances']
        await self.send(text_data=json.dumps({
            'type': 'chances_update',
            'remaining_chances': remaining_chances
        }))
    
    async def lottery_result(self, event):
        await self.send(text_data=json.dumps({
            'type': 'lottery_result',
            'record_id': event.get('record_id'),
            'prize_name': event.get('prize_name'),
            'prize_type': event.get('prize_type'),
            'is_win': event.get('is_win'),
            'created_at': event.get('created_at')
        }))
