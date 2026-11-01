
import pandas as pd
from pathlib import Path

file_path = Path(
    "data/raw/hyderabad_multi_location_weather.csv"
)

print("=" * 50)
print("       CLIMATEGUARD AI - DATA ANALYSIS")
print("=" * 50)

# Load dataset
df = pd.read_csv(file_path)

# Convert time into datetime
df["time"] = pd.to_datetime(df["time"])

# Create useful time-based features
df["hour"] = df["time"].dt.hour
df["day"] = df["time"].dt.day
df["month"] = df["time"].dt.month

# Check missing values
print("\n1. Dataset Information")
print("Total records:", len(df))
print("Total localities:", df["location"].nunique())
print("Total columns:", len(df.columns))

print("\n2. Missing Values")
print(df.isnull().sum())

# Average weather by locality
print("\n3. Average Weather by Locality")

summary = df.groupby("location").agg(
    avg_temperature=("temperature_2m", "mean"),
    avg_humidity=("relative_humidity_2m", "mean"),
    avg_rainfall=("precipitation", "mean"),
    max_rainfall=("precipitation", "max"),
    avg_wind=("wind_speed_10m", "mean")
).round(2)

print(summary)

# Save processed dataset
output_folder = Path("data/processed")
output_folder.mkdir(parents=True, exist_ok=True)

df.to_csv(
    output_folder / "weather_features.csv",
    index=False
)

summary.to_csv(
    output_folder / "locality_weather_summary.csv"
)

print("\n4. Processed files saved successfully!")
print("Folder: data/processed")
