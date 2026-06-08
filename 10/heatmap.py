import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os


def plot_home_away_heatmap(win_rate_df, save_path='static/heatmap.png'):
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    teams = win_rate_df['team'].tolist()
    n = len(teams)

    data = np.zeros((n, 6))
    for i, row in win_rate_df.iterrows():
        idx = teams.index(row['team'])
        data[idx] = [
            row['home_win_rate'],
            row['home_draw_rate'],
            row['home_loss_rate'],
            row['away_win_rate'],
            row['away_draw_rate'],
            row['away_loss_rate'],
        ]

    columns = ['主胜', '主平', '主负', '客胜', '客平', '客负']

    fig, ax = plt.subplots(figsize=(11, max(6, n * 0.8)))

    sns.heatmap(
        data,
        xticklabels=columns,
        yticklabels=teams,
        annot=True,
        fmt='.2f',
        cmap='RdYlGn',
        linewidths=0.5,
        ax=ax,
        vmin=0,
        vmax=1,
        cbar_kws={'label': '胜率'},
    )

    ax.set_title('主客场胜率热力图', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('比赛结果类型', fontsize=11)
    ax.set_ylabel('球队', fontsize=11)

    plt.tight_layout()

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return save_path


def plot_offense_defense_scatter(metrics_df, save_path='static/scatter.png'):
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(10, 8))

    x = metrics_df['offensive_index']
    y = metrics_df['defensive_index']

    scatter = ax.scatter(x, y, c=metrics_df['points'], cmap='viridis', s=120, edgecolors='black', linewidth=0.5, zorder=5)

    for _, row in metrics_df.iterrows():
        ax.annotate(row['team'], (row['offensive_index'], row['defensive_index']),
                     textcoords="offset points", xytext=(5, 5), fontsize=8)

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('积分', fontsize=10)

    ax.set_xlabel('进攻指数', fontsize=11)
    ax.set_ylabel('防守指数', fontsize=11)
    ax.set_title('球队攻防指数散点图', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return save_path


def plot_team_radar(metrics_df, save_path='static/radar.png'):
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    categories = ['进攻', '防守', '控球', '射门', '胜率', '净胜球']
    N = len(categories)

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(11, 10), subplot_kw=dict(polar=True))
    fig.subplots_adjust(right=0.75)

    norm_metrics = metrics_df.copy()
    for col, src in [
        ('off_norm', 'offensive_index'),
        ('def_norm', 'defensive_index'),
        ('pos_norm', 'avg_possession'),
        ('sho_norm', 'avg_shots'),
        ('wr_norm', 'wins'),
        ('gd_norm', 'goal_diff'),
    ]:
        vals = norm_metrics[src]
        mn, mx = vals.min(), vals.max()
        norm_metrics[col] = (vals - mn) / (mx - mn) if mx > mn else 0.5

    top_teams = norm_metrics.head(5)

    cmap = plt.cm.Set2
    for i, (_, row) in enumerate(top_teams.iterrows()):
        values = [row['off_norm'], row['def_norm'], row['pos_norm'], row['sho_norm'], row['wr_norm'], row['gd_norm']]
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=1.5, label=row['team'], color=cmap(i / 5))
        ax.fill(angles, values, alpha=0.1, color=cmap(i / 5))

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=9)
    ax.set_title('Top 5 球队雷达图', fontsize=14, fontweight='bold', y=1.08)
    ax.legend(loc='upper right', bbox_to_anchor=(1.45, 1.1), fontsize=8)

    plt.tight_layout()

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return save_path
