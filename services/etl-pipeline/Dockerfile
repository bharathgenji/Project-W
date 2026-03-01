FROM python:3.12-slim AS base

WORKDIR /app

COPY shared/requirements.txt shared/requirements.txt
RUN pip install --no-cache-dir -r shared/requirements.txt

COPY services/etl-pipeline/requirements.txt services/etl-pipeline/requirements.txt
RUN pip install --no-cache-dir -r services/etl-pipeline/requirements.txt

COPY shared/ shared/
COPY services/etl-pipeline/ services/etl-pipeline/

ENV PYTHONPATH=/app

EXPOSE 8080
CMD ["uvicorn", "services.etl_pipeline.main:app", "--host", "0.0.0.0", "--port", "8080"]
