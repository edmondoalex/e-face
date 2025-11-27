# Build stage for frontend
FROM node:18-alpine as builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./frontend/
COPY frontend/ ./frontend/
WORKDIR /app/frontend
RUN npm ci && npm run build

# Final stage: python server
FROM python:3.11-slim
WORKDIR /app
COPY backend/ ./backend/
COPY --from=builder /app/frontend/dist ./backend/frontend_dist
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
