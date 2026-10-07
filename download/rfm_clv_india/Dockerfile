# Python 3.11 slim base — small image, enough for our deps
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Prophet needs cmdstan-dev or use pystan wheel)
# Slim variant: skip cmdstan, use statsmodels fallback for the forecast module
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    || (echo "Prophet install failed; using statsmodels fallback" \
        && pip install --no-cache-dir pandas numpy scipy scikit-learn \
                       matplotlib seaborn plotly streamlit tabulate statsmodels pytest)

# Copy the rest of the application
COPY . .

# Pre-create the data and reports directories
RUN mkdir -p data/raw data/processed reports/figures

# Expose Streamlit's default port
EXPOSE 8501

# Healthcheck — Streamlit responds on / with 200
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=5)" || exit 1

# Default command: launch Streamlit
# Disable file watcher (we're not developing inside the container) for stability
# Set max upload size to 50MB to allow CSV uploads
ENTRYPOINT ["streamlit", "run", "app.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0", \
            "--server.fileWatcherType=none", \
            "--server.maxUploadSize=50"]
