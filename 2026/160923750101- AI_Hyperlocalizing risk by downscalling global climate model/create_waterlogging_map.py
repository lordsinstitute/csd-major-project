
import pandas as pd
import folium
import os

# Load geographic data
water_file = "data/raw/hyderabad_waterlogging_locations.csv"
boundary_file = "data/raw/ghmc_boundary_coordinates.csv"

water = pd.read_csv(water_file)
boundary = pd.read_csv(boundary_file)

# Create map centered on Hyderabad
m = folium.Map(
    location=[17.3850, 78.4867],
    zoom_start=11,
    tiles=None
)

# Add waterlogging hotspot markers
for _, row in water.iterrows():
    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        popup=row["location_name"],
        tooltip=row["location_name"],
        icon=folium.Icon(color="red", icon="warning-sign")
    ).add_to(m)

# Draw GHMC boundary, preserving vertex order
for ring_number, ring in boundary.groupby("ring_number", sort=True):
    ring = ring.sort_values("vertex_number")

    coordinates = list(zip(ring["latitude"], ring["longitude"]))

    folium.PolyLine(
        locations=coordinates,
        color="blue",
        weight=2,
        opacity=0.7,
        tooltip="GHMC Boundary"
    ).add_to(m)

# Save map
os.makedirs("outputs", exist_ok=True)

output_file = "outputs/hyderabad_waterlogging_map.html"
m.save(output_file)

print("Map created successfully!")
print("Waterlogging locations mapped:", len(water))
print("Boundary rings drawn:", boundary["ring_number"].nunique())
print("Saved at:", output_file)
