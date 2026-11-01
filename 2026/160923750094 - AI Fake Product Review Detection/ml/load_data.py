# STEP 1: Load the Amazon fake review dataset and take up to 10,000 balanced reviews.
import os
import sys
import glob
import pandas as pd

from ml.config import DATA_DIR, DATA_FILE

# Different Kaggle files write the label in different ways. All are understood here.
LABEL_MAP = {"cg": 1, "fake": 1, "1": 1, "1.0": 1,
             "or": 0, "real": 0, "genuine": 0, "0": 0, "0.0": 0}


def find_dataset():
    """Use 'data/fake reviews dataset.csv'. If it is missing, use the first CSV in data/."""
    if os.path.exists(DATA_FILE):
        return DATA_FILE
    others = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
    if others:
        return others[0]
    raise FileNotFoundError("No CSV found in the data folder. Put the Kaggle file inside: " + DATA_DIR)


def load_reviews(path=None, n=10000):
    path = path or find_dataset()
    df = pd.read_csv(path)

    for old in ["text_", "text", "review"]:                 # give the text column one clear name
        if old in df.columns and "review_text" not in df.columns:
            df = df.rename(columns={old: "review_text"})
    if "review_text" not in df.columns or "label" not in df.columns:
        raise ValueError("The dataset needs a text column (text_) and a label column. Found: " + str(list(df.columns)))

    df = df.dropna(subset=["review_text", "label"])
    df["label"] = df["label"].astype(str).str.strip().str.lower().map(LABEL_MAP)  # 1 = fake, 0 = real
    df = df.dropna(subset=["label"])

    half = n // 2
    fake = df[df["label"] == 1]
    real = df[df["label"] == 0]
    fake = fake.sample(min(half, len(fake)), random_state=42)   # same pick every run
    real = real.sample(min(half, len(real)), random_state=42)

    df = pd.concat([fake, real]).sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle
    df["label"] = df["label"].astype(int)
    return df


if __name__ == "__main__":
    df = load_reviews(sys.argv[1] if len(sys.argv) > 1 else None)
    print(df.shape)
    print(df.head())
    print(df["label"].value_counts())
