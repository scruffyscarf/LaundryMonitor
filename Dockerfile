FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
        gcc \
        musl-dev \
        sqlite-dev \
        linux-headers \
        bash

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN apk del gcc musl-dev linux-headers

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY scripts/ ./scripts/
COPY pytest.ini .

RUN adduser -D -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000 8501
CMD ["/app/scripts/run.sh"]
