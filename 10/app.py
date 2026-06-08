import os
from flask import Flask, render_template, request, jsonify

from team_metrics import load_matches, compute_team_metrics, compute_home_away_win_rates
from heatmap import plot_home_away_heatmap, plot_offense_defense_scatter, plot_team_radar
from predictor import MatchPredictor

app = Flask(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'matches.csv')

predictor = MatchPredictor()
model_accuracy = 0.0


def init_app():
    global model_accuracy
    df = load_matches(DATA_PATH)
    model_accuracy = predictor.train(df)


@app.route('/')
def index():
    df = load_matches(DATA_PATH)

    metrics_df = compute_team_metrics(df)
    win_rate_df = compute_home_away_win_rates(df)

    plot_home_away_heatmap(win_rate_df, os.path.join(app.static_folder, 'heatmap.png'))
    plot_offense_defense_scatter(metrics_df, os.path.join(app.static_folder, 'scatter.png'))
    plot_team_radar(metrics_df, os.path.join(app.static_folder, 'radar.png'))

    standings = metrics_df.to_dict('records')
    teams = metrics_df['team'].tolist()

    return render_template('index.html',
                           standings=standings,
                           teams=teams,
                           model_accuracy=model_accuracy)


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    home_team = data.get('home_team')
    away_team = data.get('away_team')

    if not home_team or not away_team:
        return jsonify({'error': '请选择两支球队'}), 400

    if home_team == away_team:
        return jsonify({'error': '主队和客队不能相同'}), 400

    result = predictor.predict(home_team, away_team)
    if result is None:
        return jsonify({'error': '所选球队无可用预测数据'}), 400

    return jsonify(result)


if __name__ == '__main__':
    init_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
