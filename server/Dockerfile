FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL source files (run from project root)
COPY models.py .
COPY client.py .
COPY __init__.py .
COPY openenv.yaml .
COPY server/ ./server/

EXPOSE 7860

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
