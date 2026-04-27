# ── Builder stage ────────────────────────────────────────────────────────────
# Includes build-essential (needed to compile hnswlib / chromadb C extensions)
# and installs CPU-only PyTorch to avoid pulling in ~2.5 GB of CUDA libraries.
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only PyTorch FIRST so pip resolves the rest of the deps against
# it, preventing the default CUDA-enabled wheel (~530 MB + ~2.5 GB CUDA deps)
# from being pulled in by sentence-transformers.
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

# Pre-download SBERT model into the builder layer so the runtime image starts
# instantly without a Hugging Face download on every cold start.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# ── Runtime stage ─────────────────────────────────────────────────────────────
# Slim image with no build tools — only the compiled packages and app code.
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed Python packages (including CPU torch + sentence-transformers)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy cached Hugging Face / sentence-transformers model weights
COPY --from=builder /root/.cache /root/.cache

# Copy application code
COPY main.py matcher.py ./

# Copy pre-built vector DB and CSV data
COPY chroma_db/ chroma_db/
COPY data/ data/

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
