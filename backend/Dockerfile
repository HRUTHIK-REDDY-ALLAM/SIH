FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install deps first so the layer caches across code edits.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Wait for Postgres, then serve. Schema + demo seed happen in the app's
# lifespan hook on first start.
CMD ["sh", "-c", "python -m app.wait_for_db && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
