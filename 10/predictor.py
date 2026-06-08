import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score


class MatchPredictor:
    def __init__(self):
        self.model = LogisticRegression(max_iter=1000, solver='lbfgs')
        self.scaler = StandardScaler()
        self.team_stats = None
        self.trained = False

    def _build_features(self, df):
        teams = sorted(set(df['home_team'].unique()) | set(df['away_team'].unique()))
        team_stats = {}

        for team in teams:
            home = df[df['home_team'] == team]
            away = df[df['away_team'] == team]
            played = len(home) + len(away)
            if played == 0:
                continue

            goals_scored = home['home_goals'].sum() + away['away_goals'].sum()
            goals_conceded = home['away_goals'].sum() + away['home_goals'].sum()
            avg_possession = (home['home_possession'].sum() + away['away_possession'].sum()) / played
            avg_shots = (home['home_shots'].sum() + away['away_shots'].sum()) / played

            home_goals_scored_avg = home['home_goals'].mean() if len(home) > 0 else 0
            home_goals_conceded_avg = home['away_goals'].mean() if len(home) > 0 else 0
            away_goals_scored_avg = away['away_goals'].mean() if len(away) > 0 else 0
            away_goals_conceded_avg = away['home_goals'].mean() if len(away) > 0 else 0

            team_stats[team] = {
                'avg_gf': goals_scored / played,
                'avg_ga': goals_conceded / played,
                'avg_poss': avg_possession,
                'avg_shots': avg_shots,
                'home_gf_avg': home_goals_scored_avg,
                'home_ga_avg': home_goals_conceded_avg,
                'away_gf_avg': away_goals_scored_avg,
                'away_ga_avg': away_goals_conceded_avg,
            }

        self.team_stats = team_stats

        features = []
        labels = []

        for _, row in df.iterrows():
            ht = row['home_team']
            at = row['away_team']

            if ht not in team_stats or at not in team_stats:
                continue

            hs = team_stats[ht]
            as_ = team_stats[at]

            feat = [
                hs['avg_gf'] - as_['avg_ga'],
                as_['avg_gf'] - hs['avg_ga'],
                hs['avg_poss'] - as_['avg_poss'],
                hs['avg_shots'] - as_['avg_shots'],
                hs['home_gf_avg'] - as_['away_ga_avg'],
                as_['away_gf_avg'] - hs['home_ga_avg'],
                hs['home_gf_avg'],
                hs['home_ga_avg'],
                as_['away_gf_avg'],
                as_['away_ga_avg'],
            ]

            if row['home_goals'] > row['away_goals']:
                label = 0
            elif row['home_goals'] == row['away_goals']:
                label = 1
            else:
                label = 2

            features.append(feat)
            labels.append(label)

        return np.array(features), np.array(labels)

    def train(self, df):
        X, y = self._build_features(df)
        if len(X) < 5:
            return 0.0

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.trained = True

        try:
            scores = cross_val_score(self.model, X_scaled, y, cv=min(5, len(X) // 2), scoring='accuracy')
            return round(scores.mean(), 3)
        except Exception:
            return round(self.model.score(X_scaled, y), 3)

    def predict(self, home_team, away_team):
        if not self.trained or home_team not in self.team_stats or away_team not in self.team_stats:
            return None

        hs = self.team_stats[home_team]
        as_ = self.team_stats[away_team]

        feat = [
            hs['avg_gf'] - as_['avg_ga'],
            as_['avg_gf'] - hs['avg_ga'],
            hs['avg_poss'] - as_['avg_poss'],
            hs['avg_shots'] - as_['avg_shots'],
            hs['home_gf_avg'] - as_['away_ga_avg'],
            as_['away_gf_avg'] - hs['home_ga_avg'],
            hs['home_gf_avg'],
            hs['home_ga_avg'],
            as_['away_gf_avg'],
            as_['away_ga_avg'],
        ]

        X = np.array([feat])
        X_scaled = self.scaler.transform(X)

        proba = self.model.predict_proba(X_scaled)[0]
        pred = self.model.predict(X_scaled)[0]

        result_map = {0: '主胜', 1: '平局', 2: '客胜'}

        return {
            'prediction': result_map[pred],
            'home_win_prob': round(proba[0], 3),
            'draw_prob': round(proba[1], 3),
            'away_win_prob': round(proba[2], 3),
        }
