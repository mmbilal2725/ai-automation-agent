# Docker Commands Reference

Common Docker operations for building, running, and debugging Python/FastAPI containers.

## Build Image

### Standard Build

```bash
# Basic build
docker build -t app-name:latest .

# Build with custom Dockerfile
docker build -f Dockerfile.prod -t app-name:prod .

# Build with build arguments
docker build --build-arg ENV=production -t app-name:prod .

# Build without cache (force rebuild)
docker build --no-cache -t app-name:latest .
```

### BuildKit (Faster, Better Caching)

```bash
# Enable BuildKit (recommended)
export DOCKER_BUILDKIT=1

# Or use inline
DOCKER_BUILDKIT=1 docker build -t app-name:latest .

# Make permanent (Linux/Mac)
echo 'export DOCKER_BUILDKIT=1' >> ~/.bashrc
source ~/.bashrc
```

**BuildKit benefits:**
- Parallel builds (faster)
- Better caching
- Build secrets support
- Progress output

### Multi-Platform Build

```bash
# Create builder instance
docker buildx create --name mybuilder --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t app-name:latest \
  --push \
  .

# Build for ARM (Apple Silicon)
docker buildx build \
  --platform linux/arm64 \
  -t app-name:arm64 \
  .
```

## Run Container

### Basic Run

```bash
# Run detached
docker run -d -p 8000:8000 --name app app-name:latest

# Run with custom port mapping
docker run -d -p 9000:8000 --name app app-name:latest

# Run interactively (for testing)
docker run -it -p 8000:8000 app-name:latest

# Run with auto-remove on stop
docker run --rm -p 8000:8000 app-name:latest
```

### With Environment Variables

```bash
# Single variable
docker run -d -p 8000:8000 \
  -e DB_URL="postgresql://user:pass@host:5432/db" \
  --name app app-name:latest

# Multiple variables
docker run -d -p 8000:8000 \
  -e DB_URL="postgresql://..." \
  -e DEBUG="false" \
  -e LOG_LEVEL="info" \
  --name app app-name:latest

# From .env file
docker run -d -p 8000:8000 \
  --env-file .env \
  --name app app-name:latest
```

### With Volumes (Development)

```bash
# Mount current directory
docker run -d -p 8000:8000 \
  -v $(pwd):/app \
  --name app-dev app-name:dev

# Windows PowerShell
docker run -d -p 8000:8000 `
  -v ${PWD}:/app `
  --name app-dev app-name:dev

# Named volume for data persistence
docker run -d -p 8000:8000 \
  -v app-data:/app/data \
  --name app app-name:latest
```

### With Network

```bash
# Create network
docker network create app-network

# Run with network
docker run -d -p 8000:8000 \
  --network app-network \
  --name app app-name:latest

# Connect to existing database
docker run -d -p 8000:8000 \
  --network app-network \
  -e DB_URL="postgresql://user:pass@db:5432/mydb" \
  --name app app-name:latest
```

### With Resource Limits

```bash
# Set memory limit
docker run -d -p 8000:8000 \
  -m 512m \
  --name app app-name:latest

# Set CPU limit
docker run -d -p 8000:8000 \
  --cpus="1.5" \
  --name app app-name:latest

# Both memory and CPU
docker run -d -p 8000:8000 \
  -m 512m \
  --cpus="1.5" \
  --name app app-name:latest
```

## Container Management

### Start/Stop/Restart

```bash
# Stop container
docker stop app

# Start stopped container
docker start app

# Restart container
docker restart app

# Stop with timeout (default 10s)
docker stop -t 30 app

# Force kill
docker kill app
```

### Remove Containers

```bash
# Remove stopped container
docker rm app

# Force remove running container
docker rm -f app

# Remove all stopped containers
docker container prune

# Remove all containers (stopped and running)
docker rm -f $(docker ps -aq)
```

## Debug Container

### View Logs

```bash
# View all logs
docker logs app

# Follow logs (live)
docker logs -f app

# Last 100 lines
docker logs --tail 100 app

# Logs since timestamp
docker logs --since 2024-01-01T00:00:00 app

# Logs with timestamps
docker logs -t app
```

### Execute Commands

```bash
# Interactive shell
docker exec -it app bash

# Or sh (if bash not available)
docker exec -it app sh

# Run single command
docker exec app ls -la /app

# Run as root (for debugging)
docker exec -it --user root app bash

# Check which user the app runs as
docker exec app whoami
```

### Inspect Container

```bash
# Full inspection
docker inspect app

# Get specific field (IP address)
docker inspect -f '{{.NetworkSettings.IPAddress}}' app

# Get environment variables
docker inspect -f '{{.Config.Env}}' app

# Get mounted volumes
docker inspect -f '{{.Mounts}}' app

# Check running processes
docker top app

# View resource usage (live)
docker stats app

# View resource usage (all containers)
docker stats
```

### Copy Files

```bash
# Copy from container to host
docker cp app:/app/logs/error.log ./error.log

# Copy from host to container
docker cp ./config.json app:/app/config.json

# Copy directory
docker cp app:/app/logs ./logs-backup
```

