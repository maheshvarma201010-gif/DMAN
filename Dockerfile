FROM python:3.11-slim-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Ensure necessary directories exist
RUN mkdir -p downloads sessions

# Run the bot
CMD ["python", "bot.py"]
