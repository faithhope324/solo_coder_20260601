from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction


class Command(BaseCommand):
    help = '创建默认管理员账号'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='管理员用户名 (默认: admin)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123456',
            help='管理员密码 (默认: admin123456)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='管理员邮箱 (默认: admin@example.com)'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        password = options['password']
        email = options['email']

        try:
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'用户 "{username}" 已存在，跳过创建')
                )
                user = User.objects.get(username=username)
            else:
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'成功创建管理员账号: {username}')
                )
            
            self.stdout.write('\n账号信息:')
            self.stdout.write(f'  用户名: {username}')
            self.stdout.write(f'  密码: {password}')
            self.stdout.write(f'  邮箱: {email}')
            self.stdout.write(f'  管理员后台: /admin/')
            
        except Exception as e:
            raise CommandError(f'创建管理员账号失败: {str(e)}')
