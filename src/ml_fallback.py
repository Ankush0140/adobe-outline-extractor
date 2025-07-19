# File: src/ml_fallback.py
import os
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "heading_model.pkl")

try:
    model_bundle = joblib.load(MODEL_PATH)
    vectorizer = model_bundle["vectorizer"]
    classifier = model_bundle["model"]
except Exception as e:
    print("ML fallback model not loaded:", e)
    vectorizer = None
    classifier = None

def is_heading(text):
    if not text or not vectorizer or not classifier:
        return False
    X = vectorizer.transform([text])
    prediction = classifier.predict(X)[0]
    return prediction == 1


# Optional: scripts/train_fallback_model.py (for training your own model)
if __name__ == "__main__":
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.linear_model import LogisticRegression

    