import os
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ml.config import ROOT, MODEL_DIR, DATA_FILE
from ml.predict import Analyzer
from ml.batch import analyze_dataframe
from ml.explain import highlight_html
from ml import train as trainer

PAGES = ["🏠 Home", "🔍 Check a Review", "📂 Check a CSV File", "📊 Model Performance"]

LEVEL_COLOR = {"Trusted": "#1a8f4c", "Needs a check": "#c77a00", "Likely fake or bot": "#c62d3a"}
STATUS_COLOR = {"Looks human": "#1a8f4c", "Suspicious": "#c77a00", "Bot-like": "#c62d3a"}
VERDICT_COLOR = {"Genuine": "#1a8f4c", "Fake": "#c62d3a"}

EXAMPLE_FAKE = ("Absolutely amazing blender! Best purchase of the year. Everything about it is perfect. "
                "You will not regret buying it. Highly recommended!!")
EXAMPLE_REAL = ("I have been using this blender for about 3 weeks. The size is a bit smaller than I expected "
                "and it is a little noisy, but it works fine for smoothies. Three stars, it is fine.")

CSS = """
<style>
.tl-hero{background:linear-gradient(120deg,#3b4cca 0%,#4f6bed 55%,#6ea8fe 100%);color:#fff;border-radius:18px;
         padding:34px 34px 28px 34px;margin-bottom:18px}
.tl-hero h1{margin:0 0 6px 0;font-size:2.1rem;color:#fff}
.tl-hero p{margin:0;opacity:.92;font-size:1.02rem;color:#fff}
.tl-card{border:1px solid rgba(128,128,128,.30);border-radius:14px;padding:16px 18px;
         background:rgba(128,128,128,.07);height:100%}
.tl-card h4{margin:0 0 6px 0}
.tl-step{font-size:1.6rem}
.tl-badge{display:inline-block;padding:5px 16px;border-radius:999px;font-weight:600;color:#fff;font-size:.95rem}
.tl-review{border:1px solid rgba(128,128,128,.30);border-radius:12px;padding:16px;line-height:1.9;
           background:rgba(128,128,128,.06)}
.tl-small{opacity:.75;font-size:.9rem}
</style>
"""

def badge(text, color):
    return f'<span class="tl-badge" style="background:{color}">{text}</span>'


def card(title, body, icon=""):
    return f'<div class="tl-card"><div class="tl-step">{icon}</div><h4>{title}</h4><div class="tl-small">{body}</div></div>'


