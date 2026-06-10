from django.core.management.base import BaseCommand, CommandError
from lottery_app.lottery_algorithm import LotteryAlgorithm


class Command(BaseCommand):
    help = '校验所有启用奖品的概率总和是否为 100%'

    def handle(self, *args, **options):
        algorithm = LotteryAlgorithm()
        
        try:
            valid, total_prob, message = algorithm.validate_probability_sum()
            
            if valid:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ 概率校验通过！当前总和: {total_prob}%'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ 概率校验失败！{message}'
                    )
                )
                
                from lottery_app.models import Prize
                self.stdout.write('\n各奖品概率详情:')
                prizes = Prize.objects.filter(is_active=True).order_by('sort_order', 'id')
                for prize in prizes:
                    self.stdout.write(
                        f'  {prize.get_prize_type_display()}: {prize.name} - {prize.probability}%'
                    )
                
                raise CommandError('概率总和不等于 100%')
                
        except Exception as e:
            raise CommandError(f'校验失败: {str(e)}')
