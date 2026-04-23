FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        gcc \
        libsqlite3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY scripts/ ./scripts/
COPY pytest.ini .

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

RUN echo '#!/bin/bash\n\
cd /app/backend\n\
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 &\n\
sleep 3\n\
cd /app/frontend\n\
streamlit run app.py --server.port=8501 --server.address=0.0.0.0\n\
' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 8000 8501
CMD ["/app/start.sh"]
