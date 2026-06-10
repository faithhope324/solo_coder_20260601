from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count
from django.utils import timezone
from .models import UserProfile, Prize, LotteryRecord, UserDailyChance
from .lottery_algorithm import LotteryAlgorithm
from . import tasks


@admin.register(UserProfile)
class UserProfileAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'phone', 'total_points', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar', 'total_points')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'phone', 'is_staff', 'is_active'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('groups')


@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin):
    list_display = ('prize_type_display', 'name', 'probability', 'current_stock', 'total_stock', 'points_value', 'is_active', 'sort_order', 'stock_progress')
    list_filter = ('prize_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('sort_order', 'prize_type')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['sync_stock_to_redis', 'sync_all_stock', 'clear_cache', 'activate_prizes', 'deactivate_prizes']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'prize_type', 'description', 'image')
        }),
        ('概率与库存', {
            'fields': ('probability', 'total_stock', 'current_stock', 'points_value')
        }),
        ('配置', {
            'fields': ('is_active', 'sort_order')
        }),
        ('系统信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def prize_type_display(self, obj):
        colors = {
            1: '#e74c3c', 2: '#e67e22', 3: '#f39c12', 4: '#2ecc71',
            5: '#3498db', 6: '#9b59b6', 7: '#1abc9c', 8: '#95a5a6'
        }
        color = colors.get(obj.prize_type, '#333')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">{}</span>',
            color, obj.get_prize_type_display()
        )
    prize_type_display.short_description = '奖项等级'
    
    def stock_progress(self, obj):
        if obj.total_stock == 0:
            return format_html('<span style="color: #999;">-</span>')
        
        percentage = (obj.current_stock / obj.total_stock) * 100
        color = '#2ecc71' if percentage > 50 else '#f39c12' if percentage > 20 else '#e74c3c'
        
        return format_html(
            '<div style="width: 120px; height: 16px; background: #eee; border-radius: 8px; overflow: hidden;">'
            '<div style="width: {}%; height: 100%; background: {};"></div>'
            '</div>',
            percentage, color
        )
    stock_progress.short_description = '库存进度'
    
    def sync_stock_to_redis(self, request, queryset):
        algorithm = LotteryAlgorithm()
        count = 0
        for prize in queryset:
            algorithm.sync_stock_to_redis(prize.id)
            tasks.sync_prize_stock_to_redis.delay(prize.id)
            count += 1
        self.message_user(request, f'已同步 {count} 个奖品的库存到 Redis')
    sync_stock_to_redis.short_description = '同步选中奖品库存到 Redis'
    
    def sync_all_stock(self, request, queryset):
        tasks.sync_all_prize_stock_to_redis.delay()
        self.message_user(request, '已异步同步所有奖品库存到 Redis')
    sync_all_stock.short_description = '同步所有奖品库存到 Redis'
    
    def clear_cache(self, request, queryset):
        tasks.clear_lottery_cache.delay()
        self.message_user(request, '已清除抽奖缓存')
    clear_cache.short_description = '清除抽奖缓存'
    
    def activate_prizes(self, request, queryset):
        updated = queryset.update(is_active=True)
        tasks.clear_lottery_cache.delay()
        self.message_user(request, f'已启用 {updated} 个奖品')
    activate_prizes.short_description = '启用选中的奖品'
    
    def deactivate_prizes(self, request, queryset):
        updated = queryset.update(is_active=False)
        tasks.clear_lottery_cache.delay()
        self.message_user(request, f'已禁用 {updated} 个奖品')
    deactivate_prizes.short_description = '禁用选中的奖品'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        tasks.sync_prize_stock_to_redis.delay(obj.id)
        tasks.clear_lottery_cache.delay()


@admin.register(LotteryRecord)
class LotteryRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'prize_info', 'prize_type_display', 'is_win', 'ip_address', 'created_at')
    list_filter = ('prize_type', 'is_win', 'created_at')
    search_fields = ('user__username', 'prize_name', 'ip_address')
    readonly_fields = ('user', 'prize', 'prize_name', 'prize_type', 'is_win', 'ip_address', 'user_agent', 'created_at')
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def prize_info(self, obj):
        if obj.prize:
            return format_html(
                '<a href="/admin/lottery_app/prize/{}/change/">{}</a>',
                obj.prize.id, obj.prize_name
            )
        return obj.prize_name
    prize_info.short_description = '奖品'
    
    def prize_type_display(self, obj):
        colors = {
            1: '#e74c3c', 2: '#e67e22', 3: '#f39c12', 4: '#2ecc71',
            5: '#3498db', 6: '#9b59b6', 7: '#1abc9c', 8: '#95a5a6'
        }
        color = colors.get(obj.prize_type, '#333')
        icon = '🎉' if obj.is_win else '😊'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_prize_type_display()
        )
    prize_type_display.short_description = '奖项'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'prize')
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        today = timezone.now().date()
        today_records = self.get_queryset(request).filter(created_at__date=today)
        
        extra_context['today_stats'] = {
            'total': today_records.count(),
            'win_count': today_records.filter(is_win=True).count(),
            'by_type': today_records.values('prize_type').annotate(count=Count('id')).order_by('prize_type')
        }
        
        return super().changelist_view(request, extra_context)


@admin.register(UserDailyChance)
class UserDailyChanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'free_chances_used', 'paid_chances_used', 'remaining_chances')
    list_filter = ('date',)
    search_fields = ('user__username',)
    readonly_fields = ('user', 'date', 'free_chances_used', 'paid_chances_used')
    date_hierarchy = 'date'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def remaining_chances(self, obj):
        from django.conf import settings
        remaining = settings.DAILY_FREE_CHANCES - obj.free_chances_used
        color = '#2ecc71' if remaining > 1 else '#f39c12' if remaining > 0 else '#e74c3c'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, max(0, remaining)
        )
    remaining_chances.short_description = '剩余次数'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


admin.site.site_header = '抽奖系统管理后台'
admin.site.site_title = '抽奖系统'
admin.site.index_title = '欢迎使用抽奖系统管理后台'
