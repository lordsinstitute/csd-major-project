"""
PropLens AI - Smart Real Estate Pricing Engine & Neighborhood Analyzer
Machine Learning Model Training Pipeline

This script:
1. Generates a realistic synthetic real estate dataset with geospatial & neighborhood amenity features.
2. Trains a high-performance Scikit-Learn Regression Model (Random Forest & Gradient Boosting).
3. Evaluates model performance (R2 score, MAE, RMSE).
4. Exports the trained model pipeline and feature metadata to 'backend/model.pkl'.
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Base directory for saving model
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
IS_VERCEL = bool(os.environ.get("VERCEL"))
if IS_VERCEL:
    MODEL_FILE_PATH = "/tmp/model.pkl"
else:
    MODEL_FILE_PATH = os.path.join(BACKEND_DIR, "model.pkl")

# Reference anchor coordinates (New York City as default realistic urban hub)
BASE_LAT = 40.7128
BASE_LNG = -74.0060

FEATURE_COLUMNS = [
    "area_sqft",
    "bedrooms",
    "bathrooms",
    "property_age",
    "latitude",
    "longitude",
    "transit_stops_1km",
    "schools_1km",
    "hospitals_1km",
    "parks_1km",
    "metro_distance_km",
    "type_Apartment",
    "type_Independent_House",
    "type_Villa"
]


def generate_synthetic_data(n_samples: int = 2500, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates a realistic synthetic dataset of properties with physical
    specifications, geospatial coordinates, and 1km neighborhood amenity density.
    """
    np.random.seed(random_seed)

    property_types = np.random.choice(
        ["Apartment", "Independent_House", "Villa"],
        size=n_samples,
        p=[0.60, 0.25, 0.15]
    )

    # Physical dimensions based on property type
    areas = []
    bedrooms = []
    bathrooms = []

    for p_type in property_types:
        if p_type == "Apartment":
            area = int(np.random.normal(1250, 350))
            area = max(500, min(area, 2800))
            beds = int(np.clip(round(area / 450), 1, 4))
            baths = max(1, beds - np.random.choice([0, 1], p=[0.7, 0.3]))
        elif p_type == "Independent_House":
            area = int(np.random.normal(2200, 500))
            area = max(1100, min(area, 4200))
            beds = int(np.clip(round(area / 500), 2, 5))
            baths = max(2, beds)
        else:  # Villa
            area = int(np.random.normal(3600, 700))
            area = max(2000, min(area, 6500))
            beds = int(np.clip(round(area / 600), 3, 6))
            baths = beds + np.random.choice([0, 1], p=[0.4, 0.6])

        areas.append(area)
        bedrooms.append(beds)
        bathrooms.append(baths)

    property_age = np.random.randint(0, 30, size=n_samples)

    # Coordinates distributed within ~10km of urban center
    lat_offsets = np.random.normal(0, 0.045, size=n_samples)
    lng_offsets = np.random.normal(0, 0.045, size=n_samples)
    latitudes = BASE_LAT + lat_offsets
    longitudes = BASE_LNG + lng_offsets

    # Distance to city center / transit corridor
    dist_from_core = np.sqrt(lat_offsets**2 + lng_offsets**2) * 111.0  # Approx km

    # Amenity counts inversely proportional to distance from center with noise
    transit_stops = np.clip(np.random.poisson(lam=np.maximum(1.0, 9.0 - 0.7 * dist_from_core)), 0, 15)
    schools = np.clip(np.random.poisson(lam=np.maximum(1.0, 6.0 - 0.4 * dist_from_core)), 0, 12)
    hospitals = np.clip(np.random.poisson(lam=np.maximum(1.0, 4.0 - 0.3 * dist_from_core)), 0, 8)
    parks = np.clip(np.random.poisson(lam=np.maximum(1.0, 5.0 - 0.2 * dist_from_core)), 0, 10)
    metro_dist = np.clip(0.3 + 0.5 * dist_from_core + np.random.normal(0, 0.3, size=n_samples), 0.1, 8.0)

    # Realistic Valuation Formula:
    # Base rate per sqft = $180 - $320 depending on location & core distance
    base_sqft_rate = 260.0 - (8.0 * np.clip(dist_from_core, 0, 12)) + np.random.normal(0, 10, size=n_samples)
    base_sqft_rate = np.maximum(140.0, base_sqft_rate)

    raw_price = np.array(areas) * base_sqft_rate
    raw_price += np.array(bedrooms) * 22000.0
    raw_price += np.array(bathrooms) * 14000.0
    raw_price -= property_age * 1600.0  # Age depreciation

    # Amenity value additions
    raw_price += transit_stops * 4500.0
    raw_price += schools * 6000.0
    raw_price += hospitals * 5000.0
    raw_price += parks * 5500.0
    raw_price += np.where(metro_dist <= 1.0, 35000.0, np.maximum(0, 20000.0 - metro_dist * 4000.0))

    # Type premiums
    type_multiplier = np.array([
        1.00 if t == "Apartment" else (1.25 if t == "Independent_House" else 1.55)
        for t in property_types
    ])
    final_price = raw_price * type_multiplier

    # Add realistic market variance (±3%)
    noise = np.random.normal(1.0, 0.03, size=n_samples)
    final_price = np.round(final_price * noise, -2)  # Round to nearest 100

    # Build DataFrame
    df = pd.DataFrame({
        "area_sqft": areas,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "property_age": property_age,
        "property_type": property_types,
        "latitude": latitudes,
        "longitude": longitudes,
        "transit_stops_1km": transit_stops,
        "schools_1km": schools,
        "hospitals_1km": hospitals,
        "parks_1km": parks,
        "metro_distance_km": metro_dist,
        "price": final_price
    })

    # One-hot encode property types
    df["type_Apartment"] = (df["property_type"] == "Apartment").astype(int)
    df["type_Independent_House"] = (df["property_type"] == "Independent_House").astype(int)
    df["type_Villa"] = (df["property_type"] == "Villa").astype(int)

    return df


