
import pandas as pd
import os
from math import radians, sin, cos, sqrt, atan2

# Load datasets
hotspots = pd.read_csv(
    "data/raw/hyderabad_waterlogging_locations.csv"
)

weather = pd.read_csv(
    "data/raw/hyderabad_multi_grid_historical.csv"
)

# Extract unique weather grid coordinates
grids = weather[
    ["grid_name", "latitude", "longitude"]
].drop_duplicates()

print("Unique weather grid cells:", len(grids))


# Calculate distance in kilometres
def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371

    lat1, lon1, lat2, lon2 = map(
        radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    return 2 * earth_radius * atan2(
        sqrt(a), sqrt(1 - a)
    )


# Match each hotspot to its nearest weather grid
matches = []

for _, hotspot in hotspots.iterrows():

    distances = grids.apply(
        lambda grid: calculate_distance(
            hotspot["latitude"],
            hotspot["longitude"],
            grid["latitude"],
            grid["longitude"]
        ),
        axis=1
    )

    nearest_index = distances.idxmin()
    nearest_grid = grids.loc[nearest_index]

    matches.append({
        "location_name": hotspot["location_name"],
        "hotspot_latitude": hotspot["latitude"],
        "hotspot_longitude": hotspot["longitude"],
        "nearest_grid": nearest_grid["grid_name"],
        "grid_latitude": nearest_grid["latitude"],
        "grid_longitude": nearest_grid["longitude"],
        "distance_km": distances.loc[nearest_index]
    })


# Create mapping results
results = pd.DataFrame(matches)

# Save CSV
os.makedirs("data/processed", exist_ok=True)

output_file = (
    "data/processed/hotspot_weather_grid_mapping.csv"
)

results.to_csv(output_file, index=False)

# Display results
print("\nHOTSPOT TO WEATHER GRID MAPPING")
print("--------------------------------")
print("Total hotspots mapped:", len(results))

print(
    "Unique grids matched:",
    results["nearest_grid"].nunique()
)

print("\nMapping results:")
print(results.to_string(index=False))

print(
    "\nAverage distance:",
    round(results["distance_km"].mean(), 2),
    "km"
)

print(
    "Maximum distance:",
    round(results["distance_km"].max(), 2),
    "km"
)

print("\nSaved successfully:", output_file)
