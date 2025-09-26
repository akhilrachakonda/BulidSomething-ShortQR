#!/bin/sh
export DATABASE_URL="postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-svc:5432/${POSTGRES_DB}"
exec python -m uvicorn app:app --host 0.0.0.0 --port 8080
