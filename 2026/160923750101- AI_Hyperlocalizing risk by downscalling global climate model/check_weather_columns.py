
import pandas as pd

file_path = "data/raw/hyderabad_multi_grid_historical.csv"

weather = pd.read_csv(file_path)

print("\nWEATHER DATA COLUMN NAMES")
print("-------------------------")

for column in weather.columns:
    print(column)

print("\nFIRST 5 ROWS")
print("-------------")
print(weather.head().to_string())

print("\nTOTAL ROWS:", len(weather))
