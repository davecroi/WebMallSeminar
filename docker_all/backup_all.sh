#!/bin/bash
set -e  # Exit immediately if any command fails

BACKUP_DIR="$(pwd)/backup"

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

echo "=== Backing Up Docker Volumes for All Shops ==="

# Function to back up a single shop
backup_shop() {
  SHOP_ID=$1
  WORDPRESS_VOLUME="woocommerce_wordpress_data_shop${SHOP_ID}"
  MARIADB_VOLUME="woocommerce_mariadb_data_shop${SHOP_ID}"

  echo "=== Backing Up WordPress Data for Shop ${SHOP_ID} ==="
  docker run --rm \
    -v ${WORDPRESS_VOLUME}:/volume \
    -v "${BACKUP_DIR}":/backup \
    busybox \
    tar czf /backup/wordpress_data_shop${SHOP_ID}.tar.gz -C /volume .

  echo "=== Backing Up MariaDB Data for Shop ${SHOP_ID} ==="
  docker run --rm \
    -v ${MARIADB_VOLUME}:/volume \
    -v "${BACKUP_DIR}":/backup \
    busybox \
    tar czf /backup/mariadb_data_shop${SHOP_ID}.tar.gz -C /volume .
}

# Run backup for all three shops
for SHOP in 1 2 3 4; do
  backup_shop ${SHOP}
done

echo "=== Backup Complete! All data saved in ${BACKUP_DIR} ==="
