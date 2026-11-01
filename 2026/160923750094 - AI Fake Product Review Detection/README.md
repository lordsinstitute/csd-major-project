# TrustLens

TrustLens checks online reviews. It tells you if a review is fake, if the reviewer acts like a bot, and gives one trust score from 0 to 100 with reasons (highlighted words).

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Models](#models)
- [Behaviour (Bot) Check](#behaviour-bot-check)
- [Trust Score Formulas](#trust-score-formulas)
- [Results](#results)
- [Explainable AI](#explainable-ai)
- [Installation](#installation)
- [Usage](#usage)
- [CSV Format](#csv-format)
- [Project Structure](#project-structure)
- [Limitations](#limitations)
- [Future Work](#future-work)
- [Tech Stack](#tech-stack)

## Features

| Page | What it does |
|------|--------------|
| Check a Review | One review: verdict, trust gauge, highlighted words |
| Check a CSV File | Many reviews at once, plus a table of the most bot-like users |
| Model Performance | All 4 models compared, with confusion matrix |

## How It Works

| Step | What happens | Why |
|------|--------------|-----|
| 1. Data | Kaggle fake reviews dataset. CG = fake (computer generated), OR = real. We use 10,000 reviews (5,000 + 5,000). | Balanced, so the model cannot cheat by guessing one class |
| 2. Clean | Lowercase, remove tags and symbols. | The same word should look the same |
| 3. TF-IDF | Words become numbers. Special words get high values, common words low. Top 5,000 words and word pairs. | Models only understand numbers |
| 4. Models | Train 4 models, compare them, keep the best by F1. It gives the fake probability (0 to 1). | Choose by evidence, not guess |
| 5. Score | Combine the text result and the behaviour result into one trust score. | One easy number |

## Models

| Model | Simple idea | Role |
|-------|-------------|------|
| Logistic Regression | Gives each word a weight (plus = fake-like, minus = real-like) | Competes AND is always saved as the explainer (red/green words) |
| SVM | Best dividing line between fake and real; good for text | Competes |
| Random Forest | Many decision trees vote | Competes |
| XGBoost | Trees that learn from earlier trees' mistakes | Competes |

The winner (best F1) gives the fake probability on the website.

## Behaviour (Bot) Check

- Two inputs: reviews in the last 24 hours and account age.
- Simple rules give a risk from 0 to 1 (10+ reviews a day = highest risk; an account created today adds risk). The bigger of the two risks is used.
- This part is rule-based, not trained, because the dataset has no user data.
- CSV mode: reviews per user are counted from the user_id and date columns, and the most suspicious users are shown first.

## Trust Score Formulas

| Item | Rule |
|------|------|
| Review trust | 100 x (1 - (0.7 x fake probability + 0.3 x behaviour risk)). No behaviour info: 100 x (1 - fake probability) |
| User trust | 100 x (1 - (0.5 x behaviour risk + 0.5 x average fake probability)) |
| Review level | 70+ Trusted, 40-69 Needs a check, below 40 Likely fake or bot |
| Bot status | 70+ Looks human, 40-69 Suspicious, below 40 Bot-like |
| Verdict | Fake probability 0.5 or more = Fake |

Example: fake probability 0.60, 6 reviews today, account 3 days old.
Behaviour risk = 0.6. Risk = 0.7 x 0.6 + 0.3 x 0.6 = 0.6. Trust = 40 = Needs a check.

## Results

Best model: ____________
Accuracy: ______
Precision: ______
Recall: ______
F1: ______

- Precision: of the reviews we called fake, how many really were fake.
- Recall: of all real fakes, how many we caught.
- F1: balance of both. Used to pick the best model.
- Split: 80% train / 20% test (never-seen reviews).

## Explainable AI

Word contribution = its TF-IDF value in the review x its Logistic Regression weight. Plus pushes toward fake (red), minus pushes toward real (green).

Note: the highlights always come from Logistic Regression, even if another model wins.

## Installation

```bash
git clone https://github.com/your-username/trustlens.git
cd trustlens
pip install -r requirements.txt
```

Download the Kaggle fake reviews dataset and put the file in the data folder. The repository only includes a small sample dataset, so replace it with the real Kaggle file before training.

## Usage

Train the models:

```bash
python train.py
```

Run the website:

```bash
streamlit run app.py
```

Then open the local address shown in the terminal (usually http://localhost:8501).

## CSV Format

| Column | Meaning |
|--------|---------|
| review | The review text |
| user_id | Who wrote the review |
| date | When it was posted |

## Project Structure

```
trustlens/
  data/              Kaggle dataset goes here
  models/            Saved models (joblib)
  train.py           Train and compare the 4 models
  app.py             Streamlit website
  requirements.txt
  README.md
```

## Limitations

1. Fake reviews in the dataset are computer-generated, not real paid reviewers.
2. Behaviour rules and the 70/30 and 50/50 weights are our design choices, not learned from data.
3. English only; TF-IDF does not understand meaning or sarcasm.

## Future Work

- Test on real paid-review data.
- Learn the behaviour weights from real user data instead of fixed rules.
- Support more languages and meaning-aware models.

## Tech Stack

Python, pandas, scikit-learn (TF-IDF, Logistic Regression, SVM, Random Forest), XGBoost, joblib (saves models), Streamlit (website), Plotly (charts)
