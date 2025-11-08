# LibreLane Python Installation Guide

This guide explains how to install and configure LibreLane as a Python package for use with a6hub.

## Overview

a6hub now uses LibreLane as a Python library instead of Docker containers. This provides better integration, faster execution, and easier debugging.

## Requirements

- **Python:** 3.8.1 or higher (supports 3.8, 3.9, 3.10, 3.11, 3.12, 3.13)
- **Operating System:** Linux (x86-64 or aarch64), macOS, or Windows with WSL2
- **PDK:** Sky130, GF180MCU, or IHP130
- **Disk Space:** ~5GB for PDKs and tools

## Installation

### Step 1: Install LibreLane

LibreLane is installed via pip:

```bash
pip install librelane
```

For a specific version:

```bash
pip install librelane==2.4.0
```

### Step 2: Install Process Design Kit (PDK)

LibreLane requires a PDK to function. The most common is Sky130.

**Option A: Automatic PDK Installation (Recommended)**

LibreLane can automatically install PDKs:

```bash
python3 -m librelane --install-pdk sky130
```

This installs the Sky130 PDK to `~/.ciel/` by default.

**Option B: Manual PDK Installation**

```bash
# Clone the Sky130 PDK
git clone https://github.com/google/skywater-pdk.git
cd skywater-pdk
git submodule update --init libraries/sky130_fd_sc_hd/latest

# Set PDK_ROOT environment variable
export PDK_ROOT=/path/to/skywater-pdk
```

**Option C: Using Volare (PDK Manager)**

```bash
# Install volare
pip install volare

# Install Sky130
volare enable --pdk sky130 $(volare ls-remote --pdk sky130 | head -1)
```

### Step 3: Configure PDK Path

Update your `.env` file:

```bash
# In backend/.env
PDK_ROOT=/root/.ciel  # or your custom path
```

Or set the environment variable:

```bash
export PDK_ROOT=/path/to/pdk
```

### Step 4: Verify Installation

Test that LibreLane is installed correctly:

```bash
python3 -m librelane --version
```

You should see output like:
```
LibreLane 2.4.0
```

Test with a sample design:

```bash
# Create a simple config
cat > test_config.json <<EOF
{
  "DESIGN_NAME": "test",
  "VERILOG_FILES": ["dir::test.v"],
  "CLOCK_PERIOD": 10,
  "CLOCK_PORT": "clk"
}
EOF

# Run LibreLane (will fail without actual Verilog, but tests installation)
python3 -m librelane test_config.json
```

## Docker Setup (Development Environment)

### Update Dockerfile.worker

Add LibreLane to the worker container:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install LibreLane and PDK
RUN python3 -m librelane --install-pdk sky130

# Copy application code
COPY . .

CMD ["celery", "-A", "app.workers.celery_app", "worker", "--loglevel=info"]
```

### Update docker-compose.yml

Ensure the worker has the PDK path configured:

```yaml
celery-worker:
  build:
    context: .
    dockerfile: Dockerfile.worker
  environment:
    - PDK_ROOT=/root/.ciel
    - POSTGRES_HOST=postgres
    - REDIS_HOST=redis
    - MINIO_ENDPOINT=minio:9000
  volumes:
    - ./:/app
    - storage_data:/tmp/a6hub-storage
  depends_on:
    - redis
    - postgres
```

## Configuration

### Default Settings

In `backend/app/core/config.py`:

```python
# EDA Tools paths
PDK_ROOT: str = "/opt/pdk"  # or "/root/.ciel" for auto-installed PDKs
```

### Per-Build Configuration

You can override settings per-build via the API:

```json
{
  "config": {
    "design_name": "my_chip",
    "pdk": "sky130_fd_sc_hd",
    "verilog_files": ["src/top.v"],
    "use_docker": false
  }
}
```

## Available PDKs

| PDK | Description | Install Command |
|-----|-------------|-----------------|
| **sky130** | SkyWater 130nm (most common) | `python3 -m librelane --install-pdk sky130` |
| **gf180mcu** | GlobalFoundries 180nm | `python3 -m librelane --install-pdk gf180mcu` |
| **ihp130** | IHP 130nm (newer) | `python3 -m librelane --install-pdk ihp130` |

## Troubleshooting

### Error: "No module named 'librelane'"

**Cause:** LibreLane not installed or wrong Python environment.

**Solution:**
```bash
# Check Python version
python3 --version  # Should be 3.8.1+

# Install LibreLane
pip install librelane

# Verify installation
python3 -m librelane --version
```

### Error: "PDK not found"

**Cause:** PDK_ROOT not set or PDK not installed.

**Solutions:**

1. **Check PDK_ROOT:**
   ```bash
   echo $PDK_ROOT
   ls $PDK_ROOT  # Should show PDK files
   ```

2. **Install PDK:**
   ```bash
   python3 -m librelane --install-pdk sky130
   ```

3. **Set PDK_ROOT:**
   ```bash
   export PDK_ROOT=/root/.ciel
   ```

4. **Update .env:**
   ```bash
   # In backend/.env
   PDK_ROOT=/root/.ciel
   ```

### Error: "Command not found: python3"

**Cause:** Python 3 not installed or not in PATH.

**Solutions:**

```bash
# Ubuntu/Debian
sudo apt-get install python3 python3-pip

