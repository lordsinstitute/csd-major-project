"""
Train the poultry disease classifier (Random Forest + traditional features).

Usage:
    python train_model.py
    python train_model.py --dataset path/to/dataset --test-size 0.2
    python train_model.py --skip-cv

Expected dataset layout (folder names must match exactly):
    dataset/Healthy/*.jpg
    dataset/Coccidiosis/*.jpg
    dataset/Salmonella/*.jpg
    dataset/Newcastle/*.jpg
"""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

from config import Config
from utils.feature_extraction import FEATURE_VERSION, IMAGE_SIZE, extract_features

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MIN_IMAGES_PER_CLASS = 10
RANDOM_STATE = 42


def parse_args():
    """Read command line options."""
    parser = argparse.ArgumentParser(description="Train the poultry disease model.")
    parser.add_argument(
        "--dataset", type=Path, default=Config.DATASET_DIR,
        help="Folder that contains one sub-folder per class.",
    )
    parser.add_argument(
        "--test-size", type=float, default=0.2,
        help="Fraction of images kept aside for testing (default 0.2).",
    )
    parser.add_argument(
        "--skip-cv", action="store_true",
        help="Skip the 5-fold cross validation (faster).",
    )
    return parser.parse_args()


def list_images(class_dir):
    """Return all image files directly inside a class folder."""
    return sorted(
        path for path in class_dir.iterdir()
        if path.is_file()
        and not path.name.startswith(".")
        and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def file_hash(path):
    """SHA-256 of the file bytes, used to drop exact duplicate images."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_dataset(dataset_dir, classes):
    """
    Extract features for every image.

    Returns (features, labels, summary). Unreadable files and exact
    duplicates are skipped and reported.
    """
    features, labels = [], []
    seen_hashes = set()
    skipped_unreadable, skipped_duplicates = [], 0

    for class_name in classes:
        class_dir = dataset_dir / class_name
        if not class_dir.is_dir():
            sys.exit(f"Missing dataset folder: {class_dir}")

        paths = list_images(class_dir)
        print(f"\n{class_name}: {len(paths)} files found")

        for index, path in enumerate(paths, start=1):
            digest = file_hash(path)
            if digest in seen_hashes:
                skipped_duplicates += 1
                continue
            try:
                vector = extract_features(path)
            except ValueError:
                skipped_unreadable.append(str(path))
                continue
            seen_hashes.add(digest)
            features.append(vector)
            labels.append(class_name)

            if index % 100 == 0:
                print(f"   processed {index}/{len(paths)}")

    summary = {
        "unreadable": skipped_unreadable,
        "duplicates": skipped_duplicates,
    }
    return np.array(features, dtype=np.float32), np.array(labels), summary


def build_classifier():
    """Random Forest with 200 trees; class weights handle uneven class sizes."""
    return RandomForestClassifier(
        n_estimators=Config.RF_N_ESTIMATORS,
        class_weight="balanced",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )


def print_confusion_matrix(matrix, classes):
    """Print a readable confusion matrix (rows = true, columns = predicted)."""
    width = max(len(name) for name in classes) + 2
    print("\nConfusion matrix (rows = true class, columns = predicted class)")
    print(" " * width + "".join(name[:11].rjust(13) for name in classes))
    for name, row in zip(classes, matrix):
        print(name.ljust(width) + "".join(str(value).rjust(13) for value in row))


def main():
    """Load data, evaluate on a held-out split, train the final model, save it."""
    args = parse_args()
    classes = list(Config.CLASSES)
    started = time.time()

    print("Dataset folder:", args.dataset)
    features, labels, summary = load_dataset(args.dataset, classes)

    if summary["duplicates"]:
        print(f"\nSkipped {summary['duplicates']} exact duplicate images.")
    for bad_file in summary["unreadable"]:
        print("Skipped unreadable file:", bad_file)

    counts = {name: int(np.sum(labels == name)) for name in classes}
    print("\nImages used per class:", counts)
    too_few = [name for name, total in counts.items() if total < MIN_IMAGES_PER_CLASS]
    if too_few:
        sys.exit(
            f"Each class needs at least {MIN_IMAGES_PER_CLASS} images. "
            f"Too few for: {', '.join(too_few)}"
        )
    print("Feature vector length:", features.shape[1])

    # ------------------------------------------------------------------
    # Honest evaluation: the test images are never used for training
    # ------------------------------------------------------------------
    x_train, x_test, y_train, y_test = train_test_split(
        features, labels,
        test_size=args.test_size,
        stratify=labels,
        random_state=RANDOM_STATE,
    )
    print(f"\nTraining on {len(x_train)} images, testing on {len(x_test)} images ...")
    evaluator = build_classifier().fit(x_train, y_train)
    predicted = evaluator.predict(x_test)

    accuracy = float(accuracy_score(y_test, predicted))
    report_text = classification_report(y_test, predicted, labels=classes, zero_division=0)
    report_dict = classification_report(
        y_test, predicted, labels=classes, zero_division=0, output_dict=True
    )
    matrix = confusion_matrix(y_test, predicted, labels=classes)

    print(f"\nTest accuracy: {accuracy * 100:.2f}%\n")
    print(report_text)
    print_confusion_matrix(matrix, classes)

    cv_scores = None
    if not args.skip_cv:
        folds = min(5, min(counts.values()))
        if folds >= 2:
            print(f"\nRunning {folds}-fold cross validation ...")
            splitter = StratifiedKFold(
                n_splits=folds, shuffle=True, random_state=RANDOM_STATE
            )
            cv_scores = cross_val_score(
                build_classifier(), features, labels, cv=splitter
            )
            print(
                f"Cross-validation accuracy: {cv_scores.mean() * 100:.2f}% "
                f"(+/- {cv_scores.std() * 100:.2f})"
            )

    # ------------------------------------------------------------------
    # Final model: trained on every image, so no data is wasted
    # ------------------------------------------------------------------
    print("\nTraining the final model on the full dataset ...")
    final_model = build_classifier().fit(features, labels)

    metrics = {
        "test_accuracy": round(accuracy, 4),
        "cv_accuracy_mean": round(float(cv_scores.mean()), 4) if cv_scores is not None else None,
        "cv_accuracy_std": round(float(cv_scores.std()), 4) if cv_scores is not None else None,
        "test_images": int(len(x_test)),
        "per_class": {
            name: {
                "precision": round(report_dict[name]["precision"], 4),
                "recall": round(report_dict[name]["recall"], 4),
                "f1": round(report_dict[name]["f1-score"], 4),
            }
            for name in classes
        },
        "confusion_matrix": matrix.tolist(),
        "classes": classes,
    }

    bundle = {
        "model": final_model,
        "classes": [str(name) for name in final_model.classes_],
        "feature_version": FEATURE_VERSION,
        "n_features": int(features.shape[1]),
        "image_size": list(IMAGE_SIZE),
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_samples": int(len(labels)),
        "class_counts": counts,
        "metrics": metrics,
    }

    # Write to a temporary file first so a running app never reads a half-written model
    model_path = Path(Config.MODEL_PATH)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = model_path.with_suffix(".tmp")
    joblib.dump(bundle, temp_path, compress=3)
    temp_path.replace(model_path)

    metrics_path = model_path.parent / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("\nModel saved to:  ", model_path)
    print("Metrics saved to:", metrics_path)
    print(f"Finished in {time.time() - started:.1f} seconds.")
    print(
        "\nNote: the accuracy above is only meaningful if the test images are "
        "genuinely different from the training images (see README notes)."
    )


if __name__ == "__main__":
    main()
    
