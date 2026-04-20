FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ core/
COPY api/ api/
COPY repository/ repository/
COPY alembic/ alembic/
COPY alembic.ini .
COPY scripts/ scripts/
COPY seed_data.json.gz .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python scripts/seed.py && uvicorn api.main:app --host 0.0.0.0 --port 8000"]
