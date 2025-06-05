#!/bin/bash
set -e  # Exit immediately if any command exits with a non-zero status.

chmod +x fix_urls.sh
BACKUP_DIR="$(pwd)/backup"

# Function to restore a single shop
restore_shop() {
  SHOP_ID=$1
  WORDPRESS_VOLUME="woocommerce_wordpress_data_shop${SHOP_ID}"
  MARIADB_VOLUME="woocommerce_mariadb_data_shop${SHOP_ID}"

  echo "=== Creating Docker Volumes for Shop ${SHOP_ID} (if not already created) ==="
  docker volume create ${WORDPRESS_VOLUME} || true
  docker volume create ${MARIADB_VOLUME} || true

  echo "=== Restoring WordPress Volume Data for Shop ${SHOP_ID} ==="
  docker run --rm \
    -v ${WORDPRESS_VOLUME}:/volume \
    -v "${BACKUP_DIR}":/backup \
    busybox \
    tar xzf /backup/wordpress_data_shop${SHOP_ID}.tar.gz -C /volume

  echo "=== Restoring MariaDB Volume Data for Shop ${SHOP_ID} ==="
  docker run --rm \
    -v ${MARIADB_VOLUME}:/volume \
    -v "${BACKUP_DIR}":/backup \
    busybox \
    tar xzf /backup/mariadb_data_shop${SHOP_ID}.tar.gz -C /volume
}

# Restore data for all three shops
for SHOP in 1 2 3 4; do
  restore_shop ${SHOP}
done

echo "=== Starting Containers with Docker Compose ==="
docker compose --env-file ../.env up -d

#echo "Script to adapt url if port was changed runs, wait until it is finished"
#sleep 30

#./adapt_urls_to_port.sh

echo "=== Restoration Complete for All Shops! ==="
