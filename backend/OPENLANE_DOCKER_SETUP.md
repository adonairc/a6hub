# OpenLane/LibreLane Docker Setup Guide

This guide explains how to configure and use OpenLane/LibreLane Docker images for ASIC builds in a6hub.

## Overview

a6hub uses Docker containers to run OpenLane/LibreLane ASIC design flows. The system supports multiple Docker images depending on your needs.

## Available Docker Images

### 1. OpenLane v1 (Recommended - Stable)

**Image:** `efabless/openlane:latest`

**Pros:**
- Stable and well-tested
- Extensive documentation
- Large community support
- Works with most existing designs

**Cons:**
- Older architecture
- Not recommended for new projects by the OpenLane team

**Pull the image:**
```bash
docker pull efabless/openlane:latest
```

### 2. OpenLane 2

**Image:** `ghcr.io/efabless/openlane2:2.3.1` (or latest version)

**Pros:**
- Modern architecture
- Better performance
- Active development
- Successor to OpenLane v1

**Cons:**
- May have breaking changes from v1
- Smaller community (newer)

**Pull the image:**
```bash
docker pull ghcr.io/efabless/openlane2:2.3.1
```

### 3. LibreLane (Experimental)

**Image:** Not yet publicly available via Docker Hub/GHCR

LibreLane is the renamed/forked version of OpenLane 2. As of early 2025, it requires:
- Building from source
- Using the `--dockerized` flag when installed locally
- Docker images may not be published yet

**More info:** https://github.com/librelane/librelane

## Configuration

### Default Image

The default Docker image is configured in two places:

**1. Backend Schema** (`backend/app/schemas/librelane.py`):
```python
docker_image: str = Field(default="efabless/openlane:latest", ...)
```

**2. Worker Task** (`backend/app/workers/tasks.py`):
```python
docker_image = config.get("docker_image", "efabless/openlane:latest")
```

### Changing the Default Image

**Option A: Environment Variable** (Coming soon)
```bash
# In .env file
DEFAULT_OPENLANE_IMAGE=ghcr.io/efabless/openlane2:2.3.1
```

**Option B: Per-Build Configuration**

When starting a build via the API or frontend, specify the image:
```json
{
  "config": {
    "design_name": "my_chip",
    "pdk": "sky130_fd_sc_hd",
    "docker_image": "ghcr.io/efabless/openlane2:2.3.1"
  }
}
```

**Option C: Update Code Defaults**

Edit the default in `backend/app/schemas/librelane.py`:
```python
docker_image: str = Field(default="your-preferred-image:tag", ...)
```

## Pulling Required Images

Before running builds, pull the Docker image:

```bash
# For OpenLane v1
docker pull efabless/openlane:latest

# For OpenLane 2
docker pull ghcr.io/efabless/openlane2:2.3.1

# Alternative source
docker pull ghcr.io/the-openroad-project/openlane
```

## Docker Access from Celery Worker

The Celery worker needs access to Docker to run OpenLane containers.

### Docker Compose Setup (Recommended)

In `docker-compose.yml`, the worker container already has Docker access:

```yaml
celery-worker:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
```

This mounts the host's Docker socket, allowing the worker to spawn OpenLane containers.

### Local Development

If running the worker locally (not in Docker), ensure:

1. Docker is installed and running
2. Your user has Docker permissions:
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. Test Docker access:
   ```bash
   docker ps
   ```

## Troubleshooting

### Error: "manifest unknown"

**Full Error:**
```
Error response from daemon: manifest unknown
```

**Cause:** The Docker image doesn't exist or the tag is wrong.

**Solutions:**
1. Check the image exists:
   ```bash
   # Visit Docker Hub
   https://hub.docker.com/r/efabless/openlane/tags

   # Or GitHub Container Registry
   https://github.com/efabless/openlane2/pkgs/container/openlane2
   ```

2. Update the image to a valid one:
   - Change in code: `backend/app/schemas/librelane.py`
   - Or configure per-build

