FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for audio files
RUN mkdir -p audio_files

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose Streamlit default port
EXPOSE 8000

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
