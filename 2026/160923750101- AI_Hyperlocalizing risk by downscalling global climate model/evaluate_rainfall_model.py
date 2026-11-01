
import pandas as pd
import numpy as np
import joblib

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

print("Loading dataset and trained model...")

df = pd.read_csv(
    "data/processed/rainfall_training_data.csv"
)

df["time"] = pd.to_datetime(df["time"])

features = [
    "latitude",
    "longitude",
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "surface_pressure",
    "hour",
    "month",
    "day_of_year",
    "rain_previous_1h",
    "rain_previous_3h",
    "rain_previous_6h"
]

# Use the same chronological test period as training.
test = df[df["time"].dt.year == 2025].copy()

X_test = test[features]
y_test = test["rain_next_1h"]

print("Loading saved model...")
saved_data = joblib.load("models/rainfall_model.pkl")

print("Saved file type:", type(saved_data))

if isinstance(saved_data, dict):
    print("Saved dictionary keys:", saved_data.keys())
    model = saved_data["model"]
else:
    model = saved_data

predictions = np.maximum(
    model.predict(X_test), 0
)

print("\nPERFORMANCE BY RAINFALL CATEGORY")
print("--------------------------------")

categories = [
    ("All hours", y_test >= 0),
    ("Rainy hours (>= 0.1 mm)", y_test >= 0.1),
    ("Moderate rain (>= 1 mm)", y_test >= 1),
    ("Heavy rain (>= 5 mm)", y_test >= 5)
]

for name, mask in categories:

    actual = y_test[mask]
    predicted = predictions[mask.to_numpy()]

    print(f"\n{name}")
    print("Records:", len(actual))

    if len(actual) == 0:
        print("Not enough records.")
        continue

    mae = mean_absolute_error(actual, predicted)

    rmse = np.sqrt(
        mean_squared_error(actual, predicted)
    )

    print("MAE:", round(mae, 4))
    print("RMSE:", round(rmse, 4))

    if len(actual) > 1:
        print(
            "R2:",
            round(r2_score(actual, predicted), 4)
        )

print("\nEvaluation completed!")
