import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots


class ChartGenerator:
    COLORS = {
        'mobile': '#FF6B6B',
        'pc': '#4ECDC4',
        'overall': '#6C5CE7'
    }

    def __init__(self, funnel_calc):
        self.calc = funnel_calc

    def generate_funnel_chart(self):
        funnel = self.calc.overall_funnel
        labels = [f['label'] for f in funnel]
        values = [f['count'] for f in funnel]
        rates = [f['conversion_rate'] * 100 for f in funnel]

        fig = go.Figure(go.Funnel(
            y=labels,
            x=values,
            textposition='inside',
            textinfo='value+percent initial',
            opacity=0.75,
            marker={
                'color': ['#6C5CE7', '#A29BFE', '#DFE6E9'],
                'line': {'width': [2, 2, 2], 'color': ['white', 'white', 'white']}
            },
            connector={'line': {'color': '#636E72', 'dash': 'solid', 'width': 3}}
        ))

        fig.update_layout(
            title={
                'text': '购物车漏斗转化图',
                'font': {'size': 20}
            },
            showlegend=False,
            height=450,
            margin={'l': 20, 'r': 20, 't': 60, 'b': 20}
        )

        return pio.to_json(fig)

    def generate_device_funnel_chart(self):
        device_funnel = self.calc.device_funnel
        stages = self.calc.STAGE_LABELS
        
        fig = go.Figure()

        device_names = {'mobile': '移动端', 'pc': 'PC端'}
        
        for device_key, device_label in device_names.items():
            if device_key in device_funnel:
                funnel = device_funnel[device_key]
                values = [f['count'] for f in funnel]
                rates = [f['conversion_rate'] * 100 for f in funnel]
                
                fig.add_trace(go.Bar(
                    name=device_label,
                    x=stages,
                    y=values,
                    text=[f'{v:,}<br>({r:.1f}%)' for v, r in zip(values, rates)],
                    textposition='outside',
                    marker_color=self.COLORS.get(device_key, '#6C5CE7'),
                    opacity=0.85
                ))

        fig.update_layout(
            title={
                'text': '按设备分组漏斗转化率对比',
                'font': {'size': 20}
            },
            barmode='group',
            xaxis={'title': {'text': '漏斗阶段'}},
            yaxis={'title': {'text': '会话数'}},
            legend={
                'title': {'text': '设备类型'},
                'orientation': 'h',
                'y': 1.05,
                'x': 0.5,
                'xanchor': 'center'
            },
            height=450,
            margin={'l': 20, 'r': 20, 't': 60, 'b': 20},
            plot_bgcolor='rgba(0,0,0,0.02)'
        )

        return pio.to_json(fig)

    def generate_hourly_abandonment_chart(self):
        hourly = self.calc.hourly_abandonment
        hours = [h['hour_label'] for h in hourly]
        abandon_rates = [h['abandonment_rate'] * 100 for h in hourly]
        add_cart_counts = [h['add_cart'] for h in hourly]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=hours,
                y=add_cart_counts,
                name='加购会话数',
                marker_color='rgba(52, 152, 219, 0.5)',
                yaxis='y'
            )
        )

        fig.add_trace(
            go.Scatter(
                x=hours,
                y=abandon_rates,
                mode='lines+markers',
                name='放弃率',
                line={'color': '#E74C3C', 'width': 3},
                marker={'size': 6, 'color': '#E74C3C'},
                yaxis='y2'
            )
        )

        fig.update_layout(
            title={
                'text': '24小时购物车放弃率趋势',
                'font': {'size': 20}
            },
            xaxis={'title': {'text': '小时'}},
            yaxis={
                'title': {'text': '加购会话数', 'font': {'color': '#3498DB'}},
                'tickfont': {'color': '#3498DB'}
            },
            yaxis2={
                'title': {'text': '放弃率 (%)', 'font': {'color': '#E74C3C'}},
                'tickfont': {'color': '#E74C3C'},
                'overlaying': 'y',
                'side': 'right',
                'tickformat': '.1f',
                'range': [0, 100]
            },
            legend={
                'orientation': 'h',
                'y': 1.05,
                'x': 0.5,
                'xanchor': 'center'
            },
            height=450,
            margin={'l': 20, 'r': 20, 't': 60, 'b': 20},
            plot_bgcolor='rgba(0,0,0,0.02)'
        )

        return pio.to_json(fig)

    def generate_category_abandonment_chart(self):
        top10 = self.calc.get_top_abandon_categories(10)
        categories = [item['category'] for item in reversed(top10)]
        abandon_rates = [item['abandonment_rate'] * 100 for item in reversed(top10)]
        cart_counts = [item['cart_sessions'] for item in reversed(top10)]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                y=categories,
                x=cart_counts,
                mode='lines+markers',
                name='加购会话数',
                line={'color': '#2ECC71', 'width': 2},
                marker={'size': 8, 'color': '#27AE60'},
                xaxis='x'
            )
        )

        fig.add_trace(
            go.Bar(
                y=categories,
                x=abandon_rates,
                name='放弃率',
                orientation='h',
                marker_color='#E74C3C',
                opacity=0.75,
                text=[f'{r:.1f}%' for r in abandon_rates],
                textposition='outside',
                xaxis='x2'
            )
        )

        fig.update_layout(
            title={
                'text': 'Top 10 高放弃率品类',
                'font': {'size': 20}
            },
            yaxis={'title': {'text': ''}},
            xaxis={
                'title': {'text': '加购会话数', 'font': {'color': '#27AE60'}},
                'tickfont': {'color': '#27AE60'},
                'side': 'bottom'
            },
            xaxis2={
                'title': {'text': '放弃率 (%)', 'font': {'color': '#E74C3C'}},
                'tickfont': {'color': '#E74C3C'},
                'overlaying': 'x',
                'side': 'top',
                'range': [0, 100]
            },
            legend={
                'orientation': 'h',
                'y': 1.08,
                'x': 0.5,
                'xanchor': 'center'
            },
            height=500,
            margin={'l': 80, 'r': 20, 't': 60, 'b': 20},
            plot_bgcolor='rgba(0,0,0,0.02)'
        )

        return pio.to_json(fig)

    def generate_all_charts(self):
        return {
            'funnel': self.generate_funnel_chart(),
            'device_funnel': self.generate_device_funnel_chart(),
            'hourly_abandonment': self.generate_hourly_abandonment_chart(),
            'category_abandonment': self.generate_category_abandonment_chart()
        }
