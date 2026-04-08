FROM python:3.11-slim

WORKDIR /app

# Install dependencies needed for some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy all needed pkl and csv files, and webapp.py
COPY webapp.py .
COPY movies_dict.pkl .
COPY similarity.pkl .
COPY genre_map.pkl .

EXPOSE 8502

HEALTHCHECK CMD curl --fail http://localhost:8502/_stcore/health

ENTRYPOINT ["streamlit", "run", "webapp.py", "--server.port=8502", "--server.address=0.0.0.0"]
