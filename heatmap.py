import random
import folium
from folium.plugins import HeatMap

# 10 NYC locations
entry_points = {
    "Brooklyn Bridge": (40.7061, -73.9969),
    "Queensboro Bridge": (40.7570, -73.9543),
    "Queens Midtown Tunnel": (40.7440, -73.9713),
    "West Side Highway at 60th St": (40.7713, -73.9916),
    "West 60th St": (40.7690, -73.9851),
    "Manhattan Bridge": (40.7075, -73.9903),
    "Lincoln Tunnel": (40.7608, -74.0021),
    "Holland Tunnel": (40.7256, -74.0119),
    "FDR Drive at 60th St": (40.7625, -73.9595),
    "FDR Drive at 34th St": (40.7448, -73.9721)
}

# Create a map centered around Manhattan
m = folium.Map(location=[40.7580, -73.9855], zoom_start=12, tiles='CartoDB positron')

# Build [lat, lon, intensity] for each location (random for demo)
heat_data = []
for name, (lat, lon) in entry_points.items():
    intensity = random.randint(50, 200)
    heat_data.append([lat, lon, intensity])

# Add static HeatMap layer
HeatMap(heat_data, radius=40, min_opacity=0.2, max_opacity=0.7).add_to(m)

# Save map to an HTML file and print a message
m.save("nyc_heatmap.html")
print("Created nyc_heatmap.html. Open it in a browser to see the heatmap!")
