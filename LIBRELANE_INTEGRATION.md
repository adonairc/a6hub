# LibreLane ASIC Flow Integration

This document describes the LibreLane integration added to a6hub for orchestrating ASIC design flows.

## Overview

The LibreLane integration enables users to:
- Configure ASIC build flows with a user-friendly interface
- Run complete RTL-to-GDSII flows using LibreLane in Docker (or Python library as alternative)
- Track build progress and view results
- Use pre-configured flow presets for common scenarios

**Note:** a6hub uses LibreLane in Docker by default for consistent, reproducible builds. Python library mode is available as an alternative. See `backend/LIBRELANE_PYTHON_SETUP.md` for Python installation.

## Architecture

### Backend Components

#### 1. Flow Configuration Schema (`app/schemas/librelane.py`)

Defines the complete LibreLane flow configuration with Pydantic models:

**Key Classes:**
- `LibreLaneFlowConfig`: Main configuration schema with 30+ parameters
- `PDKType`: Enum for supported Process Design Kits (Sky130, GF180MCU)
- `FlowType`: Classic vs Custom flows
- `LibreLaneBuildRequest`: Request schema for starting builds
- `LibreLaneBuildStatus`: Status response for build tracking

**Presets:**
- `minimal`: Fast flow for quick testing (DRC/LVS disabled)
- `balanced`: Balance between speed and quality
- `high_quality`: Maximum quality for tape-out ready designs

#### 2. Build Worker (`app/workers/tasks.py`)

Enhanced `run_build` task that:
- Creates proper directory structure (design/, runs/)
- Writes all project files to the design directory
- Generates LibreLane config.json from flow configuration
- Executes LibreLane in Docker container with volume mounts
- Captures comprehensive logs with step tracking
- Identifies and reports generated artifacts (GDSII, reports)
- Handles timeouts and errors gracefully

**Docker Command:**
```bash
docker run --rm \
  -v /work:/work \
  -w /work \
  efabless/openlane:latest \
  --dockerized \
  --pdk-root=/root/.ciel \
  /work/config.json
```

**Note:** The default Docker image is `efabless/openlane:latest` (OpenLane v1). For other options, see `backend/OPENLANE_DOCKER_SETUP.md`.

#### 3. Build API Endpoints (`app/api/v1/builds.py`)

New API routes under `/api/v1/builds/`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/presets` | GET | Get available flow presets |
| `/pdks` | GET | List supported PDKs |
| `/{project_id}/build` | POST | Start a build job |
| `/{project_id}/build/config` | GET | Get last used config |
| `/{project_id}/build/config` | PUT | Save/validate config |
| `/{project_id}/build/status` | GET | Get latest build status |

### Frontend Components

#### 1. Build Page (`app/projects/[id]/build/page.tsx`)

Comprehensive build configuration interface with:

**Features:**
- Quick start presets (minimal, balanced, high_quality)
- Tabbed interface (Basic Settings / Advanced Settings)
- Real-time build status tracking
- Interactive configuration controls
- Visual parameter sliders for density and utilization
- Clock frequency calculator
- Status badges with icons

**Basic Settings:**
- Design name
- PDK selection
- Clock configuration (period, port name)
- Placement density slider
- Core utilization slider
- DRC/LVS verification toggles

**Advanced Settings:**
- Synthesis strategy
- Max fanout
- Aspect ratio
- Docker image selection
- Docker enable/disable toggle

#### 2. API Client (`lib/api.ts`)

New `buildsAPI` with methods:
```typescript
buildsAPI.getPresets()
buildsAPI.getPDKs()
buildsAPI.getConfig(projectId)
buildsAPI.saveConfig(projectId, config)
buildsAPI.startBuild(projectId, { config })
buildsAPI.getStatus(projectId)
```

#### 3. Project Navigation

Updated project page tabs to include functional "Build" link that navigates to the build configuration page.

## Flow Configuration Parameters

### Core Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `design_name` | string | (required) | Top module name |
| `verilog_files` | list | [] | List of Verilog source files (auto-detected if empty) |
| `pdk` | enum | sky130_fd_sc_hd | Process Design Kit |
| `clock_period` | string | "10" | Clock period in nanoseconds |
| `clock_port` | string | "clk" | Clock port name |

### Placement & Routing

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pl_target_density` | string | "0.5" | Placement density (0.0-1.0) |
| `fp_core_util` | int | 50 | Core utilization percentage |
| `fp_aspect_ratio` | float | 1.0 | Die aspect ratio |

### Synthesis

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `synth_strategy` | string | "AREA 0" | Synthesis optimization strategy |
| `synth_max_fanout` | int | 10 | Maximum fanout constraint |
| `synth_buffering` | bool | true | Enable buffering |
| `synth_sizing` | bool | true | Enable gate sizing |

