# Use Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        libpq-dev \
        dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy start script first and make it executable
COPY start.sh /app/
RUN chmod +x /app/start.sh \
    && dos2unix /app/start.sh  # Fix line endings

# Copy project
COPY . /app/

# Create media directory
RUN mkdir -p /app/media && chmod 777 /app/media

# Expose ports
EXPOSE 5000
EXPOSE 1025
EXPOSE 1143

# Command to run both servers
CMD ["./start.sh"] 