def train_model(save_path: str = None, n_samples: int = None):
    """
    Trains a Gradient Boosting Regressor, evaluates, and returns the model package.
    Optionally saves the model package to disk.
    """
    if save_path is None:
        save_path = MODEL_FILE_PATH

    if n_samples is None:
        n_samples = 1200 if IS_VERCEL else 2500

    print("=" * 65)
    print(" PropLens AI - Training Smart Real Estate Pricing Engine ")
    print("=" * 65)

    print(f"[1/4] Generating {n_samples:,} synthetic property listings with geospatial features...")
    df = generate_synthetic_data(n_samples=n_samples, random_seed=42)

    X = df[FEATURE_COLUMNS]
    y = df["price"]

    print(f"[2/4] Splitting train (80%) and test (20%) datasets...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    print("[3/4] Fitting Scikit-Learn Gradient Boosting Regressor...")
    model = GradientBoostingRegressor(
        n_estimators=100 if IS_VERCEL else 150,
        learning_rate=0.08,
        max_depth=5,
        subsample=0.85,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Evaluation
    train_preds = model.predict(X_train)
    test_preds = model.predict(X_test)

    r2_train = r2_score(y_train, train_preds)
    r2_test = r2_score(y_test, test_preds)
    mae_test = mean_absolute_error(y_test, test_preds)
    rmse_test = np.sqrt(mean_squared_error(y_test, test_preds))

    print("-" * 65)
    print(f" Model Evaluation Metrics:")
    print(f"  * Training R^2 Score : {r2_train:.4f}")
    print(f"  * Testing R^2 Score  : {r2_test:.4f} (Accuracy Benchmark)")
    print(f"  * Mean Absolute Error: ${mae_test:,.2f}")
    print(f"  * Root Mean Sq Error : ${rmse_test:,.2f}")
    print("-" * 65)

    # Calculate baseline feature importances
    feature_importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_.tolist()))

    package = {
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "metrics": {
            "r2_score": round(float(r2_test), 4),
            "mae": round(float(mae_test), 2),
            "rmse": round(float(rmse_test), 2)
        },
        "feature_importances": feature_importances,
        "base_lat": BASE_LAT,
        "base_lng": BASE_LNG,
        "model_type": "GradientBoostingRegressor",
        "version": "1.0.0"
    }

    if save_path:
        try:
            print(f"[4/4] Saving model artifact to: {save_path}")
            with open(save_path, "wb") as f:
                pickle.dump(package, f)
            print("SUCCESS: Model successfully trained and saved.")
        except Exception as e:
            print(f"Warning: Could not save model to {save_path} ({e}); using in-memory model package.")
    return package


if __name__ == "__main__":
    train_model()
