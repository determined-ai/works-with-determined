#!/bin/bash

# Write an auth token from the determined master.
# Run daily as a CRON job or similar. 
# The "..." should be replaced with the relevant fields.
# The $PATH_TO_TOKEN placeholder in the prometheus.yml should be replaced
# with the path to the token.

curl https://.../api/v1/auth/login -X POST -d '{"username": "...", "password": "..."}' -s |\
        jq -r .token >determined-bearer-token.txt