# macOS
brew install python3

# Verify
python3 --version
```

### Error: "Build fails with LibreLane errors"

**Check logs:**

```bash
# In a6hub build logs, look for:
# - PDK path issues
# - Missing tools
# - Verilog syntax errors
```

**Common issues:**

1. **PDK version mismatch:** Ensure PDK is up-to-date
   ```bash
   python3 -m librelane --install-pdk sky130 --upgrade
   ```

2. **Insufficient disk space:** LibreLane needs ~5GB
   ```bash
   df -h
   ```

3. **Missing system tools:** Install build tools
   ```bash
   sudo apt-get install build-essential
   ```

### Error: "Permission denied"

**Cause:** PDK directory not writable.

**Solutions:**

```bash
# Check permissions
ls -ld $PDK_ROOT

# Fix permissions
sudo chown -R $USER $PDK_ROOT
```

### Slow Builds

**Causes:**
- First-time setup downloads PDK and tools (~5GB)
- Complex designs take longer
- Limited CPU/memory

**Solutions:**

1. **Pre-download PDK:**
   ```bash
   python3 -m librelane --install-pdk sky130
   ```

2. **Increase resources:**
   - Add more CPU cores to worker
   - Increase memory allocation

3. **Use caching:**
   - PDKs are cached after first download
   - Subsequent builds are faster

## Performance Optimization

### CPU/Memory

- **Minimum:** 4 CPU cores, 8GB RAM
- **Recommended:** 8+ CPU cores, 16GB+ RAM
- **For large designs:** 16+ CPU cores, 32GB+ RAM

### Concurrency

Adjust Celery worker concurrency based on resources:

```yaml
# In docker-compose.yml
command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
```

### Caching

LibreLane caches:
- Downloaded PDKs (`~/.ciel/`)
- Tool binaries
- Build artifacts

Preserve these between builds for better performance.

## Development Workflow

### Local Development (No Docker)

```bash
# Install LibreLane
pip install librelane

# Install PDK
python3 -m librelane --install-pdk sky130

# Set environment
export PDK_ROOT=/root/.ciel

# Run backend
cd backend
uvicorn main:app --reload

# Run worker
celery -A app.workers.celery_app worker --loglevel=info
```

### Docker Development

```bash
# Build worker with LibreLane
cd backend
docker-compose build celery-worker

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f celery-worker
```

## Comparing Python vs Docker

| Feature | Python (Recommended) | Docker |
|---------|---------------------|--------|
| **Setup** | `pip install librelane` | Pull ~5GB images |
| **Speed** | Faster (no container overhead) | Slower (container startup) |
| **Debugging** | Easier (direct access) | Harder (inside container) |
| **Updates** | `pip install --upgrade` | Pull new images |
| **Disk Usage** | ~5GB (PDK only) | ~10GB (image + PDK) |
| **Isolation** | Less isolated | Fully isolated |

## Testing Your Setup

### 1. Test LibreLane Installation

```bash
python3 -m librelane --version
```

Expected output:
```
LibreLane 2.4.0
```

### 2. Test PDK Access

```bash
ls $PDK_ROOT
```

Expected output should show PDK files:
```
sky130A/
sky130B/
...
```

### 3. Test a6hub Build

1. Upload a Verilog file to a project
2. Go to Build tab
3. Configure build (use_docker should be unchecked by default)
4. Start build
5. Check logs for "Running LibreLane locally"

### 4. Verify Build Output

Successful build should produce:
- GDSII file (`.gds`)
- Reports (timing, area, power)
- Netlists

## Additional Resources

- **LibreLane GitHub:** https://github.com/librelane/librelane
- **LibreLane PyPI:** https://pypi.org/project/librelane/
- **Sky130 PDK:** https://github.com/google/skywater-pdk
- **GF180MCU PDK:** https://github.com/google/gf180mcu-pdk
- **IHP130 PDK:** https://github.com/IHP-GmbH/IHP-Open-PDK

## Getting Help

If you encounter issues:

1. Check LibreLane version: `python3 -m librelane --version`
2. Check PDK installation: `ls $PDK_ROOT`
3. Review a6hub logs: `docker-compose logs celery-worker`
4. Test LibreLane independently of a6hub
5. Report issues with full error logs

## Migration from Docker

If you were using Docker before:

1. **Update configuration:**
   - Set `use_docker: false` in build configs
   - Or leave default (now false)

2. **Install LibreLane:**
   ```bash
   pip install librelane
   python3 -m librelane --install-pdk sky130
   ```

3. **Update environment:**
   ```bash
   export PDK_ROOT=/root/.ciel
   ```

4. **Restart workers:**
   ```bash
   docker-compose restart celery-worker
   ```

5. **Test builds:**
   - Start a new build
   - Verify logs show "Running LibreLane locally"
   - Check output artifacts

Docker mode is still available as a fallback by setting `use_docker: true` in the build configuration.
