# TrustLens - AI-Based Fake Review, Bot Detection and User Trust Analysis (Streamlit)

No login. No database. One command opens the website in your browser.

## Run it
1. Open the trustlens folder in VS Code and open the terminal there
2. (first time only)   pip install -r requirements.txt
3. python app.py         <- the browser opens by itself  (python run.py or streamlit run app.py also work)
4. First time: open "Check a Review" and press "Train model now" (about 1 minute). Or run:  python -m ml.train

## IMPORTANT: the dataset
data/fake reviews dataset.csv is a SAMPLE I generated (20,000 reviews) so the project runs on day one.
It is NOT real Amazon data. On it the models score about 74-79% (computed honestly, nothing is fixed or capped).
For your viva: the numbers must come from the real data. Download the real Kaggle file, copy it into the data folder (any name .csv is fine),
delete the sample, then train again (Model Performance page -> Train again).

## Pages
| Page | What it does |
|---|---|
| Home | Summary, how it works, trust levels |
| Check a Review | Type a review -> fake/genuine, trust gauge, highlighted words, Why list. Optional reviewer behaviour -> bot check |
| Check a CSV File | Many reviews at once. Add user_id (and date) columns -> bot detection table. Download results |
| Model Performance | Results table of 4 models, charts, confusion matrix, retrain |

## Read the code in this order
| Step | File | What it does |
|---|---|---|
| 1 | ml/load_data.py | Loads the CSV, 1 = fake, 0 = real, takes up to 10,000 balanced reviews |
| 2 | ml/clean.py | Lowercase, remove tags and symbols |
| 3 | ml/features.py | TF-IDF: words -> numbers |
| 4 | ml/behavior.py | Risk from reviews in one day and account age |
| 5 | ml/bot.py | User trust score and bot status |
| 6 | ml/score.py | Review trust score 0-100 and the 3 levels |
| 7 | ml/explain.py | Top words and the highlighted review |
| 8 | ml/train.py | Trains LR, SVM, Random Forest, XGBoost, keeps best F1 |
| - | ml/predict.py | Joins all steps for one review or many |
| - | ml/batch.py | CSV mode and bot detection per user |
| - | app.py | The Streamlit website (only screen code, no ML) |
| - | run.py | Starts the website and opens the browser |

## Where behaviour comes from (no database)
- Manual mode: you type reviews in 24 hours and account age in the "Reviewer behaviour" box
- CSV mode: counted from the user_id and date columns

## Troubleshooting
| Problem | Fix |
|---|---|
| Browser did not open | Open http://localhost:8501 |
| Port already in use | Close the old terminal (Ctrl + C) and run again |
| No module named ... | pip install -r requirements.txt (inside your venv) |
| Dataset error | Needs columns: label (CG/OR or fake/real) and text_ (or review_text) |
