FROM python:3.11-slim

# Install system dependencies for nvidia-smi and docker CLI
RUN apt-get update && apt-get install -y \
    pciutils \
    curl \
    && curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# We don't COPY the code because we will mount it as a volume for development
CMD ["python", "app.py"]