FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Sandbox directories
RUN mkdir -p /tmp/cicd_agent /tmp/cicd_results \
    && chmod 777 /tmp/cicd_agent /tmp/cicd_results

# Git safety
RUN git config --global safe.directory "*"

EXPOSE 8000

CMD ["uvicorn", "backend.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
