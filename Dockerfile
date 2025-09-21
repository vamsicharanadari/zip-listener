# Use lightweight Python image
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY main.py .

# Ensure logs folder exists
RUN mkdir -p /app/logs

# Start the app
CMD ["python", "main.py"]