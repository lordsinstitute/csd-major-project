# MIRAGE — Multimodal Market Manipulation Early-Warning Platform

MIRAGE is a research prototype that combines social chatter and market microstructure features to flag patterns consistent with coordinated pump-and-dump activity. It is an alerting/analyst-support tool, not a trading system or a definitive accusation of manipulation.

## What is included
- FastAPI backend with replay/demo endpoints and typed schemas.
- NLP stream: FinBERT adapter (optional model download), sentiment scoring fallback, mention-burst z-score.
- Price stream: OHLCV feature engineering, Isolation Forest and Prophet residual adapters (optional dependencies).
- Temporal fusion: PyTorch cross-attention model with a deterministic heuristic fallback.
- SHAP-compatible explanation interface and transparent feature-contribution fallback.
- Synthetic reproducible demo data, evaluation script, tests, SQL schema and Docker setup.
- React + Vite dashboard that follows the Lovable prototype's Live Monitor / Backtest / Pipeline / Settings / About information architecture.
- Project report, system design, API reference, data dictionary, model card and demo guide.

## Important scope and truthfulness notes
The linked Lovable app currently exposes a **simulated replay feed** (e.g. PUMPX, simulated social posts, replay speed and a threshold control). This repository includes synthetic demo/replay behavior and a backend contract to connect the interface. It does **not** claim that Reddit, X, Telegram or exchange credentials are configured, that live ingestion is operating, or that the model has achieved measured predictive performance. External ingestion adapters are deliberately configuration-gated and must be implemented/authorized per provider terms.

The pitch specifies FinBERT, rolling mention-rate z-score, Isolation Forest / Prophet, cross-attention and SHAP. The implementation provides working demo paths and optional integrations; install the `ml` extra and download model weights to activate the heavier model components.

## Quick start (Windows PowerShell)
1. Install Python 3.11+ and Node.js 20+.
2. Extract the project ZIP.
3. Backend:
   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   uvicorn app.main:app --reload --port 8000
   ```
4. Frontend (new terminal):
   ```powershell
   cd frontend
   npm install
   Copy-Item .env.example .env
   npm run dev
   ```
5. Open `http://localhost:5173`. API docs: `http://localhost:8000/docs`.

## Demo mode
The default backend uses deterministic synthetic PUMPX-like data. Start backend and frontend, select Replay, and inspect `/api/v1/replay`. Do not interpret the generated values as live market data.

## Optional ML dependencies
```bash
pip install -r requirements-ml.txt
```
FinBERT weights are downloaded from Hugging Face on first use if enabled. This may require substantial disk space, RAM and internet access. To keep development lightweight, `USE_FINBERT=false` is the default.

## Tests and evaluation
```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
python -m scripts.generate_dataset --rows 1000
python -m scripts.evaluate_baselines
```
Metrics are computed on synthetic labelled examples and are only pipeline smoke tests. Replace with a leakage-controlled, independently labelled historical dataset before reporting scientific results.

## Architecture
`docs/SYSTEM_DESIGN.md` and `docs/API_REFERENCE.md` describe component boundaries and endpoints. The dashboard consumes the backend; it does not connect directly to social or exchange providers.

## Security and operations
- Never commit API keys. Configure secrets in environment variables or a secret manager.
- Respect platform API terms, rate limits, privacy and data-retention rules.
- Validate timestamps, symbols, payload sizes and source authenticity.
- Add authentication, authorization, rate limiting, audit logs and TLS before public deployment.
- Store all timestamps in UTC; keep source and ingestion metadata for traceability.

## Team ownership (from pitch)
1. Text stream: social ingestion, FinBERT, mention bursts and labelled text data.
2. Price stream: exchange OHLCV ingestion, anomaly models and feature definitions.
3. Fusion & systems: cross-attention, SHAP, API/database/dashboard integration and evaluation.

## License
Academic prototype. Add an institutional or open-source license only after the team agrees on ownership and third-party dependency obligations.
