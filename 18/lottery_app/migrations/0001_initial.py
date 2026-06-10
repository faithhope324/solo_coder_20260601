from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='手机号')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='头像')),
                ('total_points', models.IntegerField(default=0, verbose_name='总积分')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': '用户',
                'verbose_name_plural': '用户',
                'db_table': 'user_profile',
            },
        ),
        migrations.CreateModel(
            name='Prize',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='奖品名称')),
                ('prize_type', models.IntegerField(choices=[(1, '一等奖'), (2, '二等奖'), (3, '三等奖'), (4, '四等奖'), (5, '五等奖'), (6, '六等奖'), (7, '七等奖'), (8, '八等奖')], verbose_name='奖项等级')),
                ('description', models.TextField(blank=True, null=True, verbose_name='奖品描述')),
                ('image', models.ImageField(blank=True, null=True, upload_to='prizes/', verbose_name='奖品图片')),
                ('probability', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='中奖概率(%)')),
                ('total_stock', models.IntegerField(default=0, verbose_name='总库存')),
                ('current_stock', models.IntegerField(default=0, verbose_name='当前库存')),
                ('points_value', models.IntegerField(default=0, verbose_name='积分价值')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('sort_order', models.IntegerField(default=0, verbose_name='排序')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '奖品',
                'verbose_name_plural': '奖品',
                'db_table': 'prize',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='LotteryRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prize_name', models.CharField(max_length=100, verbose_name='奖品名称')),
                ('prize_type', models.IntegerField(verbose_name='奖项等级')),
                ('is_win', models.BooleanField(default=True, verbose_name='是否中奖')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP地址')),
                ('user_agent', models.TextField(blank=True, null=True, verbose_name='用户代理')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('prize', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='lottery_app.prize', verbose_name='奖品')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lottery_app.userprofile', verbose_name='用户')),
            ],
            options={
                'verbose_name': '抽奖记录',
                'verbose_name_plural': '抽奖记录',
                'db_table': 'lottery_record',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserDailyChance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='日期')),
                ('free_chances_used', models.IntegerField(default=0, verbose_name='已用免费次数')),
                ('paid_chances_used', models.IntegerField(default=0, verbose_name='已用付费次数')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lottery_app.userprofile', verbose_name='用户')),
            ],
            options={
                'verbose_name': '用户每日抽奖次数',
                'verbose_name_plural': '用户每日抽奖次数',
                'db_table': 'user_daily_chance',
                'unique_together': {('user', 'date')},
            },
        ),
        migrations.AddIndex(
            model_name='lotteryrecord',
            index=models.Index(fields=['user', '-created_at'], name='lottery_rec_user_id_9d5679_idx'),
        ),
        migrations.AddIndex(
            model_name='lotteryrecord',
            index=models.Index(fields=['created_at'], name='lottery_rec_created_7e8d1c_idx'),
        ),
    ]
