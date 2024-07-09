#!/bin/bash

# Create or update config.json with environment variables
cat <<EOL > config.json
{
    "instagram": {
        "username": "${INSTA_USERNAME}",
        "password": "${INSTA_PASSWORD}"
    },
    "google_drive": {
        "sheet_url": "${GDRIVE_SHEET_URL}"
    },
    "util":{
        "days_to_scrape": ${DAYS_TO_SCRAPE:-7},
        "base_wait_time": ${BASE_WAIT_TIME:-30},
        "base_rand_time": ${BASE_RAND_TIME:-10}
    }
}
EOL

# Run the main process
exec "$@"

