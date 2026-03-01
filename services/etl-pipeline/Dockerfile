FROM python:3.12-slim AS base

WORKDIR /app

COPY shared/requirements.txt shared/requirements.txt
RUN pip install --no-cache-dir -r shared/requirements.txt

COPY services/etl-pipeline/requirements.txt services/etl-pipeline/requirements.txt
RUN pip install --no-cache-dir -r services/etl-pipeline/requirements.txt

COPY shared/ shared/
COPY services/etl-pipeline/ services/etl-pipeline/

ENV PYTHONPATH=/app

# Hyphenated dir not importable as Python module — create symlink
RUN ln -s /app/services/etl-pipeline /app/services/etl_pipeline

EXPOSE 8080
CMD ["uvicorn", "services.etl_pipeline.main:app", "--host", "0.0.0.0", "--port", "8080"]
