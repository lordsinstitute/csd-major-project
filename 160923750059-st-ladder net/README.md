<div align="center">

# 🚦 ST-LadderNet · Hyderabad Traffic Prediction

**Deep learning traffic forecasting for Hyderabad, from data collection to a live dashboard.**

Based on the IEEE paper *ST-LadderNet: Spatial-Temporal Correlation Stepply Enhanced Deep Learning Model for Urban Traffic Predicting*.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-st--laddernet.vercel.app-000?logo=vercel)](https://st-laddernet.vercel.app)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-ST--LadderNet-EE4C2C?logo=pytorch&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-REST%20API-000?logo=flask)
![SQLite](https://img.shields.io/badge/DB-SQLite%20%7C%20PostgreSQL-003B57?logo=sqlite&logoColor=white)

**[🌐 Live demo](https://st-laddernet.vercel.app)** · [Quick start](#-quick-start) · [Results](#-results-nyc-taxi-benchmark) · [API](#-rest-api) · [Team](#-team)

<!-- Add a screenshot: save one as docs/dashboard.png and it will show here -->
<img src="docs/dashboard.png" alt="ST-LadderNet dashboard showing the Hyderabad traffic map, KPIs and forecasts" width="900">

</div>

---

## 📌 About

Urban traffic depends on **where** (a jam spreads to nearby roads) and **when** (rush hours repeat daily and weekly). Many models learn these one after the other. **ST-LadderNet** learns them together:

- A **Ladder CNN** looks at a small 3×3 neighbourhood for the newest readings and climbs to 5×5 and 7×7 for older ones, because congestion takes time to travel from further away.
- A **GRU** learns how traffic changes over time and fuses the spatial features into a forecast.

This project turns that idea into a working system. It collects road speeds for 12 major Hyderabad corridors, stores them in a database, forecasts each road **15, 30, 45 and 60 minutes ahead**, and shows everything on a web dashboard.

## ✨ Features

- 🗺️ **Live traffic map** of 12 Hyderabad corridors (NH 65, Gachibowli, Tank Bund, LB Nagar and more), coloured by congestion level, with English and Telugu labels
- 🔮 **Forecasts 15–60 minutes ahead** for every road, with a "best time to leave" suggestion
- 🔔 **Congestion alerts** for roads predicted to jam in the next hour
- 📊 **Analytics**: 6-hour speed trends and the hours when the city usually jams
- 🧠 **ST-LadderNet in PyTorch**, evaluated on the public NYC Taxi benchmark against three baselines
- 🔌 **REST API** (Flask) with 11 JSON endpoints
- 🗄️ **SQLite** out of the box, **PostgreSQL + TimescaleDB** for production
- 📱 Responsive, light and dark mode, and a **demo mode** that runs fully in the browser

## 🏗️ Architecture

```
 TomTom Traffic API ─┐
 OpenWeather API ────┼─► Collector ──► Database ──► Preprocessing ──► ST-LadderNet ──► Flask API ──► Web Dashboard
 Simulator ──────────┘   (every 30 min) (SQLite /    (grid, scaling,   (Ladder CNN      (/api/*)      (Vercel / local)
                                         PostgreSQL)  daily + weekly)   3×3→5×5→7×7
                                                                        + GRU)
 NYC Taxi dataset ─────────────────────────────────► Training & evaluation (RMSE · MAE · MAPE vs. baselines)
```

Until trained weights exist, the backend forecasts with a **baseline** (typical speed for that time of day plus today's deviation, fading over the horizon). Once `ml/weights.pt` exists, it switches to ST-LadderNet automatically.

## 🚀 Quick start

No API keys needed: the app fills itself with 7 days of simulated history so every chart works on first run.

**Requirements:** Python **3.10 or newer** (3.12 recommended).

### Windows (PowerShell)

```powershell
cd st-laddernet
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m backend.app
```

> If activation fails with "running scripts is disabled", run
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` and activate again.

### macOS / Linux

```bash
cd st-laddernet
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m backend.app
```

Wait for `Open http://localhost:8000`, then open **http://localhost:8000**. The badge at the top shows **Live · simulator**. Keep the terminal open while you use the dashboard.

## 🛰️ Use real traffic data

1. Get a free key at [developer.tomtom.com](https://developer.tomtom.com) (Traffic API → Flow Segment Data; 20,000 free calls a month).
2. Copy `.env.example` to `.env` and set `TOMTOM_API_KEY=your_key`.
3. Delete `data/traffic.db` so simulated history isn't mixed with real readings.
4. Run `python -m backend.app`. The badge changes to **Live · TomTom**.

12 roads × every 30 minutes ≈ 17,280 calls a month, which fits the free tier. To add roads, edit `backend/roads.py` (name, free-flow speed and a list of `[lat, lng]` points).

Optional: set `OPENWEATHER_API_KEY` to show weather on the dashboard and store it for the model.

## 🧠 Train and evaluate the model

Install PyTorch (CPU build):

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m ml.model          # quick shape check
```

### NYC Taxi benchmark (no API key needed)

`ml/nyc.py` downloads the public NYC Taxi volume dataset (10 × 20 grid, 30-minute slots, 40 days train / 20 days test, from the [STDN repository](https://github.com/tangxianfeng/STDN)), trains ST-LadderNet and compares it with three baselines.

```bash
python -m ml.nyc --baselines-only   # check the data, no PyTorch needed
python -m ml.nyc                    # train ST-LadderNet (~15–20 min on a laptop CPU)
python -m ml.nyc --no-period        # ablation: without daily/weekly inputs
python -m ml.nyc --dataset bike     # NYC Bike data instead
```

Results are printed as a table and saved to `results/` as CSV and JSON.

### Hyderabad data

After collecting 2–3 weeks of real readings:

```bash
python -m ml.train --days 21 --epochs 40
```

Restart the server and the forecasts switch from "Baseline" to "ST-LadderNet". Training on simulated data only teaches the model the simulator's formula, so use real readings.

## 📈 Results (NYC Taxi benchmark)

Test set: 20 days, cells with more than 10 trips. Lower is better.

| Model | RMSE @30 min | MAE @30 min | MAPE @30 min | RMSE @60 | RMSE @90 | RMSE @120 |
|---|---:|---:|---:|---:|---:|---:|
| Historical average | 38.72 | 21.76 | 21.3% | 38.74 | 38.75 | 38.76 |
| Last value | 34.27 | 20.36 | 22.7% | 54.39 | 72.90 | 88.90 |
| Linear regression | 25.43 | 15.36 | 18.5% | 30.49 | 33.34 | 34.96 |
| ST-LadderNet (initial run) | 46.36 | 25.02 | 26.4% | 48.46 | 52.54 | 58.13 |
| **ST-LadderNet (improved)** | _to be updated_ | | | | | |

The initial run used only the last 4 hours of data, so it missed daily and weekly patterns. The improved version adds same-time-yesterday and same-time-last-week inputs, day-of-week features and a skip connection to the GRU.

## 🔌 REST API

| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | status, data source, reading count, database type |
| GET | `/api/roads` | road catalogue with geometry |
| GET | `/api/live` | latest speed and congestion level per road |
| GET | `/api/predictions?horizon=30` | latest forecast per road (15/30/45/60) |
| GET | `/api/history?hours=6&roads=1,2` | speed time series |
| GET | `/api/roads/<id>?hours=24` | one road: history, forecast, typical profile |
| GET | `/api/alerts` | roads forecast moderate or worse in the next hour |
| GET | `/api/stats` | average speed, congested count, accuracy (1 − MAPE, 24 h) |
| GET | `/api/profile` | % of roads congested by hour of day (IST) |
| GET | `/api/snapshot` | everything above in one call (used by the dashboard) |
| POST | `/api/collect` | force one collection + prediction cycle |

**Congestion levels** use current speed ÷ free-flow speed: above 70% Low, 50–70% Moderate, 35–50% High, below 35% Congested.

## 🗄️ Database

SQLite by default (`data/traffic.db`), no setup. Tables: `roads`, `readings`, `predictions`, `weather`.

For production, PostgreSQL + TimescaleDB (time-series partitioning and retention) + PostGIS:

```bash
docker compose up -d
psql postgresql://traffic:traffic@localhost:5432/traffic -f backend/schema_postgres.sql
pip install "psycopg[binary]"
# in .env:
# DATABASE_URL=postgresql://traffic:traffic@localhost:5432/traffic
```

## 📁 Project structure

```
st-laddernet/
├── backend/
│   ├── app.py              Flask server, API routes, background collector
│   ├── config.py           settings from .env
│   ├── db.py               SQLite / PostgreSQL access
│   ├── roads.py            road catalogue, congestion levels, simulator
│   ├── collector.py        TomTom + OpenWeather fetchers, simulated backfill
│   ├── predictor.py        forecasts (ST-LadderNet or baseline), accuracy scoring
│   ├── services.py         queries that shape the API responses
│   ├── schema_sqlite.sql
│   └── schema_postgres.sql
├── ml/
│   ├── model.py            ST-LadderNet (Ladder CNN + GRU) in PyTorch
│   ├── data.py             Hyderabad readings → city-grid tensors
│   ├── train.py            training on Hyderabad data
│   ├── infer.py            inference used by the backend
│   └── nyc.py              NYC Taxi benchmark: download, train, evaluate
├── frontend/
│   └── index.html          dashboard (vanilla HTML/CSS/JS, no build step)
├── data/                   SQLite database and downloaded datasets
├── results/                benchmark results (CSV / JSON)
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── requirements-ml.txt
```

## 🌐 Deployment

- **Frontend (live demo):** the dashboard is deployed on [Vercel](https://st-laddernet.vercel.app) as a static page. Without a backend it runs in **demo mode**, simulating traffic in the browser.
  ```bash
  npx vercel --prod     # run inside a folder containing the standalone index.html
  ```
- **Full stack:** run `python -m backend.app` on any small VM, Render or Railway, behind a reverse proxy (nginx, Caddy), with a hosted PostgreSQL database such as Neon or Supabase. Run a single process, because the collector thread lives inside the app.

## 🛠️ Tech stack

| Area | Technology |
|---|---|
| Languages | Python 3.12, JavaScript |
| Deep learning | PyTorch (Ladder CNN + GRU) |
| Data processing | NumPy |
| Backend | Flask (REST API) |
| Database | SQLite, PostgreSQL + TimescaleDB |
| Frontend | HTML, CSS, JavaScript, SVG charts, Leaflet + OpenStreetMap |
| External APIs | TomTom Traffic Flow, OpenWeather |
| Deployment | Vercel, Docker |

## 🧩 Troubleshooting

| Problem | Fix |
|---|---|
| `No matching distribution found for flask>=3.0` | Your Python is too old. Install 3.10+ and recreate the venv with `py -3.12 -m venv .venv` |
| `No module named backend` | Run commands from inside the `st-laddernet` folder |
| `No module named flask` | Activate the virtual environment first |
| `127.0.0.1 refused to connect` | The server isn't running. Start `python -m backend.app` and keep that terminal open |
| `Address already in use` | Set `PORT=8001` in `.env` and open http://localhost:8001 |
| Badge still says "simulator" | Check `TOMTOM_API_KEY` in `.env` (the file must be named `.env`, not `.env.txt`), then restart |

## 🗺️ Roadmap

- [x] Data collection, database, REST API
- [x] ST-LadderNet implementation in PyTorch
- [x] Web dashboard with forecasts, alerts and analytics, deployed on Vercel
- [x] NYC Taxi benchmark with baselines
- [ ] Improved ST-LadderNet results and ablation study
- [ ] Live Hyderabad data via TomTom
- [ ] Backend and database hosted online
- [ ] User login, admin panel, route planner, PDF reports

## 👥 Team

| Name | Roll number |
|---|---|
| Mohammed Yaser | 160923750012 |
| Mohammed Idrees | 160923750043 |
| Abdullah | 160923750059 |

**Supervisor:** Mr. Aqeel Haider Shams
**Department:** Computer Science & Engineering (Data Science), Lords Institute of Engineering & Technology, Hyderabad
**Industry partner:** MANAC Infotech

## 📚 References

- *ST-LadderNet: Spatial-Temporal Correlation Stepply Enhanced Deep Learning Model for Urban Traffic Predicting*, [IEEE Xplore](https://ieeexplore.ieee.org/document/10858917/)
- NYC Taxi volume dataset from [STDN (Yao et al., AAAI 2019)](https://github.com/tangxianfeng/STDN)
- [TomTom Traffic Flow API](https://developer.tomtom.com) · [OpenWeather API](https://openweathermap.org/api) · Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors

## 📄 License

This is an academic project. Add a license file (for example MIT) before publishing if you want others to reuse the code.
