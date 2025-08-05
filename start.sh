#!/bin/bash
# Railway startup script for Twerlo

# Set default port if not provided by Railway
export PORT=${PORT:-8000}

echo "Starting Twerlo on port $PORT"
echo "LLM Provider: ${LLM_BASE_URL}"
echo "Embedding Provider: ${EMBEDDING_BASE_URL}"

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
