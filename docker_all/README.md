# WebMall Docker Setup

This directory contains the Docker configuration for running the WebMall e-commerce environment with 4 WordPress shops, MariaDB databases, and Elasticsearch.

## Prerequisites

-   Docker and Docker Compose installed on your system
-   At least 4GB of RAM available for containers
-   Ports 8081-8084, 9200, and your chosen frontend port available

## Quick Start

### 1. Environment Configuration

Create a `.env` file in the parent directory (one level up from this `docker_all` folder):

```bash
# Copy the example file 
cp ../.env.example ../.env
```
Set the SHOP_PORT variable as desired.

### 2. Starting the Containers

#### Option A: Fresh Start (Recommended for first run)

```bash
cd docker_all
./restore_all_and_deploy_local.sh
```

This script will:

-   Load environment variables from `../.env`
-   Create Docker volumes for each shop
-   Restore backup data if available
-   Configure WordPress with your specified ports
-   Start all containers
-   Fix URLs and apply configurations

#### Option B: Start Without Restore (if containers already configured)

```bash
cd docker_all
docker compose --env-file ../.env up -d
```

### 3. Verify Installation

After starting, you can access:

-   **Shop 1**: http://localhost:8081 (or your configured SHOP1_PORT)
-   **Shop 2**: http://localhost:8082 (or your configured SHOP2_PORT)
-   **Shop 3**: http://localhost:8083 (or your configured SHOP3_PORT)
-   **Shop 4**: http://localhost:8084 (or your configured SHOP4_PORT)
-   **Frontend**: http://localhost:3000 (or your configured FRONTEND_PORT)
-   **Elasticsearch**: http://localhost:9200

## Container Management

### Stop All Containers

```bash
cd docker_all
docker compose --env-file ../.env down
```

### View Container Status

```bash
cd docker_all
docker compose --env-file ../.env ps
```

### View Logs

```bash
# All containers
docker compose --env-file ../.env logs

# Specific shop
docker compose --env-file ../.env logs wordpress_shop1

# Follow logs in real-time
docker compose --env-file ../.env logs -f
```

### Restart Containers

```bash
cd docker_all
docker compose --env-file ../.env restart
```

## Configuration Details

### WordPress Configuration

-   **Admin Username**: admin
-   **Admin Password**: admin
-   **Database**: Each shop has its own MariaDB instance
-   **Search**: Elasticsearch integration enabled for all shops

### Port Configuration

The shops are configured to use the ports specified in your `.env` file. The restore script automatically:

1. Reads your port configuration from `.env`
2. Updates WordPress configuration files with the correct ports
3. Copies the configured files to each container

### Volumes

Each shop maintains persistent data in Docker volumes:

-   `woocommerce_wordpress_data_shop[1-4]`: WordPress files and uploads
-   `woocommerce_mariadb_data_shop[1-4]`: Database data
-   `esdata`: Elasticsearch data

## Troubleshooting

### Containers Won't Start

1. Check if ports are available:
    ```bash
    netstat -tulpn | grep :8081
    ```
2. Verify `.env` file exists and has correct format
3. Check Docker logs for specific errors

### Port Conflicts

If you get port binding errors, update your `.env` file with different ports:

```bash
SHOP1_PORT=8091
SHOP2_PORT=8092
# etc.
```

### Permission Issues

If you encounter permission issues:

```bash
# Fix script permissions
chmod +x restore_all_and_deploy_local.sh
chmod +x fix_urls.sh
chmod +x fix_urls_deploy.sh
```

### Reset Everything

To completely reset and start fresh:

```bash
# Stop and remove containers
docker compose --env-file ../.env down -v

# Remove volumes (WARNING: This deletes all data!)
docker volume rm woocommerce_wordpress_data_shop1 woocommerce_wordpress_data_shop2 woocommerce_wordpress_data_shop3 woocommerce_wordpress_data_shop4
docker volume rm woocommerce_mariadb_data_shop1 woocommerce_mariadb_data_shop2 woocommerce_mariadb_data_shop3 woocommerce_mariadb_data_shop4

# Start fresh
./restore_all_and_deploy_local.sh
```

## Architecture

The setup includes:

-   **4 WordPress Shops**: Each running on Bitnami WordPress image
-   **4 MariaDB Databases**: One for each shop
-   **Elasticsearch**: Shared search engine for all shops
-   **Frontend**: Nginx-based frontend application
-   **Network**: All containers communicate via `webmall` Docker network

## File Structure

```
docker_all/
├── deployed_wp_config_local/   # WordPress configuration templates
│   ├── shop_1.php
│   ├── shop_2.php
│   ├── shop_3.php
│   └── shop_4.php
├── backup_all.sh               # Script to create backup of all running docker volumes
├── docker-compose.yml          # Main container orchestration
├── fix_urls_deploy.sh          # Deployment URL fixing
├── index.html                  # WebMall starting and submission page
└── README.md                   # This file
├── restore_all_and_deploy_local.sh  # Setup and deployment script
```

