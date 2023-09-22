#!/bin/bash
echo "running"
sleep 5 # wait for vpn container to start
echo "login script running"
python3 -m helpers.firefox_cookie
sleep 15
echo "scraper script running"
python3 scraper.py