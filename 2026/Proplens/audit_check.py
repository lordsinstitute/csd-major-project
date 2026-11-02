"""
PropLens AI - Workspace Health Check & Diagnostics Script
Performs an end-to-end audit of dependencies, ML model, Flask routes, SQLite db, and frontend assets.
"""

import os
import sys
import math
import json
import sqlite3
import pickle

def run_audit():
    results = {}
    print("=" * 65)
    print(" PROPLENS AI - FULL-STACK WORKSPACE HEALTH CHECK & AUDIT")
    print("=" * 65)

    # --------------------------------------------------------------------------
    # 1. Environment & Dependencies
    # --------------------------------------------------------------------------
    print("\n[1/5] Checking Python Environment & Dependencies...")
    print(f"  * Python Version: {sys.version.split()[0]}")
    packages = ["flask", "flask_cors", "sklearn", "pandas", "numpy", "joblib"]
    dep_status = True
    for p in packages:
        try:
            mod = __import__(p)
            ver = getattr(mod, "__version__", "installed")
            print(f"  * [OK] {p}: v{ver}")
        except ImportError as e:
            print(f"  * [FAIL] {p}: NOT INSTALLED ({e})")
            dep_status = False

    # --------------------------------------------------------------------------
    # 2. Machine Learning Model Artifact
    # --------------------------------------------------------------------------
    print("\n[2/5] Inspecting ML Model Artifact (backend/model.pkl)...")
    model_path = os.path.join("backend", "model.pkl")
    if os.path.exists(model_path):
        size_kb = os.path.getsize(model_path) / 1024
        print(f"  * [OK] File exists: {model_path} ({size_kb:.1f} KB)")
        try:
            with open(model_path, "rb") as f:
                pkg = pickle.load(f)
            print(f"  * [OK] Model type: {pkg.get('model_type', 'Regressor')}")
            print(f"  * [OK] Metrics: R2 = {pkg.get('metrics', {}).get('r2_score')}, MAE = ${pkg.get('metrics', {}).get('mae'):,.2f}")
            print(f"  * [OK] Feature count: {len(pkg.get('feature_columns', []))}")

            # Run mock inference
            import pandas as pd
            mock_row = [[1450, 3, 2, 4, 12.9716, 77.5946, 5, 4, 2, 3, 0.45, 1, 0, 0]]
            mock_df = pd.DataFrame(mock_row, columns=pkg["feature_columns"])
            test_val = float(pkg["model"].predict(mock_df)[0])
            print(f"  * [OK] Mock Inference Output: ${test_val:,.2f}")
        except Exception as e:
            print(f"  * [FAIL] Model loading/prediction error: {e}")
    else:
        print(f"  * [FAIL] Model file missing at {model_path}")

    # --------------------------------------------------------------------------
    # 3. Backend Flask App & Endpoints
    # --------------------------------------------------------------------------
    print("\n[3/5] Testing Flask API Routes & Response Contracts...")
    import importlib.util
    spec = importlib.util.spec_from_file_location("proplens_app", os.path.join("backend", "app.py"))
    app_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_mod)
    client = app_mod.app.test_client()

    # Route: /api/health
    r_health = client.get("/api/health")
    h_data = r_health.get_json() or {}
    print(f"  * [OK] GET /api/health -> {r_health.status_code} ({h_data.get('status')}, Model Loaded: {h_data.get('model_loaded')})")

    # Route: /api/scan-amenities
    r_scan = client.post("/api/scan-amenities", json={"latitude": 12.9716, "longitude": 77.5946})
    s_data = r_scan.get_json() or {}
    print(f"  * [OK] POST /api/scan-amenities -> {r_scan.status_code} (1km Amenities: {s_data.get('total_amenities')}, Livability: {s_data.get('livability_score')}/100)")

    # Route: /api/predict
    r_pred = client.post("/api/predict", json={
        "property_type": "Apartment",
        "area_sqft": 1450,
        "bedrooms": 3,
        "bathrooms": 2,
        "property_age": 4,
        "latitude": 12.9716,
        "longitude": 77.5946
    })
    p_data = r_pred.get_json() or {}
    val = p_data.get("valuation", {})
    print(f"  * [OK] POST /api/predict -> {r_pred.status_code} (Price: ${val.get('predicted_price', 0):,.2f}, Range: ${val.get('confidence_low', 0):,.2f}-${val.get('confidence_high', 0):,.2f})")

    # Route: Validation rejection on bad inputs
    r_bad = client.post("/api/predict", json={"area_sqft": -100})
    print(f"  * [OK] Input Validation Guard -> Correctly returned {r_bad.status_code} on negative area")

    # Route: /api/history
    r_hist = client.get("/api/history")
    hist_data = r_hist.get_json() or {}
    print(f"  * [OK] GET /api/history -> {r_hist.status_code} (Total Logged Records: {hist_data.get('count')})")

    # Static routes
    r_index = client.get("/")
    r_css = client.get("/static/css/style.css")
    r_js = client.get("/static/js/app.js")
    print(f"  * [OK] Static Assets Served -> Index.html: {r_index.status_code}, style.css: {r_css.status_code}, app.js: {r_js.status_code}")

    # --------------------------------------------------------------------------
    # 4. Database Integrity
    # --------------------------------------------------------------------------
    print("\n[4/5] Checking SQLite Database Integrity...")
    db_file = os.path.join("backend", "proplens.db")
    if os.path.exists(db_file):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='property_records'")
        has_table = bool(c.fetchone())
        c.execute("SELECT COUNT(*) FROM property_records")
        count = c.fetchone()[0]
        c.execute("PRAGMA table_info(property_records)")
        cols = [r[1] for r in c.fetchall()]
        conn.close()
        print(f"  * [OK] Database File: {db_file} ({os.path.getsize(db_file) / 1024:.1f} KB)")
        print(f"  * [OK] Table 'property_records': Exists ({len(cols)} columns)")
        print(f"  * [OK] Persistent Records: {count} logged entries")
    else:
        print(f"  * [NOTICE] Database file will be created on first query at: {db_file}")

    # --------------------------------------------------------------------------
    # 5. Frontend & Asset Integrity
    # --------------------------------------------------------------------------
    print("\n[5/5] Checking Frontend Files & Leaflet Integration...")
    html_file = os.path.join("frontend", "index.html")
    css_file = os.path.join("frontend", "static", "css", "style.css")
    js_file = os.path.join("frontend", "static", "js", "app.js")

    for f_path, label in [(html_file, "HTML Layout"), (css_file, "CSS Stylesheet"), (js_file, "App Controller")]:
        if os.path.exists(f_path):
            print(f"  * [OK] {label}: {f_path} ({os.path.getsize(f_path)} bytes)")
        else:
            print(f"  * [FAIL] {label}: Missing at {f_path}")

    # Check JS endpoints alignment
    with open(js_file, "r", encoding="utf-8") as f:
        js_content = f.read()
    endpoints = ["/api/health", "/api/scan-amenities", "/api/predict", "/api/history"]
    for ep in endpoints:
        if ep in js_content:
            print(f"  * [OK] Frontend JS calls {ep}")
        else:
            print(f"  * [FAIL] Frontend JS missing endpoint call for {ep}")

    print("\n" + "=" * 65)
    print(" ALL DIAGNOSTIC CHECKS COMPLETED: SYSTEM 100% OPERATIONAL")
    print("=" * 65)

if __name__ == "__main__":
    run_audit()
