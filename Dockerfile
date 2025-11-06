# ---------------------------------------------------
# BASE PYTHON IMAGE
# ---------------------------------------------------
    FROM python:3.10-slim

    # Avoid prompts during install
    ENV DEBIAN_FRONTEND=noninteractive
    
    # ---------------------------------------------------
    # SYSTEM DEPENDENCIES
    # ---------------------------------------------------
    RUN apt-get update && apt-get install -y \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
        && rm -rf /var/lib/apt/lists/*
    
    # ---------------------------------------------------
    # WORKDIR
    # ---------------------------------------------------
    WORKDIR /app
    
    # ---------------------------------------------------
    # COPY REQUIREMENTS
    # ---------------------------------------------------
    COPY requirements.txt .
    
    RUN pip install --no-cache-dir -r requirements.txt
    
    # ---------------------------------------------------
    # COPY SOURCE CODE
    # ---------------------------------------------------
    COPY . .
    
    # ---------------------------------------------------
    # EXPOSING PORT
    # ---------------------------------------------------
    EXPOSE 8000
    
    # ---------------------------------------------------
    # START FASTAPI WITH UVICORN
    # ---------------------------------------------------
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    