
import requests
import pandas as pd
from pathlib import Path

# Hyderabad central coordinates
LATITUDE = 17.3850
LONGITUDE = 78.4867

URL = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": "2023-01-01",
    "end_date": "2025-12-31",
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "rain",
        "wind_speed_10m",
        "surface_pressure"
    ],
    "timezone": "Asia/Kolkata"
}

print("Downloading historical Hyderabad weather...")

try:
    response = requests.get(URL, params=params, timeout=120)
    response.raise_for_status()

    data = response.json()
    hourly = data["hourly"]

    df = pd.DataFrame(hourly)

    df.insert(0, "latitude", LATITUDE)
    df.insert(1, "longitude", LONGITUDE)

    output_folder = Path("data/raw")
    output_folder.mkdir(parents=True, exist_ok=True)

    output_file = output_folder / "hyderabad_historical_weather.csv"

    df.to_csv(output_file, index=False)

    print("\nHistorical data collected successfully!")
    print("Total records:", len(df))
    print("Start:", df["time"].iloc[0])
    print("End:", df["time"].iloc[-1])
    print("Saved:", output_file)

    print("\nFirst 5 records:")
    print(df.head())

except requests.exceptions.RequestException as error:
    print("\nHistorical data download failed.")
    print(error)

