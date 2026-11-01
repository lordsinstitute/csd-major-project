# STEP 7: Explain the score in simple words (Explainable AI).
# Logistic Regression gives every word a weight:
#   positive weight -> pushes toward FAKE,  negative weight -> pushes toward REAL.
# contribution of a word = its TF-IDF value in this review x its weight.
import html
import re
import numpy as np

from ml.clean import clean_text


def term_contributions(text, vectorizer, explainer):
    """List of (word or word pair, contribution) for everything found in the review."""
    X = vectorizer.transform([clean_text(text)]).tocoo()
    names = vectorizer.get_feature_names_out()
    weights = explainer.coef_[0]
    return [(names[j], float(v * weights[j])) for j, v in zip(X.col, X.data)]


def top_terms(text, vectorizer, explainer, n=8):
    """The n words that matter most (either direction). Used for the bar chart."""
    items = term_contributions(text, vectorizer, explainer)
    return sorted(items, key=lambda i: -abs(i[1]))[:n]


def top_fake_words(text, vectorizer, explainer, n=3):
    items = term_contributions(text, vectorizer, explainer)
    words = [w for w, c in sorted(items, key=lambda i: -i[1]) if c > 0][:n]
    return ", ".join(words)


def explain_text(text, vectorizer, explainer, top_n=4):
    """Short sentences for the 'Why?' list."""
    items = term_contributions(text, vectorizer, explainer)
    fake_words = [w for w, c in sorted(items, key=lambda i: -i[1]) if c > 0][:top_n]
    real_words = [w for w, c in sorted(items, key=lambda i: i[1]) if c < 0][:top_n]
    reasons = []
    if fake_words:
        reasons.append("Words that look fake-like: " + ", ".join(fake_words) + ".")
    if real_words:
        reasons.append("Words that look real-like: " + ", ".join(real_words) + ".")
    return reasons


def highlight_html(text, vectorizer, explainer):
    """The review text with fake-like words in red and real-like words in green."""
    weights = explainer.coef_[0]
    scale = float(np.percentile(np.abs(weights), 99)) or 1.0    # what counts as a 'strong' word
    vocab = vectorizer.vocabulary_
    out = []
    for part in re.findall(r"[A-Za-z']+|[^A-Za-z']+", text):
        safe = html.escape(part).replace("\n", "<br>")
        if re.match(r"[A-Za-z']", part):
            idx = vocab.get(part.lower().strip("'"))
            if idx is not None:
                w = float(weights[idx])
                alpha = min(abs(w) / scale, 1.0) * 0.65
                if alpha > 0.05:
                    color = "220,53,69" if w > 0 else "40,167,69"
                    out.append(f'<span style="background:rgba({color},{alpha:.2f});'
                               f'padding:1px 4px;border-radius:5px">{safe}</span>')
                    continue
        out.append(safe)
    return "".join(out)
