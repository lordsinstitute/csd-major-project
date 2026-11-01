
import pandas as pd

print("Loading training dataset...")

df = pd.read_csv(
    "data/processed/rainfall_training_data.csv"
)

df["time"] = pd.to_datetime(df["time"])

print("\nYEARLY RAINFALL DISTRIBUTION")
print("--------------------------------")

for year, group in df.groupby(df["time"].dt.year):

    rain = group["rain_next_1h"]

    print(f"\nYear: {year}")
    print("Total records:", len(group))
    print("Rainy hours:", (rain >= 0.1).sum())
    print("Hours >= 1 mm:", (rain >= 1).sum())
    print("Hours >= 5 mm:", (rain >= 5).sum())
    print("Hours >= 10 mm:", (rain >= 10).sum())
    print("Maximum rainfall:", rain.max())

print("\nAnalysis completed!")
