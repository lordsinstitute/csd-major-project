# 1. Problem Statement

**Project title:** AI-Powered Fake Product Review Detection (TrustLens)

## 1.1 Background
People depend on online reviews to decide what to buy. Fake reviews mislead buyers and hurt honest sellers.
Bots make the problem worse: one bot account can post many reviews in a short time and push a rating up or down.

## 1.2 Problem
Buyers cannot easily tell a real review from a fake one, and checking thousands of reviews and accounts by hand is not possible.
Three gaps exist in many existing solutions:

| Gap | Why it matters |
|---|---|
| Text-only detection | Bots also show unusual *behaviour* (many reviews in one day, brand-new accounts). Text alone misses this. |
| No clear reason | A label such as "fake" without a reason is hard to trust. Users need a score and an explanation. |
| Heavy or complex systems | Deep models and platform-specific systems are hard to run, explain and reuse. |

## 1.3 Proposed solution
TrustLens checks every review and every user and gives a **trust score from 0 to 100** with reasons.
It combines a machine-learning text model with simple behaviour rules.

## 1.4 Objectives
| # | Objective |
|---|---|
| O1 | Detect fake and genuine reviews from the review text using machine learning. |
| O2 | Detect bot-like behaviour using reviews per day and account age. |
| O3 | Give a trust score from 0 to 100 for each review and each user. |
| O4 | Explain every result in simple words (which words pushed the score up or down). |
| O5 | Provide a simple website that checks one review or a whole CSV file. |
| O6 | Keep it simple: one command to run, no login, no database. |

## 1.5 Scope
**In scope**
- English product reviews.
- Text classification with four classical models (Logistic Regression, SVM, Random Forest, XGBoost) and selection of the best by F1 score.
- Rule-based behaviour risk (reviews in 24 hours, account age) and a user trust score.
- Explanation with word highlighting.
- Streamlit website with four pages: Home, Check a Review, Check a CSV File, Model Performance.

**Out of scope (future work)**
- Deep or transformer models (for example BERT, DeBERTa).
- Learning the behaviour rules and score weights from real reviewer data.
- Network (reviewer graph) features, SHAP or LIME explanations.
- Other languages, live platform integration or a browser extension.

## 1.6 Expected outcome
A working prototype that, for any review, shows: a Fake/Genuine verdict, a 0-100 trust score, a bot check when behaviour is known, and the words that explain the decision.
