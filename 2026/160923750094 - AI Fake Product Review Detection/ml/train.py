import os
import sys
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from ml.config import MODEL_DIR
from ml.load_data import load_reviews, find_dataset
from ml.clean import clean_text
from ml.features import make_vectorizer


def main(path=None, progress=None):
    def say(text, fraction):
        print(text)
        if progress:
            progress(text, fraction)

    path = path or find_dataset()
    say("Loading and cleaning reviews...", 0.05)
    df = load_reviews(path)
    df["clean"] = df["review_text"].apply(clean_text)

    X_train_text, X_test_text, y_train, y_test = train_test_split(
        df["clean"], df["label"], test_size=0.2, random_state=42, stratify=df["label"])

    say("Turning text into numbers (TF-IDF)...", 0.15)
    vectorizer = make_vectorizer()
    X_train = vectorizer.fit_transform(X_train_text)
    X_test = vectorizer.transform(X_test_text)

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "SVM": CalibratedClassifierCV(LinearSVC(), cv=3),     # wrapped so it can give probabilities
        "Random Forest": RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=200, max_depth=6, eval_metric="logloss"),
    }

    rows, trained, predictions = [], {}, {}
    for i, (name, model) in enumerate(models.items()):
        say(f"Training {name}...", 0.25 + 0.15 * i)
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        rows.append({"Model": name,
                     "Accuracy": accuracy_score(y_test, pred), "Precision": precision_score(y_test, pred),
                     "Recall": recall_score(y_test, pred), "F1": f1_score(y_test, pred)})
        trained[name], predictions[name] = model, pred

    results = pd.DataFrame(rows).round(4)
    print(results.to_string(index=False))
    best = results.sort_values("F1", ascending=False).iloc[0]["Model"]
    print("\nBest model:", best)

    say("Saving the best model...", 0.95)
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(vectorizer, os.path.join(MODEL_DIR, "vectorizer.joblib"))
    joblib.dump(trained[best], os.path.join(MODEL_DIR, "best_model.joblib"))
   
    joblib.dump(trained["Logistic Regression"], os.path.join(MODEL_DIR, "explainer.joblib"))
    results.to_csv(os.path.join(MODEL_DIR, "results.csv"), index=False)

    meta = {"best": best, "dataset": os.path.basename(path), "reviews_used": int(len(df)),
            "train_rows": int(len(y_train)), "test_rows": int(len(y_test)),
            "confusion": confusion_matrix(y_test, predictions[best], labels=[0, 1]).tolist()}
    with open(os.path.join(MODEL_DIR, "meta.json"), "w") as f:
        json.dump(meta, f)
    say("Done.", 1.0)
    return results


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
