# Greek Life Webscraper

## Launch all services with docker-compose

This is the best way to launch an app, it will launch following services:

1) Python Docker Container w/ ./app mounted
2) Gluetun VPN

### Prerequisites

You need to install Docker and docker-compose, you may find instructions
for your OS by these links:

- https://docs.docker.com/engine/install/
- https://docs.docker.com/compose/install/

### Launch

```
docker-compose build  
docker-compose up
```

## LOCAL RUN

### Make sure you have Docker installed on device [https://www.python.org/downloads/]

### After installing python and pip, open terminal and navigate to directory of script and run the following commands

> pip3 install virtualenv
>
> virtualenv venv
>
> pip3 install -r requirements.txt
>
> source venv/bin/activate

## HOW TO RUN SCRIPT

### run commands in terminal in same directory as script

> source venv/bin/activate
> python3 scraper.py

### the scraper will start and run until completion

## Change Settings

### some ig, google, and util settings can be adjusted in the config.json file

## Run on schedule

### Set up cron [https://www.tutorialspoint.com/unix_commands/crontab.htm] in terminal to always run the script at the same time