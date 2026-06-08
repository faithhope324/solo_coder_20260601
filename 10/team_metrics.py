import pandas as pd
import numpy as np


def load_matches(csv_path):
    return pd.read_csv(csv_path)


def compute_team_metrics(df):
    teams = sorted(set(df['home_team'].unique()) | set(df['away_team'].unique()))
    metrics = {}

    for team in teams:
        home = df[df['home_team'] == team]
        away = df[df['away_team'] == team]

        played = len(home) + len(away)
        wins = len(home[home['home_goals'] > home['away_goals']]) + len(away[away['away_goals'] > away['home_goals']])
        draws = len(home[home['home_goals'] == home['away_goals']]) + len(away[away['away_goals'] == away['home_goals']])
        losses = played - wins - draws

        goals_scored = home['home_goals'].sum() + away['away_goals'].sum()
        goals_conceded = home['away_goals'].sum() + away['home_goals'].sum()

        avg_possession = (home['home_possession'].sum() + away['away_possession'].sum()) / played
        avg_shots = (home['home_shots'].sum() + away['away_shots'].sum()) / played

        home_goals_scored = home['home_goals'].sum()
        home_goals_conceded = home['away_goals'].sum()
        away_goals_scored = away['away_goals'].sum()
        away_goals_conceded = away['home_goals'].sum()

        home_games = len(home)
        away_games = len(away)

        offensive_index = (goals_scored / played) * 0.4 + (avg_shots / 10) * 0.3 + (avg_possession / 100) * 0.3
        defensive_index = 1.0 / ((goals_conceded / played) * 0.6 + (1 - avg_possession / 100) * 0.2 + 0.2)

        points = wins * 3 + draws * 1

        metrics[team] = {
            'played': played,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_scored': int(goals_scored),
            'goals_conceded': int(goals_conceded),
            'goal_diff': int(goals_scored - goals_conceded),
            'points': points,
            'avg_possession': round(avg_possession, 1),
            'avg_shots': round(avg_shots, 1),
            'offensive_index': round(offensive_index, 3),
            'defensive_index': round(defensive_index, 3),
            'home_goals_scored': int(home_goals_scored),
            'home_goals_conceded': int(home_goals_conceded),
            'away_goals_scored': int(away_goals_scored),
            'away_goals_conceded': int(away_goals_conceded),
            'home_games': home_games,
            'away_games': away_games,
        }

    result_df = pd.DataFrame.from_dict(metrics, orient='index')
    result_df.index.name = 'team'
    result_df = result_df.reset_index()
    result_df = result_df.sort_values(by=['points', 'goal_diff', 'goals_scored'], ascending=False)
    result_df['rank'] = range(1, len(result_df) + 1)

    return result_df


def compute_home_away_win_rates(df):
    teams = sorted(set(df['home_team'].unique()) | set(df['away_team'].unique()))
    records = []

    for team in teams:
        home = df[df['home_team'] == team]
        away = df[df['away_team'] == team]

        home_games = len(home)
        away_games = len(away)

        home_wins = len(home[home['home_goals'] > home['away_goals']])
        home_draws = len(home[home['home_goals'] == home['away_goals']])
        away_wins = len(away[away['away_goals'] > away['home_goals']])
        away_draws = len(away[away['away_goals'] == away['home_goals']])

        home_win_rate = home_wins / home_games if home_games > 0 else 0
        home_draw_rate = home_draws / home_games if home_games > 0 else 0
        home_loss_rate = 1 - home_win_rate - home_draw_rate
        away_win_rate = away_wins / away_games if away_games > 0 else 0
        away_draw_rate = away_draws / away_games if away_games > 0 else 0
        away_loss_rate = 1 - away_win_rate - away_draw_rate

        records.append({
            'team': team,
            'home_win_rate': round(home_win_rate, 3),
            'home_draw_rate': round(home_draw_rate, 3),
            'home_loss_rate': round(home_loss_rate, 3),
            'away_win_rate': round(away_win_rate, 3),
            'away_draw_rate': round(away_draw_rate, 3),
            'away_loss_rate': round(away_loss_rate, 3),
        })

    return pd.DataFrame(records)
