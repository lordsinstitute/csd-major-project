
import pandas as pd

print("Loading rainfall training data...")

df = pd.read_csv(
    "data/processed/rainfall_training_data.csv"
)

rain = df["rain_next_1h"]

print("\nRAINFALL DISTRIBUTION")
print("-----------------------------")

print("Total records:", len(rain))
print("Zero-rainfall hours:", (rain == 0).sum())
print("Rainfall hours:", (rain > 0).sum())

print(
    "Percentage of zero-rainfall hours:",
    round((rain == 0).mean() * 100, 2), "%"
)

print("\nRainfall statistics:")
print(rain.describe())

print("\nRainfall thresholds:")
for threshold in [0.1, 1, 2.5, 5, 10]:
    count = (rain >= threshold).sum()
    percentage = count / len(rain) * 100

    print(
        f"Rainfall >= {threshold} mm: "
        f"{count} hours ({percentage:.2f}%)"
    )
