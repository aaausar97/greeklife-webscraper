#!/bin/sh
# Try to ping an external server
ping -c 1 8.8.8.8 > /dev/null 2>&1

# Check the exit code of the ping command
if [ $? -eq 0 ]; then
  exit 0
else
  exit 1
fi