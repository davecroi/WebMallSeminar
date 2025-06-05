#!/bin/bash

chmod +x fix_urls.sh
docker compose --env-file ../.env up -d
#echo "Script to adapt url if port was changed runs, wait until it is finished"
#sleep 30

#./adapt_urls_to_port.sh
