FROM python:3.9-slim

WORKDIR /app

COPY src/ ./src/
COPY input/ ./input/
COPY output/ ./output/

RUN pip install --no-cache-dir PyMuPDF scikit-learn joblib

CMD ["python", "./src/main.py"]
