from log_parser import LogParser
from funnel_calculator import FunnelCalculator
from chart_generator import ChartGenerator

parser = LogParser('data/user_behavior.csv', 'data/products.csv')
calc = FunnelCalculator(parser)
chart_gen = ChartGenerator(calc)
charts = chart_gen.generate_all_charts()
print('All charts generated successfully!')
print(f'Sessions:', len(parser.sessions))
print(f'Overall abandonment rate: {calc.get_overall_abandonment_rate():.2%}')
print(f'Anomaly sessions: {len(parser.get_anomaly_sessions())}')
top3 = calc.get_top_abandon_categories(3)
for c in top3:
    print(f"  - {c['category']}: {c['abandonment_rate']:.2%} ({c['cart_sessions']} cart sessions)")
print(f'\nDevice funnel:')
for device, funnel in calc.device_funnel.items():
    print(f'  {device}:')
    for stage in funnel:
        print(f"    {stage['label']}: {stage['count']} ({stage['conversion_rate']:.2%})")
