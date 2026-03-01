FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy AS base

WORKDIR /app

COPY shared/requirements.txt shared/requirements.txt
RUN pip install --no-cache-dir -r shared/requirements.txt

COPY services/license-scraper/requirements.txt services/license-scraper/requirements.txt
RUN pip install --no-cache-dir -r services/license-scraper/requirements.txt

COPY shared/ shared/
COPY services/license-scraper/ services/license-scraper/

ENV PYTHONPATH=/app

# Hyphenated dir not importable as Python module — create symlink
RUN ln -s /app/services/license-scraper /app/services/license_scraper

EXPOSE 8080
CMD ["uvicorn", "services.license_scraper.main:app", "--host", "0.0.0.0", "--port", "8080"]
