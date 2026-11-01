
import pandas as pd
import os

water_file = "data/raw/hyderabad_waterlogging_locations.csv"
boundary_file = "data/raw/ghmc_boundary_coordinates.csv"

print("Checking ClimateGuard AI geographic data...")

if os.path.exists(water_file):
    water = pd.read_csv(water_file)
    print("\nWaterlogging locations:")
    print("Total locations:", len(water))
    print(water.head())
else:
    print("Waterlogging CSV not found!")

if os.path.exists(boundary_file):
    boundary = pd.read_csv(boundary_file)
    print("\nGHMC boundary:")
    print("Total boundary points:", len(boundary))
    print(boundary.head())
else:
    print("GHMC boundary CSV not found!")
