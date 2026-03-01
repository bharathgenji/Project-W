FROM python:3.12-slim AS base

WORKDIR /app

COPY shared/requirements.txt shared/requirements.txt
RUN pip install --no-cache-dir -r shared/requirements.txt

COPY services/bid-ingester/requirements.txt services/bid-ingester/requirements.txt
RUN pip install --no-cache-dir -r services/bid-ingester/requirements.txt

COPY shared/ shared/
COPY services/bid-ingester/ services/bid-ingester/

ENV PYTHONPATH=/app

# Hyphenated dir not importable as Python module — create symlink
RUN ln -s /app/services/bid-ingester /app/services/bid_ingester

EXPOSE 8080
CMD ["uvicorn", "services.bid_ingester.main:app", "--host", "0.0.0.0", "--port", "8080"]
