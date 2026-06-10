import json
from datetime import date
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from .models import Prize, LotteryRecord
from .lottery_algorithm import LotteryAlgorithm
from .redis_service import RedisService
from . import tasks

lottery_algorithm = LotteryAlgorithm()
redis_service = RedisService()


def login_view(request):
    if request.user.is_authenticated:
        return redirect('lottery_index')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('lottery_index')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def index_view(request):
    prizes = Prize.objects.filter(is_active=True).order_by('sort_order', 'id')
    remaining_chances = redis_service.get_remaining_chances(request.user.id)
    
    context = {
        'prizes': prizes,
        'remaining_chances': remaining_chances,
        'daily_free_chances': settings.DAILY_FREE_CHANCES,
    }
    return render(request, 'index.html', context)


@login_required
@require_http_methods(['GET'])
def get_prizes_api(request):
    prizes = Prize.objects.filter(is_active=True).order_by('sort_order', 'id')
    prize_list = []
    
    for prize in prizes:
        stock = lottery_algorithm.get_prize_stock(prize.id)
        prize_list.append({
            'id': prize.id,
            'name': prize.name,
            'prize_type': prize.prize_type,
            'prize_type_display': prize.get_prize_type_display(),
            'description': prize.description,
            'probability': float(prize.probability),
            'stock': stock,
            'points_value': prize.points_value,
            'sort_order': prize.sort_order,
        })
    
    return JsonResponse({
        'success': True,
        'prizes': prize_list
    })


@login_required
@require_http_methods(['GET'])
def get_remaining_chances_api(request):
    remaining = redis_service.get_remaining_chances(request.user.id)
    return JsonResponse({
        'success': True,
        'remaining_chances': remaining,
        'daily_free_chances': settings.DAILY_FREE_CHANCES
    })


@login_required
@require_http_methods(['POST'])
@csrf_exempt
def draw_api(request):
    user = request.user
    
    remaining = redis_service.get_remaining_chances(user.id)
    if remaining <= 0:
        return JsonResponse({
            'success': False,
            'message': '今日抽奖次数已用完，请明天再来',
            'code': 'NO_CHANCES'
        }, status=400)
    
    success, remaining_after = redis_service.consume_chance(user.id)
    if not success:
        return JsonResponse({
            'success': False,
            'message': '消耗抽奖次数失败，请重试',
            'code': 'CONSUME_FAILED'
        }, status=500)
    
    prize, message = lottery_algorithm.draw_prize()
    
    if prize is None:
        return JsonResponse({
            'success': False,
            'message': message,
            'code': 'DRAW_FAILED',
            'remaining_chances': remaining_after
        }, status=400)
    
    ip_address = redis_service.get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    is_win = prize.prize_type < 8
    
    tasks.save_lottery_record.delay(
        user_id=user.id,
        prize_id=prize.id,
        prize_name=prize.name,
        prize_type=prize.prize_type,
        is_win=is_win,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=timezone.now().isoformat()
    )
    
    tasks.send_remaining_chances_update.delay(user.id, remaining_after)
    
    return JsonResponse({
        'success': True,
        'message': '抽奖成功',
        'prize': {
            'id': prize.id,
            'name': prize.name,
            'prize_type': prize.prize_type,
            'prize_type_display': prize.get_prize_type_display(),
            'description': prize.description,
            'points_value': prize.points_value,
            'is_win': is_win,
        },
        'remaining_chances': remaining_after,
        'prize_index': prize.sort_order - 1 if prize.sort_order > 0 else 0
    })


@login_required
@require_http_methods(['GET'])
def get_lottery_records_api(request):
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    offset = (page - 1) * page_size
    
    records = LotteryRecord.objects.filter(user=request.user).order_by('-created_at')[offset:offset + page_size]
    total = LotteryRecord.objects.filter(user=request.user).count()
    
    record_list = []
    for record in records:
        record_list.append({
            'id': record.id,
            'prize_name': record.prize_name,
            'prize_type': record.prize_type,
            'is_win': record.is_win,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse({
        'success': True,
        'records': record_list,
        'total': total,
        'page': page,
        'page_size': page_size
    })
