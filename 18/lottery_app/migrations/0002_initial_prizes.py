from django.db import migrations


def create_initial_prizes(apps, schema_editor):
    Prize = apps.get_model('lottery_app', 'Prize')
    
    prizes = [
        Prize(
            name='iPhone 15 Pro',
            prize_type=1,
            description='一等奖：最新款 iPhone 手机',
            probability=1.00,
            total_stock=10,
            current_stock=10,
            points_value=10000,
            sort_order=1,
        ),
        Prize(
            name='蓝牙耳机',
            prize_type=2,
            description='二等奖：高品质蓝牙耳机',
            probability=5.00,
            total_stock=100,
            current_stock=100,
            points_value=1000,
            sort_order=2,
        ),
        Prize(
            name='优惠券',
            prize_type=3,
            description='三等奖：100元优惠券',
            probability=14.00,
            total_stock=1000,
            current_stock=1000,
            points_value=100,
            sort_order=3,
        ),
        Prize(
            name='50积分',
            prize_type=4,
            description='四等奖：50积分',
            probability=20.00,
            total_stock=10000,
            current_stock=10000,
            points_value=50,
            sort_order=4,
        ),
        Prize(
            name='20积分',
            prize_type=5,
            description='五等奖：20积分',
            probability=20.00,
            total_stock=10000,
            current_stock=10000,
            points_value=20,
            sort_order=5,
        ),
        Prize(
            name='10积分',
            prize_type=6,
            description='六等奖：10积分',
            probability=20.00,
            total_stock=10000,
            current_stock=10000,
            points_value=10,
            sort_order=6,
        ),
        Prize(
            name='5积分',
            prize_type=7,
            description='七等奖：5积分',
            probability=10.00,
            total_stock=10000,
            current_stock=10000,
            points_value=5,
            sort_order=7,
        ),
        Prize(
            name='谢谢参与',
            prize_type=8,
            description='八等奖：谢谢参与',
            probability=10.00,
            total_stock=999999,
            current_stock=999999,
            points_value=0,
            sort_order=8,
        ),
    ]
    
    Prize.objects.bulk_create(prizes)


def reverse_prizes(apps, schema_editor):
    Prize = apps.get_model('lottery_app', 'Prize')
    Prize.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('lottery_app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_prizes, reverse_prizes),
    ]
