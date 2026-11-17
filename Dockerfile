FROM python:3.12-slim

WORKDIR /app

# Install system utilities and Git
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    graphviz \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source repository
COPY . .

EXPOSE 8000 8501

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
