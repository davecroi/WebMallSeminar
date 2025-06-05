#!/bin/bash

# Load environment variables from .env file
export $(grep -v '^#' ../.env | xargs)

# Define the container names based on your Docker Compose setup
CONTAINERS=(
  "WebMall_wordpress_shop1"
  "WebMall_wordpress_shop2"
  "WebMall_wordpress_shop3"
  "WebMall_wordpress_shop4"
)

# Function to check if the container is healthy
check_health() {
  local container=$1
  local health_status

  health_status=$(docker inspect --format '{{.State.Health.Status}}' "$container" 2>/dev/null)

  if [ "$health_status" == "healthy" ]; then
    return 0
  else
    return 1
  fi
}

# Loop through the containers and check health
for i in "${!CONTAINERS[@]}"; do
  CONTAINER="${CONTAINERS[$i]}"
  PORT_VAR="SHOP$((i + 1))_PORT"
  PORT="${!PORT_VAR}"

  echo "Checking health status of $CONTAINER..."
  
  # Wait for the container to be healthy
  until check_health "$CONTAINER"; do
    echo "$CONTAINER is not healthy yet. Waiting for 5 seconds..."
    sleep 5
  done

  echo "$CONTAINER is healthy. Proceeding with running fix_urls.sh..."

  # Run the fix-urls.sh script inside the container with the respective port
  docker exec "$CONTAINER" /bin/bash -c "/usr/local/bin/fix_urls.sh $PORT"

  echo "Finished running fix_urls.sh on $CONTAINER with port $PORT."
done
echo "Finished all url-fixes for the 4 shops"