FROM python:3.9-slim

WORKDIR /app

# Install dependencies first for better layer caching
# Copy requirements FIRST (relative to Dockerfile location)
COPY ./requirements.txt /app/requirements.txt

# Install Python packages
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . .

# Set Dynatrace environment variables
ENV DT_PYTHONPATH=/usr/local/bin/python3

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]