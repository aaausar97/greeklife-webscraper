FROM python:3

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    cron \
    tesseract-ocr \
    libtesseract-dev \
    --no-install-recommends firefox-esr wget libdbus-glib-1-2 libxt6 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install geckodriver (WebDriver for Firefox)
RUN wget -q "https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz" -O /tmp/geckodriver.tar.gz && \
    tar -x -C /opt -f /tmp/geckodriver.tar.gz && \
    rm /tmp/geckodriver.tar.gz && \
    chmod 755 /opt/geckodriver && \
    ln -fs /opt/geckodriver /usr/bin/geckodriver && \
    ln -fs /opt/geckodriver /usr/local/bin/geckodriver

ENV DISPLAY=:99

RUN python3 --version
RUN pip install --no-cache-dir --upgrade pip
RUN pip3 --version

RUN geckodriver --version

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

CMD ["/bin/bash", "run.sh"]
