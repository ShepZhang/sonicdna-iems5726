# SonicDNA · single-stage Streamlit container.
# Build context expected to be the project root, NOT the application/ folder.
#   docker build -f application/Dockerfile -t sonicdna .
#   docker run -p 8501:8501 sonicdna
#
# At build time we download the Kaggle dataset (8 MB) and re-run the
# pipeline so the resulting image contains everything needed to serve.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps:
#  - fonts-dejavu-core   for matplotlib (vinyl MoodPrint typography)
#  - curl                for the streamlit healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-dejavu-core \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first so Docker can cache the layer.
COPY source_code/requirements.txt /tmp/req-pipeline.txt
COPY application/requirements.txt /tmp/req-app.txt
RUN pip install -r /tmp/req-pipeline.txt -r /tmp/req-app.txt

# Copy source code.
COPY source_code/ /app/source_code/
COPY application/ /app/application/

# Build models + processed parquet inside the image so the runtime
# is self-contained (no Kaggle API call at request time).
WORKDIR /app/source_code
RUN python -c "import kagglehub, shutil, os; \
p = kagglehub.dataset_download('maharshipandya/-spotify-tracks-dataset'); \
os.makedirs('data/raw', exist_ok=True); \
shutil.copy(os.path.join(p, 'dataset.csv'), 'data/raw/dataset.csv')" \
    && python -m pipeline.preprocess \
    && python -m pipeline.cluster \
    && python -m pipeline.build_samples

WORKDIR /app/application

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
