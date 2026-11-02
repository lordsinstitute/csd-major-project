# Image-Based Poultry Disease Detection and Farm Analytics Dashboard

A Flask web application where farmers upload a photo of chicken faeces, get a
disease prediction from a traditional machine-vision model (no deep learning),
and track their flock health on an analytics dashboard.

The model predicts one of four classes: **Healthy, Coccidiosis, Salmonella,
Newcastle**, with a confidence score and a risk level.

> This tool gives an automated image-based estimate. It is not a veterinary
> diagnosis. If birds are sick or dying, contact a veterinarian.

## Features

- Farmer registration, login and logout (hashed passwords, CSRF, rate limiting)
- Image upload with real validation and re-encoding
- Disease prediction: confidence, risk level, recommendations and disease info
- Every scan saved with batch name, bird counts, date and image
- History page with search, filters (disease, risk, date range) and pagination
- Dashboard: 4 summary cards and 6 Chart.js charts
- Analytics page: sick vs dead birds, farm-wise, disease-wise, batch-wise, trend insight
- Export of the filtered records as CSV and PDF

## Tech stack

| Area | Tools |
|---|---|
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js |
| Backend | Python, Flask, Flask-Login, Flask-WTF, Flask-SQLAlchemy, Flask-Limiter |
| Database | SQLite |
| Machine learning | numpy, Pillow, opencv-python, scikit-image, scikit-learn, scipy, joblib |
| Reports | reportlab |

## How the model works

1. Resize the image to 128x128 and apply a light Gaussian blur.
2. Extract features:
   - **HOG** (shapes and edges)
   - **Colour** (HSV histograms, RGB mean and standard deviation)
   - **Texture** (LBP histogram and GLCM statistics)
3. Combine them into one vector (1884 numbers).
4. `RandomForestClassifier(n_estimators=200)` gives `predict()` and `predict_proba()`.

Risk level (from the confidence of the predicted class): above 90 is High,
70 to 90 is Medium, below 70 is Low. A Healthy prediction is always shown as Low
(`RISK_HEALTHY_IS_LOW` in `config.py`).

## Project structure

```
app.py                 application factory and entry point
config.py              settings (development, production, testing)
extensions.py          rate limiter
train_model.py         trains the Random Forest from your dataset
database/              SQLAlchemy instance and init script
models/                Farmer and DiseaseRecord models
routes/                blueprints: auth, main, scan, history, analytics, export
utils/                 forms, image handling, features, ML service, analytics, export
templates/  static/    Jinja2 pages, CSS and JavaScript
dataset/               training images (one folder per class)
ml_model/              trained model (created by train_model.py)
uploads/               uploaded images (private, served only to their owner)
tests/                 automated test suite
```

## Setup

```bash
python -m venv venv
# Windows: venv\Scripts\activate      Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python -m database.init_db      # optional: the app also creates tables on start
```

## Dataset and training

Put your images in these folders (names must match exactly):

```
dataset/Healthy/
dataset/Coccidiosis/
dataset/Salmonella/
dataset/Newcastle/
```

Then train:

```bash
python train_model.py
```

The script prints the test accuracy, per-class precision and recall, a
confusion matrix and cross-validation accuracy. It saves
`ml_model/poultry_rf_model.joblib` and `ml_model/metrics.json`.
Useful options: `--dataset PATH`, `--test-size 0.2`, `--skip-cv`.

Tips for trustworthy results:

- Use at least 100 images per class when possible.
- Use different photos in every class. Near-duplicate or augmented copies of one
  photo spread over training and testing inflate the accuracy number.
- Newcastle disease is mainly recognised by respiratory and nervous signs, so a
  droppings photo alone may not separate it reliably from other diseases.
  Check the confusion matrix.
- Load only model files you trained yourself. A `.joblib` file is a Python pickle.

## Run

```bash
python app.py
```

Open http://127.0.0.1:5000, register a farmer account, log in, then upload an image.
Until the model is trained, the Analyze button is disabled with an explanation.

## Configuration

| Setting | How to change | Default |
|---|---|---|
| `SECRET_KEY` | environment variable | random key stored in `.secret_key` |
| `APP_ENV` | `development`, `production` or `testing` | `development` |
| `DATABASE_URL` | environment variable | `database/poultry.db` (SQLite) |
| `DASHBOARD_SCOPE` | `own` (each farmer sees their data) or `all` (shared view) | `own` |
| `RATELIMIT_STORAGE_URI` | environment variable | `memory://` |
| Other values | `config.py` (page size, upload size, thresholds, limits) | |

## Tests

```bash
pip install -r requirements-dev.txt
pytest
pytest tests/test_auth.py -v      # one file
```

Tests use an in-memory database and temporary folders, so they never touch your
real data. The prediction tests use a tiny model trained on synthetic coloured
images. They prove the pipeline works, not the real accuracy of your model.

## Security notes

- Passwords are stored only as salted Werkzeug hashes.
- All forms and the logout action use CSRF tokens.
- Login and registration are rate limited per IP address.
- The login error message is the same for a wrong email and a wrong password.
- Uploaded images are verified with Pillow, re-encoded (this removes EXIF/GPS data),
  renamed randomly, and served only to the farmer who uploaded them.
- CSV export neutralises spreadsheet formula injection.

## Deployment notes

- Set `APP_ENV=production` (secure cookies require HTTPS) and a fixed `SECRET_KEY`.
- Run behind a production server (for example `gunicorn app:app`), not `python app.py`.
- With several server processes, set `RATELIMIT_STORAGE_URI` to a shared store such
  as Redis. The default in-memory store counts per process.
- Behind a reverse proxy, configure the proxy headers (Werkzeug `ProxyFix`),
  otherwise every visitor appears to share the proxy's IP address for rate limiting.
- Back up `database/poultry.db` and `uploads/`.

## Known limitations

- The PDF uses the built-in Helvetica font, which covers Latin characters only.
- Per-class probabilities are shown only right after an analysis (the database
  stores the predicted class and its confidence).
- Orphaned uploads (a farmer closes the browser during the review step) stay in
  `uploads/` until that farmer uploads again.
- Records cannot be edited or deleted from the interface.
