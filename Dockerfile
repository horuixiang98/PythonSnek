FROM python:3.9-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy application code
COPY . .

# Set Dynatrace environment variables
ENV DT_ENABLEMULTIPROCESSINGINSTRUMENTATION=true
ENV DT_PYTHONPATH=/usr/local/bin/python3

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]