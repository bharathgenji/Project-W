FROM python:3.12-slim AS base

WORKDIR /app

COPY shared/requirements.txt shared/requirements.txt
RUN pip install --no-cache-dir -r shared/requirements.txt

COPY services/permit-ingester/requirements.txt services/permit-ingester/requirements.txt
RUN pip install --no-cache-dir -r services/permit-ingester/requirements.txt

COPY shared/ shared/
COPY services/permit-ingester/ services/permit-ingester/

ENV PYTHONPATH=/app

# Hyphenated dir not importable as Python module — create symlink
RUN ln -s /app/services/permit-ingester /app/services/permit_ingester

EXPOSE 8080
CMD ["uvicorn", "services.permit_ingester.main:app", "--host", "0.0.0.0", "--port", "8080"]
