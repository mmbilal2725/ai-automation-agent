# FastAPI Production Dockerfile
FROM python:3.11-slim

WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application
COPY ./app /code/app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /code
USER appuser

# Expose port
EXPOSE 80

# Run application
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
