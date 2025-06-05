#!/bin/bash
set -e  # Exit immediately if any command exits with a non-zero status.

chmod +x fix_urls.sh
BACKUP_DIR="$(pwd)/backup"
CONFIG_DIR="$(pwd)/deployed_wp_config"

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

  echo "=== Copying the wpconfig.php file for Shop ${SHOP_ID} ==="
  docker run --rm \
    -v ${WORDPRESS_VOLUME}:/volume \
    -v "${CONFIG_DIR}":/config \
    busybox \
    cp /config/shop_${SHOP_ID}.php /volume/wp-config.php

  echo "=== Restoring MariaDB Volume Data for Shop ${SHOP_ID} ==="
  docker run --rm \
    -v ${MARIADB_VOLUME}:/volume \
    -v "${BACKUP_DIR}":/backup \
    busybox \
    tar xzf /backup/mariadb_data_shop${SHOP_ID}.tar.gz -C /volume

}

# Restore data for all four shops
for SHOP in 1 2 3 4; do
  restore_shop ${SHOP}
done

echo "=== Starting Containers with Docker Compose ==="
docker compose --env-file ../.env up -d

echo "=== Waiting for all containers to be healthy ==="
sleep 60

echo "=== Fixing URLs ==="
docker exec WebMall_wordpress_shop1 /bin/bash -c "/usr/local/bin/fix_urls_deploy.sh 'http://localhost:8080' 'https://webmall-1.informatik.uni-mannheim.de/'"
docker exec WebMall_wordpress_shop2 /bin/bash -c "/usr/local/bin/fix_urls_deploy.sh 'http://localhost:8081' 'https://webmall-2.informatik.uni-mannheim.de/'"
docker exec WebMall_wordpress_shop3 /bin/bash -c "/usr/local/bin/fix_urls_deploy.sh 'http://localhost:8082' 'https://webmall-3.informatik.uni-mannheim.de/'"
docker exec WebMall_wordpress_shop4 /bin/bash -c "/usr/local/bin/fix_urls_deploy.sh 'http://localhost:8083' 'https://webmall-4.informatik.uni-mannheim.de/'"

echo "=== Restoration Complete for All Shops! ==="