## Image Management

### List and Inspect Images

```bash
# List images
docker images

# List with size
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# View image layers
docker history app:latest

# View image layers (human-readable sizes)
docker history --human app:latest

# Inspect image
docker inspect app:latest
```

### Tag and Push

```bash
# Tag image
docker tag app:latest registry.example.com/app:latest
docker tag app:latest registry.example.com/app:v1.2.3

# Login to registry
docker login registry.example.com

# Push image
docker push registry.example.com/app:latest
docker push registry.example.com/app:v1.2.3

# Push all tags
docker push --all-tags registry.example.com/app
```

### Remove Images

```bash
# Remove image
docker rmi app:latest

# Force remove
docker rmi -f app:latest

# Remove dangling images
docker image prune

# Remove all unused images
docker image prune -a

# Remove images by pattern
docker images | grep "app" | awk '{print $3}' | xargs docker rmi
```

## Clean Up

### Prune Commands

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Remove everything unused
docker system prune

# Remove everything including volumes
docker system prune -a --volumes

# Check disk usage
docker system df
```

### Complete Cleanup

```bash
# Stop all containers
docker stop $(docker ps -aq)

# Remove all containers
docker rm $(docker ps -aq)

# Remove all images
docker rmi $(docker images -q)

# Remove all volumes
docker volume rm $(docker volume ls -q)

# Remove all networks (except defaults)
docker network prune -f
```

## Testing and Validation

### Test Image

```bash
# Build and test in one line
docker build -t app:test . && \
docker run -d -p 8000:8000 --name app-test app:test && \
sleep 10 && \
curl -f http://localhost:8000/health && \
docker logs app-test && \
docker stop app-test && \
docker rm app-test

# Test with specific health check
docker run -d -p 8000:8000 --name app-test app:test
sleep 10
curl -v http://localhost:8000/health
docker logs app-test
docker exec app-test whoami  # Verify non-root
docker stop app-test
docker rm app-test
```

### Check Image Size

```bash
# Get image size
docker images app:latest --format "{{.Size}}"

# Compare sizes
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep app

# Dive tool (detailed analysis)
dive app:latest
```

### Security Scan

```bash
# Docker scan
docker scan app:latest

# Trivy scan
trivy image app:latest

# Snyk scan
snyk container test app:latest
```

## Docker Compose Commands

### Basic Operations

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f app

# Rebuild and start
docker-compose up -d --build
```

### Service Management

```bash
# List services
docker-compose ps

# Execute command in service
docker-compose exec app bash

# Run one-off command
docker-compose run app python manage.py migrate

# Scale service
docker-compose up -d --scale app=3
```

## Troubleshooting Commands

### Check Container Status

```bash
# Is container running?
docker ps | grep app

# Why did container stop?
docker ps -a | grep app

# Check exit code
docker inspect app --format='{{.State.ExitCode}}'

# Check if health check is passing
docker inspect app --format='{{.State.Health.Status}}'
```

### Network Debugging

```bash
# Check container IP
docker inspect app --format='{{.NetworkSettings.IPAddress}}'

# Check port mappings
docker port app

# Check network connectivity
docker exec app ping -c 3 google.com

# Check if port is listening
docker exec app netstat -tulpn | grep 8000

# Or with ss
docker exec app ss -tlnp | grep 8000
```

### File System Debugging

```bash
# Check disk space in container
docker exec app df -h

# Check file ownership
docker exec app ls -la /app

# Check running processes
docker exec app ps aux

# Check environment variables
docker exec app env
```

## Performance Monitoring

```bash
# Real-time stats
docker stats app

# Resource usage history
docker stats --no-stream app

# Container events
docker events --filter container=app

# System-wide info
docker info

# Check Docker daemon logs (Linux)
journalctl -u docker.service
```

## Advanced Operations

### Export/Import

```bash
# Export container to tar
docker export app > app-container.tar

# Import tar to image
docker import app-container.tar app:imported

# Save image to tar
docker save app:latest > app-image.tar

# Load image from tar
docker load < app-image.tar
```

### Commit Changes

```bash
# Create image from container
docker commit app app:modified

# With message
docker commit -m "Added configuration" app app:modified
```

### Build Cache Management

```bash
# View build cache
docker buildx du

# Clean build cache
docker buildx prune

# Clean specific cache
docker buildx prune --filter type=exec.cachemount
```

## Quick Reference

| Operation | Command |
|-----------|---------|
| Build | `docker build -t app:latest .` |
| Run | `docker run -d -p 8000:8000 --name app app:latest` |
| Stop | `docker stop app` |
| Remove | `docker rm app` |
| Logs | `docker logs -f app` |
| Shell | `docker exec -it app bash` |
| Stats | `docker stats app` |
| Clean | `docker system prune -a` |

## See Also

- `troubleshooting.md` - Detailed troubleshooting guide
- `cicd.md` - CI/CD pipeline examples
- `best-practices.md` - Command best practices
