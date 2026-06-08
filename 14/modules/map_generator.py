import folium
from folium import plugins
import os


def generate_heatmap(df, center_lat, center_lon, output_dir):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles='OpenStreetMap')

    heat_data = df[['上车纬度', '上车经度']].dropna().values.tolist()

    if heat_data:
        plugins.HeatMap(
            heat_data,
            min_opacity=0.3,
            max_val=1.0,
            radius=15,
            blur=10,
            gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
        ).add_to(m)

    output_path = os.path.join(output_dir, 'heatmap.html')
    m.save(output_path)
    return output_path
