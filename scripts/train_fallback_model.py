# scripts/train_fallback_model.py

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
import joblib
import os

# Example heading and non-heading data
data = [
    ("1. Introduction", 1),
    ("2. Scope", 1),
    ("Proposal Summary", 1),
    ("Background", 1),
    ("S.No", 0),
    ("Name", 0),
    ("Age", 0),
    ("Date of joining", 0),
    ("Signature of officer", 0),
    ("Rs.", 0),
]

# Prepare training data
texts, labels = zip(*data)
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(texts)

model = LogisticRegression()
model.fit(X, labels)

# Save model to src/ directory
output_path = os.path.join(os.path.dirname(__file__), "../src/heading_model.pkl")
joblib.dump({"model": model, "vectorizer": vectorizer}, output_path)
print(f"✅ Model saved to: {output_path}")
