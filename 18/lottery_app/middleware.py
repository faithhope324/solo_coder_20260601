import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .redis_service import RedisService


class RateLimitMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.redis_service = RedisService()
        self.limited_paths = ['/api/draw/', '/draw/']

    def __call__(self, request):
        if request.user.is_authenticated and self._should_limit(request):
            allowed, wait_time = self.redis_service.check_rate_limit(request.user.id)
            if not allowed:
                return JsonResponse({
                    'success': False,
                    'message': f'操作过于频繁，请在 {wait_time} 秒后重试',
                    'code': 'RATE_LIMITED',
                    'wait_time': wait_time
                }, status=429)
        
        response = self.get_response(request)
        return response

    def _should_limit(self, request):
        path = request.path
        for limited_path in self.limited_paths:
            if path.startswith(limited_path) and request.method == 'POST':
                return True
        return False

    def process_view(self, request, view_func, view_args, view_kwargs):
        return None