### Verification

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `run_drc` | bool | true | Run Design Rule Check |
| `run_lvs` | bool | true | Run Layout vs Schematic |
| `run_magic_drc` | bool | true | Run Magic DRC |
| `run_klayout_drc` | bool | false | Run KLayout DRC |

### Docker

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `use_docker` | bool | true | Run in Docker container |
| `docker_image` | string | efabless/openlane:latest | Docker image to use (see OPENLANE_DOCKER_SETUP.md for alternatives) |

## Usage Example

### 1. Navigate to Build Page

From any project, click the "Build" tab to access the build configuration page.

### 2. Configure Flow

**Option A: Use a Preset**
1. Click on a preset card (Minimal, Balanced, or High Quality)
2. Configuration is automatically applied

**Option B: Manual Configuration**
1. Set design name (defaults to project name)
2. Select PDK (Sky130 HD, HS, MS, LS, or GF180MCU)
3. Configure clock (period in ns, port name)
4. Adjust placement density slider
5. Set core utilization
6. Enable/disable verification options

### 3. Start Build

1. Click "Start Build" button
2. Job is created and queued to Celery worker
3. Status card appears showing job progress
4. Click "View Job Details" to see full logs

### 4. Monitor Progress

The build status card shows:
- Current status (Pending, Running, Completed, Failed)
- Job ID for reference
- Current step (extracted from logs)
- Link to detailed job page

## LibreLane Config.json Generation

The worker automatically generates a config.json file:

```json
{
  "DESIGN_NAME": "my_chip",
  "VERILOG_FILES": [
    "dir::design/counter.v",
    "dir::design/top.v"
  ],
  "CLOCK_PERIOD": "10",
  "CLOCK_PORT": "clk",
  "PDK": "sky130_fd_sc_hd",
  "STD_CELL_LIBRARY": "sky130_fd_sc_hd",
  "FP_CORE_UTIL": 50,
  "FP_ASPECT_RATIO": 1.0,
  "PL_TARGET_DENSITY": 0.5,
  "PL_RANDOM_SEED": 42,
  "SYNTH_STRATEGY": "AREA 0",
  "SYNTH_MAX_FANOUT": 10,
  "GRT_REPAIR_ANTENNAS": true,
  "DRT_OPT_ITERS": 64,
  "RUN_DRC": true,
  "RUN_LVS": true
}
```

## Output Artifacts

LibreLane generates the following in `runs/RUN_<timestamp>/`:

- **GDSII Files**: Final layout (`.gds`)
- **Reports**: Timing, area, power analysis
- **Logs**: Step-by-step execution logs
- **Netlists**: Post-synthesis/PnR netlists
- **LEF/DEF**: Physical design data

## File Auto-Detection

When `verilog_files` is not specified or is empty, the system automatically detects all Verilog-related files in the project:
- `.v` - Verilog files
- `.sv` - SystemVerilog files
- `.vh` - Verilog header files

All detected files are included in the build by default, ensuring no source files are accidentally omitted.

## Error Handling

The system handles:
- **Timeout**: Builds exceeding `WORKER_TIMEOUT` (3600s default)
- **Missing files**: Validates project has files and detects Verilog sources automatically
- **Docker errors**: Captures stderr and exit codes
- **Permission errors**: Checks project ownership

## Future Enhancements

Potential improvements:
- [ ] Real-time log streaming via WebSockets
- [ ] Artifact download from MinIO
- [ ] GDSII viewer integration
- [ ] Timing report visualization
- [ ] Multi-corner analysis support
- [ ] Custom flow scripting
- [ ] Build comparison tools
- [ ] Resource usage tracking

## Testing

To test the integration:

1. **Start the backend services:**
   ```bash
   cd backend
   docker-compose up -d
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Create a test project:**
   - Login to a6hub
   - Create a new project
   - Upload a simple Verilog file (e.g., counter.v)

4. **Configure and run build:**
   - Navigate to Build tab
   - Select "Minimal Flow" preset
   - Click "Start Build"
   - Monitor status

## Dependencies

**Backend:**
- `pydantic` 2.1.0+: Schema validation
- `celery` 5.3.4+: Task queue
- `docker`: Container execution (system dependency)

**Frontend:**
- `react` 18.3.1+: UI framework
- `next` 15.0.2+: React framework
- `axios` 1.6.2+: HTTP client
- `lucide-react` 0.294.0+: Icons

## API Documentation

Full API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Navigate to the "builds" tag to see all LibreLane-related endpoints.

## Configuration Reference

See `app/schemas/librelane.py` for the complete list of all 30+ configurable parameters and their descriptions.
