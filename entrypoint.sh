#!/bin/bash
set -e

echo "Running database migrations..."
python migrate.py upgrade

echo "Running database seeds..."
python seed_db.py

echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
