
import requests
import pandas as pd
from pathlib import Path

# Actual grid coordinates identified by our previous test
grids = {
    "Grid_1": (17.398945, 78.457085),
    "Grid_2": (17.469244, 78.532814),
    "Grid_3": (17.469244, 78.359070),
    "Grid_4": (17.469244, 78.445946),
    "Grid_5": (17.328646, 78.554910),
    "Grid_6": (17.398945, 78.543880),
    "Grid_7": (17.328646, 78.468210),
    "Grid_8": (17.258347, 78.392685)
}

url = "https://api.open-meteo.com/v1/forecast"

all_data = []

print("Collecting unique Hyderabad weather grids...\n")

for grid_name, (lat, lon) in grids.items():

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "rain",
            "wind_speed_10m"
        ],
        "forecast_days": 7,
        "timezone": "Asia/Kolkata"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        hourly = data["hourly"]

        df = pd.DataFrame(hourly)

        df.insert(0, "grid_name", grid_name)
        df.insert(1, "latitude", data["latitude"])
        df.insert(2, "longitude", data["longitude"])

        all_data.append(df)

        print("Collected:", grid_name)

    except requests.exceptions.RequestException as error:
        print("Failed:", grid_name, error)

if all_data:

    final_df = pd.concat(all_data, ignore_index=True)

    output = Path("data/raw")
    output.mkdir(parents=True, exist_ok=True)

    file_path = output / "hyderabad_unique_grid_weather.csv"

    final_df.to_csv(file_path, index=False)

    print("\nCollection completed!")
    print("Unique grids:", final_df["grid_name"].nunique())
    print("Total records:", len(final_df))
    print("Saved:", file_path)

else:
    print("No data collected.")