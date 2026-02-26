# ============================================
# Hello World FastAPI Dockerfile
# ============================================
# Simple single-stage Dockerfile for learning and prototyping
# NOT for production use - see production.Dockerfile

FROM python:3.13-slim

WORKDIR /app

# Install FastAPI and Uvicorn
RUN pip install --no-cache-dir fastapi uvicorn[standard]

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Expected main.py:
# from fastapi import FastAPI
# app = FastAPI()
# @app.get("/")
# async def root():
#     return {"message": "Hello World"}
