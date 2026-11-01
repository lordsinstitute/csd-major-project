
import pandas as pd

file_path = "data/processed/hotspot_weather_grid_mapping.csv"

df = pd.read_csv(file_path)

summary = (
    df.groupby("nearest_grid")
    .agg(
        hotspot_count=("location_name", "count"),
        average_distance_km=("distance_km", "mean"),
        maximum_distance_km=("distance_km", "max")
    )
    .reset_index()
)

summary = summary.sort_values(
    "hotspot_count", ascending=False
)

print("\nHOTSPOT DISTRIBUTION BY WEATHER GRID")
print("------------------------------------")
print(summary.to_string(index=False))

print("\nTotal hotspots:", summary["hotspot_count"].sum())
print("Weather grids with hotspots:", len(summary))

summary.to_csv(
    "data/processed/hotspot_grid_distribution.csv",
    index=False
)

print("\nSaved: data/processed/hotspot_grid_distribution.csv")
