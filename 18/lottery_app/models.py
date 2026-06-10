from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class UserProfile(AbstractUser):
    phone = models.CharField('手机号', max_length=20, blank=True, null=True)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, null=True)
    total_points = models.IntegerField('总积分', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'user_profile'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class Prize(models.Model):
    PRIZE_TYPE_CHOICES = [
        (1, '一等奖'),
        (2, '二等奖'),
        (3, '三等奖'),
        (4, '四等奖'),
        (5, '五等奖'),
        (6, '六等奖'),
        (7, '七等奖'),
        (8, '八等奖'),
    ]

    name = models.CharField('奖品名称', max_length=100)
    prize_type = models.IntegerField('奖项等级', choices=PRIZE_TYPE_CHOICES)
    description = models.TextField('奖品描述', blank=True, null=True)
    image = models.ImageField('奖品图片', upload_to='prizes/', blank=True, null=True)
    probability = models.DecimalField('中奖概率(%)', max_digits=5, decimal_places=2, default=0)
    total_stock = models.IntegerField('总库存', default=0)
    current_stock = models.IntegerField('当前库存', default=0)
    points_value = models.IntegerField('积分价值', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    sort_order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'prize'
        verbose_name = '奖品'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.get_prize_type_display()} - {self.name}'

    def clean(self):
        from django.core.exceptions import ValidationError
        from decimal import Decimal
        
        if self.probability < 0 or self.probability > 100:
            raise ValidationError({'probability': '概率必须在 0-100 之间'})
        
        if self.is_active:
            other_prizes = Prize.objects.filter(is_active=True).exclude(id=self.id)
            total_prob = sum(p.probability for p in other_prizes) + self.probability
            diff = abs(total_prob - Decimal('100'))
            
            if diff > Decimal('0.01'):
                raise ValidationError(
                    f'所有启用奖品的概率总和必须为 100%，当前总和为 {total_prob}%，差值为 {diff}%'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        from .lottery_algorithm import LotteryAlgorithm
        algorithm = LotteryAlgorithm()
        algorithm.clear_cache()


class LotteryRecord(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name='用户')
    prize = models.ForeignKey(Prize, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='奖品')
    prize_name = models.CharField('奖品名称', max_length=100)
    prize_type = models.IntegerField('奖项等级')
    is_win = models.BooleanField('是否中奖', default=True)
    ip_address = models.GenericIPAddressField('IP地址', null=True, blank=True)
    user_agent = models.TextField('用户代理', blank=True, null=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'lottery_record'
        verbose_name = '抽奖记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.prize_name}'


class UserDailyChance(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name='用户')
    date = models.DateField('日期')
    free_chances_used = models.IntegerField('已用免费次数', default=0)
    paid_chances_used = models.IntegerField('已用付费次数', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'user_daily_chance'
        verbose_name = '用户每日抽奖次数'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'date']

    def __str__(self):
        return f'{self.user.username} - {self.date}'
