FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p generated_models uploads

# Expose port
EXPOSE 8080

# Set environment variables
ENV FLASK_APP=financial_models_ui.py
ENV FLASK_ENV=production
ENV PORT=8080

# Run the application
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 300 --keep-alive 5 --max-requests 50 --max-requests-jitter 5 --worker-class sync --log-level info --access-logfile - --error-logfile - financial_models_ui:app"]

