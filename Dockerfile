FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ core/
COPY api/ api/
COPY repository/ repository/
COPY alembic/ alembic/
COPY alembic.ini .

COPY seed.py .
COPY seed_data/ seed_data/

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python seed.py && uvicorn api.main:app --host 0.0.0.0 --port 8000"]
