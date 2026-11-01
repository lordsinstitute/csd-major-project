
import requests
import pandas as pd
from pathlib import Path
import time

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

URL = "https://archive-api.open-meteo.com/v1/archive"

all_data = []

print("Collecting 3-year historical weather for 8 grids...\n")

for grid_name, (lat, lon) in grids.items():

    params = {
        "latitude": lat,
        "longitude": lon,
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

    try:
        response = requests.get(
            URL,
            params=params,
            timeout=120
        )
        response.raise_for_status()

        data = response.json()
        hourly = data["hourly"]

        df = pd.DataFrame(hourly)

        df.insert(0, "grid_name", grid_name)
        df.insert(1, "latitude", data["latitude"])
        df.insert(2, "longitude", data["longitude"])

        all_data.append(df)

        print(
            "Collected:",
            grid_name,
            "| Records:",
            len(df)
        )

    except requests.exceptions.RequestException as error:
        print("Failed:", grid_name, error)

    time.sleep(1)

if all_data:

    final_df = pd.concat(all_data, ignore_index=True)

    output_folder = Path("data/raw")
    output_folder.mkdir(parents=True, exist_ok=True)

    output_file = (
        output_folder /
        "hyderabad_multi_grid_historical.csv"
    )

    final_df.to_csv(output_file, index=False)

    print("\nHistorical collection completed!")
    print("Successful grids:", final_df["grid_name"].nunique())
    print("Total records:", len(final_df))
    print("Saved:", output_file)

else:
    print("No historical data collected.")