def gauge(score, title):
    color = "#1a8f4c" if score >= 70 else "#c77a00" if score >= 40 else "#c62d3a"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, number={"suffix": " / 100"}, title={"text": title},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": color},
               "steps": [{"range": [0, 40], "color": "rgba(198,45,58,0.22)"},
                         {"range": [40, 70], "color": "rgba(199,122,0,0.22)"},
                         {"range": [70, 100], "color": "rgba(26,143,76,0.22)"}]}))
    fig.update_layout(height=270, margin=dict(l=25, r=25, t=60, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig


@st.cache_resource(show_spinner=False)
def load_analyzer():
    return Analyzer()


def get_analyzer():
    try:
        return load_analyzer()
    except FileNotFoundError:
        return None


def load_meta():
    path = os.path.join(MODEL_DIR, "meta.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def load_results():
    path = os.path.join(MODEL_DIR, "results.csv")
    return pd.read_csv(path) if os.path.exists(path) else None


def train_panel():
    """Shown when the model is missing, and on the Model Performance page."""
    st.subheader("🛠️ Train the model")
    if os.path.exists(DATA_FILE):
        st.success("Dataset found: data/fake reviews dataset.csv")
    else:
        st.warning("No dataset yet. Upload the Kaggle CSV below, or copy it into the data folder.")

    upload = st.file_uploader("Upload the dataset CSV (columns: label and text_)", type="csv", key="train_upload")
    if st.button("🚀 Train model now", type="primary"):
        if upload is not None:
            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
            with open(DATA_FILE, "wb") as f:
                f.write(upload.getvalue())
        bar = st.progress(0.0, text="Starting...")
        try:
            trainer.main(progress=lambda text, frac: bar.progress(frac, text=text))
        except Exception as e:
            st.error(f"Training failed: {e}")
        else:
            st.cache_resource.clear()
            st.session_state["just_trained"] = True
            st.rerun()


def need_model():
    analyzer = get_analyzer()
    if analyzer is None:
        st.warning("The model is not trained yet. Train it once here, then every page will work.")
        train_panel()
        st.stop()
    return analyzer


def page_home():
    st.markdown("""
    <div class="tl-hero"><h1>🛡️ TrustLens</h1>
    <p>AI-based fake review detection, bot detection and user trust analysis.
    Every review and every user gets a trust score from 0 to 100, with clear reasons.</p></div>
    """, unsafe_allow_html=True)

    if st.session_state.pop("just_trained", False):
        st.success("Model trained. You can now check reviews.")

    meta, results = load_meta(), load_results()
    if meta and results is not None:
        best = results[results["Model"] == meta["best"]].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Best model", meta["best"])
        c2.metric("F1 score", f"{best['F1']:.3f}")
        c3.metric("Accuracy", f"{best['Accuracy']:.3f}")
        c4.metric("Reviews used", f"{meta['reviews_used']:,}")
    else:
        st.info("Model not trained yet. Open **Check a Review** to train it with one button.")

    st.markdown("### How a review is checked")
    cols = st.columns(5)
    steps = [("🧹", "1. Clean", "Remove tags, symbols and extra spaces."),
             ("🔢", "2. Numbers", "TF-IDF turns words into numbers."),
             ("🤖", "3. Model", "4 models compared, best one kept."),
             ("🕵️", "4. Behaviour", "Reviews per day and account age."),
             ("🎯", "5. Score + Why", "One 0–100 score with reasons.")]
    for col, (icon, title, body) in zip(cols, steps):
        col.markdown(card(title, body, icon), unsafe_allow_html=True)

    st.markdown("### What you can do")
    left, right = st.columns(2)
    with left:
        st.markdown("""
- **Fake or genuine** decision from the review text
- **Manual review** box and **CSV file** upload
- **Bot detection** for users (Looks human / Suspicious / Bot-like)
        """)
    with right:
        st.markdown("""
- **User behaviour** check: reviews per day, account age
- **Explanation**: highlighted words and a "Why?" list
- **Trust score** for every review and every user
        """)

    st.markdown("### Trust levels")
    a, b, c = st.columns(3)
    a.markdown(badge("Trusted · 70 to 100", LEVEL_COLOR["Trusted"]) + "<br><span class='tl-small'>Show the review.</span>", unsafe_allow_html=True)
    b.markdown(badge("Needs a check · 40 to 69", LEVEL_COLOR["Needs a check"]) + "<br><span class='tl-small'>Send for a manual look.</span>", unsafe_allow_html=True)
    c.markdown(badge("Likely fake or bot · 0 to 39", LEVEL_COLOR["Likely fake or bot"]) + "<br><span class='tl-small'>Hide it and flag the account.</span>", unsafe_allow_html=True)


def set_example(text):
    st.session_state["review_text"] = text


def page_review():
    st.title("🔍 Check a Review")
    analyzer = need_model()

    st.caption("Paste a product review, or try an example.")
    b1, b2, _ = st.columns([1, 1, 3])
    b1.button("Try a fake-style example", on_click=set_example, args=(EXAMPLE_FAKE,))
    b2.button("Try a real-style example", on_click=set_example, args=(EXAMPLE_REAL,))

    text = st.text_area("Review text", key="review_text", height=150,
                        placeholder="Type or paste a product review here...")

    with st.expander("🕵️ Reviewer behaviour (optional) — turns on bot detection"):
        use_behaviour = st.checkbox("I know how this reviewer behaves")
        c1, c2 = st.columns(2)
        last24 = c1.slider("Reviews posted by this reviewer in the last 24 hours", 0, 30, 1, disabled=not use_behaviour)
        age = c2.slider("Reviewer account age (days)", 0, 365, 30, disabled=not use_behaviour)

    if st.button("Check review", type="primary"):
        if not text.strip():
            st.warning("Please type or paste a review first.")
            return
        result = analyzer.analyze(text, last24 if use_behaviour else None, age if use_behaviour else None)
        show_review_result(analyzer, text, result, use_behaviour)


def show_review_result(analyzer, text, r, used_behaviour):
    st.markdown("---")
    left, right = st.columns([1, 1])
    with left:
        st.plotly_chart(gauge(r["trust"], "Review trust score"))
    with right:
        st.markdown("**Text verdict**")
        st.markdown(badge(r["verdict"], VERDICT_COLOR[r["verdict"]]), unsafe_allow_html=True)
        st.markdown("**Trust level**")
        st.markdown(badge(r["level"], LEVEL_COLOR[r["level"]]), unsafe_allow_html=True)
        st.metric("Chance the text is fake", f"{r['fake_prob'] * 100:.0f}%")

    if r["bot_status"]:
        st.markdown("#### 🕵️ Bot detection")
        c1, c2 = st.columns([1, 2])
        c1.metric("User trust score", f"{r['user_trust']} / 100")
        c2.markdown(badge(r["bot_status"], STATUS_COLOR[r["bot_status"]]), unsafe_allow_html=True)
    elif not used_behaviour:
        st.caption("Tip: open *Reviewer behaviour* above to add reviews per day and account age. Then the bot check turns on.")

    tab1, tab2, tab3 = st.tabs(["💡 Why this score", "🖍️ Highlighted review", "🧮 Score breakdown"])
    with tab1:
        for reason in r["reasons"]:
            st.markdown(f"- {reason}")
        if r["terms"]:
            terms = pd.DataFrame(r["terms"], columns=["Word", "Push"]).sort_values("Push")
            fig = go.Figure(go.Bar(x=terms["Push"], y=terms["Word"], orientation="h",
                                   marker_color=["#c62d3a" if v > 0 else "#1a8f4c" for v in terms["Push"]]))
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), title="Which words push the decision",
                              xaxis_title="← looks real          looks fake →", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig)
    with tab2:
        st.markdown(f'<div class="tl-review">{highlight_html(text, analyzer.vectorizer, analyzer.explainer)}</div>',
                    unsafe_allow_html=True)
        st.markdown('<span class="tl-small">🟥 red = looks fake-like &nbsp; 🟩 green = looks real-like. '
                    'Darker colour = stronger push. Single words only.</span>', unsafe_allow_html=True)
    with tab3:
        text_risk = r["fake_prob"]
        if r["behavior_risk"] is None:
            st.markdown(f"No reviewer info, so the score uses the **text only**:  \n"
                        f"`trust = 100 × (1 − {text_risk:.2f}) = {r['trust']}`")
        else:
            b = r["behavior_risk"]
            st.markdown(f"`trust = 100 × (1 − (0.7 × {text_risk:.2f} + 0.3 × {b:.2f})) = {r['trust']}`")
            st.dataframe(pd.DataFrame({"Part": ["Text risk (fake chance)", "Behaviour risk"],
                                       "Value": [f"{text_risk:.2f}", f"{b:.2f}"], "Weight": ["70%", "30%"]}),
                         hide_index=True)


def use_demo():
    st.session_state["use_demo"] = True


def page_csv():
    st.title("📂 Check a CSV File")
    analyzer = need_model()

    st.caption("Needs a column named **review_text**. Add **user_id** (and **date**) to turn on bot detection.")
    demo_path = os.path.join(ROOT, "samples", "demo_upload.csv")
    c1, c2, c3 = st.columns([2, 1, 1])
    upload = c1.file_uploader("Upload a CSV file", type="csv", label_visibility="collapsed")
    c2.button("Use the demo file", on_click=use_demo)
    if os.path.exists(demo_path):
        with open(demo_path, "rb") as f:
            c3.download_button("Download demo file", f.read(), "demo_upload.csv", "text/csv")

    max_rows = st.slider("Maximum reviews to check", 100, 10000, 2000, step=100)

    source = upload if upload is not None else (demo_path if st.session_state.get("use_demo") else None)
    if source is not None:
        label = upload.name if upload is not None else "samples/demo_upload.csv"
        st.info(f"File ready: **{label}**")
        if st.button("Analyze file", type="primary"):
            try:
                df = pd.read_csv(source)
                with st.spinner("Checking reviews..."):
                    st.session_state["csv_result"] = analyze_dataframe(df, analyzer, max_rows)
            except Exception as e:
                st.error(f"Could not read this file: {e}")

    res = st.session_state.get("csv_result")
    if res is None:
        return
    show_csv_result(res)


def show_csv_result(res):
    rev, users = res["reviews"], res["users"]
    st.markdown("---")
    total = len(rev)
    fake = int((rev["verdict"] == "Fake").sum())
    k = st.columns(5 if res["has_user"] else 4)
    k[0].metric("Reviews checked", f"{total:,}")
    k[1].metric("Genuine", f"{total - fake:,}")
    k[2].metric("Fake", f"{fake:,}")
    k[3].metric("Average trust", f"{rev['trust'].mean():.0f} / 100")
    if res["has_user"]:
        k[4].metric("Bot-like users", int((users["status"] == "Bot-like").sum()))
    if res["accuracy"] is not None:
        st.success(f"The file has a label column. The model matched it for {res['accuracy'] * 100:.1f}% of the reviews.")

    g1, g2, g3 = st.columns(3)
    with g1:
        fig = px.pie(rev, names="verdict", hole=0.55, color="verdict", color_discrete_map=VERDICT_COLOR, title="Genuine vs fake")
        fig.update_layout(height=290, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)
    with g2:
        fig = px.histogram(rev, x="trust", nbins=20, title="Trust score spread", color_discrete_sequence=["#4f6bed"])
        fig.update_layout(height=290, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)
    with g3:
        counts = rev["level"].value_counts().reindex(list(LEVEL_COLOR)).fillna(0).reset_index()
        counts.columns = ["level", "count"]
        fig = px.bar(counts, x="level", y="count", color="level", color_discrete_map=LEVEL_COLOR, title="Trust levels")
        fig.update_layout(height=290, margin=dict(l=10, r=10, t=50, b=10), showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)

    tabs = st.tabs(["📝 Reviews", "🕵️ Users and bots", "⬇️ Download"])
    with tabs[0]:
        f1, f2 = st.columns([2, 1])
        levels = f1.multiselect("Show trust levels", list(LEVEL_COLOR), default=list(LEVEL_COLOR))
        search = f2.text_input("Search in review text")
        view = rev[rev["level"].isin(levels)]
        if search:
            view = view[view["review"].str.contains(search, case=False, na=False)]
        st.dataframe(view.rename(columns={"review": "Review", "verdict": "Verdict", "fake_prob": "Fake chance",
                                          "trust": "Trust score", "level": "Level", "top_words": "Fake-like words",
                                          "user_id": "User"}),
                     hide_index=True,
                     column_config={"Trust score": st.column_config.ProgressColumn("Trust score", min_value=0, max_value=100, format="%d")})
    with tabs[1]:
        if users is None:
            st.info("No user_id column in this file, so bot detection is off. Add **user_id** (and **date**) and upload again.")
        else:
            bots = int((users["status"] == "Bot-like").sum())
            st.markdown(f"**{bots}** bot-like and **{int((users['status'] == 'Suspicious').sum())}** suspicious users. Most suspicious first.")
            st.dataframe(users.rename(columns={"user_id": "User", "reviews": "Reviews", "max_per_day": "Most in one day",
                                               "avg_fake_chance": "Avg fake chance %", "user_trust": "User trust",
                                               "status": "Status", "note": "Behaviour note"}),
                         hide_index=True,
                         column_config={"User trust": st.column_config.ProgressColumn("User trust", min_value=0, max_value=100, format="%d")})
    with tabs[2]:
        st.download_button("Download review results (CSV)", rev.to_csv(index=False).encode("utf-8"),
                           "trustlens_review_results.csv", "text/csv")
        if users is not None:
            st.download_button("Download user results (CSV)", users.to_csv(index=False).encode("utf-8"),
                               "trustlens_user_results.csv", "text/csv")


def page_model():
    st.title("📊 Model Performance")
    meta, results = load_meta(), load_results()
    if meta is None or results is None:
        st.warning("No trained model yet.")
        train_panel()
        return

    st.markdown(f"Trained on **{meta['reviews_used']:,}** reviews from `{meta['dataset']}` "
                f"({meta['train_rows']:,} for training, {meta['test_rows']:,} for testing). "
                f"Best model by F1: **{meta['best']}**.")
    st.dataframe(results, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        long = results.melt(id_vars="Model", var_name="Metric", value_name="Score")
        fig = px.bar(long, x="Model", y="Score", color="Metric", barmode="group", title="All models, all metrics")
        fig.update_layout(height=380, yaxis_range=[0, 1.05], paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)
    with c2:
        fig = px.imshow(meta["confusion"], text_auto=True, x=["Genuine", "Fake"], y=["Genuine", "Fake"],
                        color_continuous_scale="Blues", title=f"Confusion matrix: {meta['best']}",
                        labels=dict(x="Predicted", y="Actual", color="Reviews"))
        fig.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)

    with st.expander("🔁 Train again (for example with a new dataset)"):
        train_panel()


def main():
    st.set_page_config(page_title="TrustLens", page_icon="🛡️", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## 🛡️ TrustLens")
        st.caption("Fake review, bot detection and user trust analysis")
        page = st.radio("Go to", PAGES, label_visibility="collapsed")

    {"🏠 Home": page_home, "🔍 Check a Review": page_review, "📂 Check a CSV File": page_csv,
     "📊 Model Performance": page_model}[page]()


def inside_streamlit():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx(suppress_warning=True) is not None
    except Exception:
        return False


if __name__ == "__main__":
    if inside_streamlit():
        main()
    else:                      
        from run import launch
        launch()
