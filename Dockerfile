FROM python:3.10-alpine

WORKDIR /app

# Install Chromium and dependencies
RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    python3-dev \
    build-base \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Set environment variables for Chromium
ENV CHROME_BIN=/usr/bin/chromium-browser \
    CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port 8000
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]