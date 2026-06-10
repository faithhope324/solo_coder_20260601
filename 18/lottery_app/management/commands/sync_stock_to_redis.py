from django.core.management.base import BaseCommand, CommandError
from lottery_app.lottery_algorithm import LotteryAlgorithm
from lottery_app.models import Prize


class Command(BaseCommand):
    help = '同步所有奖品库存到 Redis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--prize-id',
            type=int,
            help='指定奖品 ID 进行同步',
            required=False
        )

    def handle(self, *args, **options):
        algorithm = LotteryAlgorithm()
        prize_id = options.get('prize_id')

        try:
            if prize_id:
                prize = Prize.objects.get(id=prize_id)
                algorithm.sync_stock_to_redis(prize_id)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'成功同步奖品 "{prize.name}" (ID: {prize_id}) 的库存到 Redis，当前库存: {prize.current_stock}'
                    )
                )
            else:
                algorithm.sync_all_stock_to_redis()
                count = Prize.objects.count()
                self.stdout.write(
                    self.style.SUCCESS(f'成功同步 {count} 个奖品的库存到 Redis')
                )
                
                prizes = Prize.objects.all()
                for prize in prizes:
                    stock = algorithm.get_prize_stock(prize.id)
                    self.stdout.write(
                        f'  - {prize.get_prize_type_display()}: {prize.name} (库存: {stock})'
                    )
                    
        except Prize.DoesNotExist:
            raise CommandError(f'奖品 ID {prize_id} 不存在')
        except Exception as e:
            raise CommandError(f'同步失败: {str(e)}')
