FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim AS runner

WORKDIR /app

# Copy installed dependencies
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source code and models
COPY backend/ /app/backend/
COPY public/ /app/public/
COPY scripts/ /app/scripts/
COPY tests/ /app/tests/

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
