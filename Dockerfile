FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for chromadb / hnswlib build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download SBERT model so container starts fast (no HF download at runtime)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# Copy application code
COPY main.py matcher.py ./

# Copy pre-built vector DB and CSV data
COPY chroma_db/ chroma_db/
COPY data/ data/

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
