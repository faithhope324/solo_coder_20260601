import folium
from folium.plugins import HeatMap
import os


def generate_heatmap(heatmap_data, output_path='static/heatmap.html'):
    if not heatmap_data:
        m = folium.Map(location=[39.9042, 116.4074], zoom_start=11)
        folium.Marker(
            [39.9042, 116.4074],
            popup='暂无数据'
        ).add_to(m)
        m.save(output_path)
        return output_path
    
    center_lat = sum(d['lat'] for d in heatmap_data) / len(heatmap_data)
    center_lon = sum(d['lon'] for d in heatmap_data) / len(heatmap_data)
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    
    heat_data = [[d['lat'], d['lon'], d['count'] * d['weight']] for d in heatmap_data]
    
    HeatMap(
        heat_data,
        min_opacity=0.3,
        radius=25,
        blur=15,
        max_zoom=13,
        gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}
    ).add_to(m)
    
    for d in heatmap_data[:15]:
        folium.CircleMarker(
            location=[d['lat'], d['lon']],
            radius=8,
            popup=f"<strong>{d['region']}</strong><br>行程数: {d['count']:,}",
            color='black',
            fill=True,
            fill_color='red',
            fill_opacity=0.7,
            weight=1
        ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)
    
    return output_path


def generate_region_marker_map(region_stats, output_path='static/region_map.html'):
    m = folium.Map(location=[39.9042, 116.4074], zoom_start=10)
    
    for row in region_stats.head(10).itertuples():
        from region_aggregation import get_region_coordinates
        lat, lon = get_region_coordinates(row.region)
        
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(f"""
                <strong>{row.region}</strong><br>
                行程数: {row.trip_count:,}<br>
                总车费: ¥{row.total_fare:,.2f}<br>
                平均车费: ¥{row.avg_fare:.2f}<br>
                平均距离: {row.avg_distance:.1f}公里
            """, max_width=300),
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)
    
    return output_path
