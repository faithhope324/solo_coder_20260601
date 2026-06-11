from flask import Flask, render_template
from log_parser import LogParser
from funnel_calculator import FunnelCalculator
from chart_generator import ChartGenerator

app = Flask(__name__)

BEHAVIOR_PATH = 'data/user_behavior.csv'
PRODUCTS_PATH = 'data/products.csv'

parser = LogParser(BEHAVIOR_PATH, PRODUCTS_PATH)
calculator = FunnelCalculator(parser)
chart_gen = ChartGenerator(calculator)
charts = chart_gen.generate_all_charts()


@app.route('/')
def dashboard():
    overall_funnel = calculator.overall_funnel
    overall_abandon_rate = calculator.get_overall_abandonment_rate()
    
    device_funnel = calculator.device_funnel
    
    anomaly_sessions = parser.get_anomaly_sessions(min_cart_items=10)
    
    top_categories = calculator.get_top_abandon_categories(10)
    
    peak_hours = calculator.get_peak_abandon_hours(3)
    
    stats = {
        'total_sessions': len(parser.sessions),
        'total_cart_sessions': len(parser.get_cart_sessions()),
        'total_payment_sessions': len(parser.get_payment_sessions()),
        'overall_abandon_rate': overall_abandon_rate,
        'anomaly_count': len(anomaly_sessions)
    }
    
    return render_template(
        'dashboard.html',
        stats=stats,
        funnel_data=overall_funnel,
        device_funnel=device_funnel,
        charts=charts,
        anomaly_sessions=anomaly_sessions[:50],
        top_categories=top_categories,
        peak_hours=peak_hours
    )


@app.route('/api/anomaly')
def api_anomaly():
    from flask import jsonify
    anomalies = parser.get_anomaly_sessions(min_cart_items=10)
    return jsonify({
        'total': len(anomalies),
        'data': anomalies[:100]
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
