FROM python:3

# Set the non-interactive frontend for APT
ENV DEBIAN_FRONTEND=noninteractive

# Update and install required packages
RUN apt-get update && apt-get install -y \
    cron \
    tesseract-ocr \
    libtesseract-dev \
    firefox-esr \
    wget \
    libdbus-glib-1-2 \
    libxt6 \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install geckodriver (WebDriver for Firefox)
RUN wget -q "https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz" -O /tmp/geckodriver.tar.gz && \
    tar -x -C /opt -f /tmp/geckodriver.tar.gz && \
    rm /tmp/geckodriver.tar.gz && \
    chmod 755 /opt/geckodriver && \
    ln -fs /opt/geckodriver /usr/bin/geckodriver && \
    ln -fs /opt/geckodriver /usr/local/bin/geckodriver

# Set display environment variable
ENV DISPLAY=:99

# Check Python version
RUN python3 --version

# Upgrade pip and check version
RUN pip install --no-cache-dir --upgrade pip
RUN pip3 --version

# Check geckodriver version
RUN geckodriver --version

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy application files
COPY . .

# Start the application
CMD [ "python3", "scraper.py"]