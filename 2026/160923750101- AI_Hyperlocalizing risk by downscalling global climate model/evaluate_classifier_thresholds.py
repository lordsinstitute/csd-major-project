
import pandas as pd
import joblib

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

print("Loading test dataset and classifier...")

df = pd.read_csv(
    "data/processed/rainfall_training_data.csv"
)

df["time"] = pd.to_datetime(df["time"])

saved = joblib.load("models/rain_classifier.pkl")

model = saved["model"]
features = saved["features"]

test = df[df["time"].dt.year == 2025].copy()

X_test = test[features]

y_test = (
    test["rain_next_1h"] >= 0.1
).astype(int)

probabilities = model.predict_proba(X_test)[:, 1]

print("\nTHRESHOLD COMPARISON")
print("--------------------------------")

for threshold in [0.3, 0.4, 0.5, 0.6, 0.7]:

    predictions = (
        probabilities >= threshold
    ).astype(int)

    precision = precision_score(
        y_test, predictions, zero_division=0
    )

    recall = recall_score(
        y_test, predictions, zero_division=0
    )

    f1 = f1_score(
        y_test, predictions, zero_division=0
    )

    matrix = confusion_matrix(
        y_test, predictions
    )

    tn, fp, fn, tp = matrix.ravel()

    print(f"\nThreshold: {threshold}")
    print("Precision:", round(precision, 3))
    print("Recall:", round(recall, 3))
    print("F1-score:", round(f1, 3))
    print("False alarms:", fp)
    print("Missed rain events:", fn)
    print("Correct rain detections:", tp)

print("\nThreshold evaluation completed!")