3. Pull the image manually:
   ```bash
   docker pull efabless/openlane:latest
   ```

### Error: "exit code 125"

**Cause:** Docker failed to run the container. Check:
- Image exists (see above)
- Docker has permissions
- Sufficient disk space

**Check logs:**
```bash
docker logs a6hub-celery-worker
```

### Error: "Permission denied" accessing Docker

**Cause:** Worker doesn't have Docker socket permissions.

**Solutions:**

1. Add user to docker group:
   ```bash
   sudo usermod -aG docker $USER
   ```

2. For Docker Compose, ensure socket is mounted:
   ```yaml
   volumes:
     - /var/run/docker.sock:/var/run/docker.sock
   ```

3. Restart services:
   ```bash
   docker-compose restart celery-worker
   ```

### Image Pull Fails

**Error:** "unauthorized" or "denied"

**Cause:** Private registry or authentication required.

**Solutions:**

1. For GitHub Container Registry (GHCR):
   ```bash
   # Login with GitHub token
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   ```

2. For Docker Hub:
   ```bash
   docker login
   ```

## Version Compatibility

| Image | PDK Support | Recommended For |
|-------|-------------|-----------------|
| `efabless/openlane:latest` | Sky130, GF180MCU | Production, existing designs |
| `ghcr.io/efabless/openlane2:2.3.1` | Sky130, GF180MCU, newer PDKs | New designs, experimentation |
| LibreLane (source install) | Sky130, GF180MCU, IHP130 | Cutting edge, development |

## PDK (Process Design Kit) Requirements

OpenLane Docker images include PDKs, but verify support:

**Sky130 (default):**
- Included in all images
- Most tested and stable
- 130nm open-source PDK

**GF180MCU:**
- Included in newer images
- 180nm process
- Better for analog/mixed-signal

**IHP130:**
- Newer PDK
- May require latest images or LibreLane

## Network Requirements

Docker images can be large (several GB). Ensure:
- Sufficient bandwidth for initial pull
- Disk space (5-10 GB per image)
- No firewall blocking Docker Hub/GHCR

## Performance Considerations

**CPU/Memory:**
- OpenLane builds are CPU-intensive
- Minimum: 4 CPU cores, 8GB RAM
- Recommended: 8+ CPU cores, 16GB+ RAM

**Disk Space:**
- Docker images: 5-10 GB each
- Build artifacts: 100-500 MB per job
- Logs: 1-10 MB per job

**Concurrency:**
- Set Celery worker concurrency based on resources
- Default: `--concurrency=2`
- Adjust in `docker-compose.yml`:
  ```yaml
  command: celery -A app.workers.celery_app worker --loglevel=info --queues=build --concurrency=4
  ```

## Testing Your Setup

1. **Pull the image:**
   ```bash
   docker pull efabless/openlane:latest
   ```

2. **Test container:**
   ```bash
   docker run --rm efabless/openlane:latest openlane --version
   ```

3. **Start a build in a6hub:**
   - Upload a Verilog file
   - Configure build settings
   - Start the build
   - Monitor logs for successful container execution

## Additional Resources

- **OpenLane Documentation:** https://github.com/The-OpenROAD-Project/OpenLane
- **OpenLane 2 Documentation:** https://github.com/efabless/openlane2
- **LibreLane:** https://github.com/librelane/librelane
- **Sky130 PDK:** https://github.com/google/skywater-pdk
- **Docker Hub (OpenLane):** https://hub.docker.com/r/efabless/openlane
- **GHCR (OpenLane 2):** https://github.com/efabless/openlane2/pkgs/container/openlane2

## Getting Help

If you encounter issues:

1. Check the a6hub troubleshooting guide: `backend/TROUBLESHOOTING.md`
2. Review OpenLane/LibreLane logs in Celery worker
3. Test the Docker image independently of a6hub
4. Report issues with full error logs and configuration
