# FoodFinder Docker Setup

This guide explains how to run FoodFinder using Docker and Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) installed

## Quick Start

### 1. Clone/Navigate to the project

```bash
cd /var/www/html/FoodFinder
```

### 2. Create your .env file from the template

```bash
cp .env.example .env
```

### 3. Edit .env with your actual credentials

**⚠️ IMPORTANT: Keep `.env` file PRIVATE and NEVER commit it to git!**

The `.env` file is listed in `.gitignore` and should contain your actual credentials:

```env
# Database Configuration
DB_HOST=mysql
DB_PORT=3306
DB_NAME=foodfinder
DB_USER=foodfinder_user
DB_PASSWORD=your_secure_password_here
MYSQL_ROOT_PASSWORD=your_secure_root_password
DATABASE_URL="mysql://foodfinder_user:your_secure_password_here@mysql:3306/foodfinder"

# Node Environment
NODE_ENV=production
```

**Never share or commit this file!** It contains sensitive credentials.

### 3. Build and start the containers

```bash
docker-compose up --build
```

This will:
- Build the Next.js web app image
- Start a MySQL database container
- Initialize the database with the schema
- Start the FoodFinder web app on port 3003

### 4. Access the app

Open your browser and navigate to:
```
http://localhost:3003
```

## Common Commands

### Start the app (without rebuilding)
```bash
docker-compose up
```

### Start in background
```bash
docker-compose up -d
```

### Stop the app
```bash
docker-compose down
```

### Stop and remove all data
```bash
docker-compose down -v
```

### View logs
```bash
docker-compose logs -f
```

### View web app logs only
```bash
docker-compose logs -f web
```

### View database logs only
```bash
docker-compose logs -f mysql
```

### Rebuild the web app image
```bash
docker-compose build --no-cache web
```

## Architecture

- **web**: Next.js application running on port 3003
- **mysql**: MySQL 8.0 database on port 3306
- **foodfinder-network**: Docker network connecting the services

## Database

The MySQL database is automatically initialized with `foodfinder_schema.sql` when the container first starts.

Database credentials (from `.env`):
- Host: `mysql` (inside Docker network) or `localhost` (from host)
- Port: `3306`
- Database: `foodfinder`
- User: `kevin`
- Password: `Squogg27`

## Security Best Practices

### Environment Variables

- **Never commit `.env` to git** — It's automatically ignored and should contain secrets
- **Always use `.env.example`** — This is the template and IS committed to git
- **Use strong passwords** — For production, use generated secure passwords
- **Rotate credentials regularly** — Especially in production environments

### Docker Security

- Keep Docker images updated: `docker-compose pull`
- Don't run containers as root unnecessarily
- Use read-only volumes where possible
- Limit resource usage with memory/CPU limits
- Don't expose sensitive ports unnecessarily

### For Production

1. Use a secrets management service (AWS Secrets Manager, Vault, etc.)
2. Never put credentials in docker-compose.yml directly
3. Use environment variables from CI/CD secrets
4. Consider using Docker secrets for swarm deployments
5. Implement proper access controls and logging

## Troubleshooting

### Port already in use

If port 3003 or 3306 is already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "3003:3003"  # Change first number to your desired port
```

### Database connection issues

Ensure MySQL is fully initialized before the app tries to connect:

```bash
docker-compose logs mysql
```

Wait for "ready for connections" message.

### Rebuild everything from scratch

```bash
docker-compose down -v
docker-compose up --build
```

## Production Considerations

For production deployment:

1. Use environment variables for sensitive data (don't commit `.env`)
2. Set `NODE_ENV=production`
3. Use a reverse proxy (nginx/Apache) in front of the app
4. Set up proper backup strategies for MySQL data
5. Consider using a managed database service instead of containerized MySQL
6. Add SSL/TLS certificates
7. Use proper logging and monitoring

## Python Scraper in Docker

To add the Python scraper to Docker, create an additional service in `docker-compose.yml`:

```yaml
scraper:
  build:
    context: ./agent
    dockerfile: Dockerfile
  container_name: foodfinder-scraper
  environment:
    DATABASE_URL: "mysql://kevin:Squogg27@mysql:3306/foodfinder"
  depends_on:
    mysql:
      condition: service_healthy
  networks:
    - foodfinder-network
```

And create `agent/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "-m", "scraper.main"]
```

Then run:
```bash
docker-compose up -d scraper
```
