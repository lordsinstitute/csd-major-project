from sklearn.feature_extraction.text import TfidfVectorizer


def make_vectorizer():
    return TfidfVectorizer(
        max_features=5000,      
        ngram_range=(1, 2),      
        stop_words="english",    
        min_df=2,                
    )
