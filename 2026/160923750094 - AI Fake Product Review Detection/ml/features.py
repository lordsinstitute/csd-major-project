# STEP 3: Turn text into numbers with TF-IDF.
# A word gets a high number if it is special to a review, and a low number if it is everywhere.
from sklearn.feature_extraction.text import TfidfVectorizer


def make_vectorizer():
    return TfidfVectorizer(
        max_features=5000,       # keep the 5000 best words / word pairs
        ngram_range=(1, 2),      # single words and pairs like "highly recommend"
        stop_words="english",    # ignore "the", "is", "and" ...
        min_df=2,                # ignore words seen in fewer than 2 reviews
    )
