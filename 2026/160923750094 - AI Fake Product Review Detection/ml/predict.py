import os
import joblib

from ml.config import MODEL_DIR
from ml.clean import clean_text
from ml.behavior import behavior_risk
from ml.bot import user_trust_score, bot_status
from ml.score import trust_score, level_name
from ml.explain import explain_text, top_terms, top_fake_words


class Analyzer:
    def __init__(self):
        paths = {name: os.path.join(MODEL_DIR, name + ".joblib")
                 for name in ["vectorizer", "best_model", "explainer"]}
        for p in paths.values():
            if not os.path.exists(p):
                raise FileNotFoundError("Model not trained yet: " + p)
        self.vectorizer = joblib.load(paths["vectorizer"])
        self.model = joblib.load(paths["best_model"])
        self.explainer = joblib.load(paths["explainer"])

    def analyze(self, text, reviews_last_24h=None, account_age_days=None):
        clean = clean_text(text)
        if not clean:
            return {"trust": 50, "level": "Needs a check", "verdict": "Fake", "fake_prob": 0.5,
                    "behavior_risk": None, "user_trust": None, "bot_status": None,
                    "reasons": ["The review has no readable words."], "terms": []}

        X = self.vectorizer.transform([clean])
        fake_prob = float(self.model.predict_proba(X)[0][1])      

        risk, b_reasons = None, []
        if reviews_last_24h is not None:
            risk, b_reasons = behavior_risk(reviews_last_24h, account_age_days)

        score = trust_score(fake_prob, risk)
        reasons = [f"Text model: {round(fake_prob * 100)}% chance this review is fake."]
        reasons += explain_text(text, self.vectorizer, self.explainer)
        reasons += b_reasons

        user_score, status = None, None
        if risk is not None:
            user_score = user_trust_score(risk, fake_prob)
            status = bot_status(user_score)

        return {"trust": score, "level": level_name(score),
                "verdict": "Fake" if fake_prob >= 0.5 else "Genuine",
                "fake_prob": round(fake_prob, 3), "behavior_risk": risk,
                "user_trust": user_score, "bot_status": status,
                "reasons": reasons, "terms": top_terms(text, self.vectorizer, self.explainer)}

    def analyze_batch(self, texts, reviews_last_24h=None, account_age_days=999):
        cleaned = [clean_text(t) for t in texts]
        X = self.vectorizer.transform(cleaned)
        probs = self.model.predict_proba(X)[:, 1]                
        results = []
        for i, text in enumerate(texts):
            p = float(probs[i]) if cleaned[i] else 0.5
            risk = None
            if reviews_last_24h is not None:
                risk, _ = behavior_risk(int(reviews_last_24h[i]), account_age_days)
            score = trust_score(p, risk)
            results.append({"verdict": "Fake" if p >= 0.5 else "Genuine",
                            "fake_prob": round(p, 3), "trust": score, "level": level_name(score),
                            "top_words": top_fake_words(text, self.vectorizer, self.explainer)})
        return results
