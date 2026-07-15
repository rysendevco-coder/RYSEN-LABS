FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system dashboard \
    && adduser --system --ingroup dashboard --home /app dashboard

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

COPY config ./config

RUN chown -R dashboard:dashboard /app
USER dashboard

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3).read()"

CMD ["python", "-m", "app.server"]
