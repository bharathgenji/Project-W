# Stage 1: Build React frontend
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY services/api-server/frontend/package*.json ./
RUN npm ci
COPY services/api-server/frontend/ .
RUN npm run build

# Stage 2: Python API server
FROM python:3.12-slim AS base
WORKDIR /app

COPY shared/requirements.txt shared/requirements.txt
RUN pip install --no-cache-dir -r shared/requirements.txt

COPY services/api-server/requirements.txt services/api-server/requirements.txt
RUN pip install --no-cache-dir -r services/api-server/requirements.txt

COPY shared/ shared/
COPY services/api-server/ services/api-server/

# Copy built frontend
COPY --from=frontend-build /frontend/dist services/api-server/frontend/dist

ENV PYTHONPATH=/app

# api-server dir uses a hyphen which Python can't import — create a symlink
RUN ln -s /app/services/api-server /app/services/api_server

EXPOSE 8080
CMD ["uvicorn", "services.api_server.main:app", "--host", "0.0.0.0", "--port", "8080"]
