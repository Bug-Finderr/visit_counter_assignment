FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OTEL_TRACES_EXPORTER=none OTEL_METRICS_EXPORTER=none OTEL_LOGS_EXPORTER=none

WORKDIR /app

COPY requirements.txt .
# setuptools ships old copies of wheel/jaraco, pip vendors old msgpack/urllib3; nothing is installed at runtime
RUN pip install --no-cache-dir -r requirements.txt && pip uninstall -y setuptools wheel pip

COPY app ./app

ARG GIT_SHA=dev
ENV GIT_SHA=$GIT_SHA

USER 10001:10001
EXPOSE 8000

CMD ["opentelemetry-instrument", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
