import pandas as pd

from ml.behavior import behavior_risk
from ml.bot import user_trust_score, bot_status
from ml.load_data import LABEL_MAP

TEXT_COLUMNS = ["review_text", "text_", "text", "review"]


def find_text_column(df):
    return next((c for c in TEXT_COLUMNS if c in df.columns), None)


def analyze_dataframe(df, analyzer, max_rows=2000):
    df = df.head(max_rows).copy()
    col = find_text_column(df)
    if col is None:
        raise ValueError("The CSV needs a column named review_text (or text_, text, review).")
    texts = df[col].fillna("").astype(str).tolist()


    has_user = "user_id" in df.columns
    per_day, last24 = {}, None
    if has_user:
        df["user_id"] = df["user_id"].fillna("unknown").astype(str)
        totals = df.groupby("user_id").size().to_dict()
        per_day = dict(totals)                                    
        if "date" in df.columns:                                  
            day = pd.to_datetime(df["date"], errors="coerce").dt.date
            busiest = df.assign(_day=day).groupby(["user_id", "_day"]).size().groupby("user_id").max().to_dict()
            per_day = {u: busiest.get(u, totals[u]) for u in totals}
        last24 = [per_day[u] for u in df["user_id"]]

    results = analyzer.analyze_batch(texts, last24, 999)         
    out = pd.DataFrame(results)
    out.insert(0, "review", [t[:150] for t in texts])
    if has_user:
        out.insert(0, "user_id", df["user_id"].values)

    users = None
    if has_user:
        rows = []
        for uid, g in out.groupby("user_id"):
            risk, why = behavior_risk(int(per_day[uid]), 999)
            avg = g["fake_prob"].mean()
            score = user_trust_score(risk, avg)
            rows.append({"user_id": uid, "reviews": len(g), "max_per_day": int(per_day[uid]),
                         "avg_fake_chance": round(avg * 100), "user_trust": score,
                         "status": bot_status(score), "note": why[0] if why else "Normal posting rate"})
        users = pd.DataFrame(rows).sort_values("user_trust").reset_index(drop=True)

    
    accuracy = None
    if "label" in df.columns:
        truth = df["label"].astype(str).str.strip().str.lower().map(LABEL_MAP)
        if truth.notna().all():
            accuracy = float(((out["verdict"] == "Fake").astype(int).values == truth.astype(int).values).mean())

    return {"reviews": out, "users": users, "has_user": has_user, "accuracy": accuracy, "text_column": col}
