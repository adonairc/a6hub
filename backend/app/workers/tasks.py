"""
Celery tasks for executing simulation and build jobs
"""
from celery import Task
from datetime import datetime
import subprocess
import logging
from pathlib import Path

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.job import Job, JobStatus
from app.core.config import settings
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session"""
    
    def __call__(self, *args, **kwargs):
        with SessionLocal() as db:
            self.db = db
            return super().__call__(*args, **kwargs)


@celery_app.task(bind=True, base=DatabaseTask)
def run_simulation(self, job_id: int):
    """
    Execute Verilog simulation task
    
    Args:
        job_id: Database ID of the job to execute
    
    Returns:
        dict: Job results including status and artifacts path
    """
    logger.info(f"Starting simulation job {job_id}")
    
    # Get job from database
    job = self.db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.error(f"Job {job_id} not found")
        return {"status": "error", "message": "Job not found"}
    
    try:
        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.celery_task_id = self.request.id
        self.db.commit()
        
        # Get project files
        project = job.project
        config = job.config or {}
        
        # Create temporary work directory
        work_dir = Path(settings.STORAGE_BASE_PATH) / f"job_{job_id}"
        work_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy project files to work directory from MinIO or database
        for file in project.files:
            file_path = work_dir / file.filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                # Check if file is stored in MinIO
                if file.use_minio and file.minio_bucket and file.minio_key:
                    # Download from MinIO
                    file_content = storage_service.download_file(file.minio_bucket, file.minio_key)
                    file_path.write_bytes(file_content)
                    logger.info(f"Copied {file.filepath} from MinIO: {file.minio_key}")
                elif file.content:
                    # Fall back to legacy content field
                    file_path.write_text(file.content)
                    logger.info(f"Copied {file.filepath} from database")
                else:
                    logger.warning(f"Skipping {file.filepath} - no content available")
                    continue
            except Exception as e:
                logger.error(f"Failed to copy file {file.filepath}: {str(e)}")
                raise Exception(f"Failed to copy file {file.filepath}: {str(e)}")
        
        # Determine simulator (Verilator or Icarus)
        simulator = config.get("simulator", "verilator")
        testbench = config.get("testbench", "testbench.v")
        
        logs = []
        
        if simulator == "verilator":
            # Run Verilator simulation
            cmd = [
                settings.VERILATOR_PATH,
                "--cc",
                "--exe",
                "--build",
                str(work_dir / testbench),
            ]
            
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=settings.WORKER_TIMEOUT
            )
            
            logs.append(f"Command: {' '.join(cmd)}\n")
            logs.append(f"STDOUT:\n{result.stdout}\n")
            logs.append(f"STDERR:\n{result.stderr}\n")
            
            if result.returncode != 0:
                raise Exception(f"Verilator failed with code {result.returncode}")
        
        else:  # Icarus Verilog
            # Compile with iverilog
            cmd = [
                settings.ICARUS_PATH,
                "-o",
                str(work_dir / "sim.vvp"),
                str(work_dir / testbench),
            ]
            
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=settings.WORKER_TIMEOUT
            )
            
            logs.append(f"Command: {' '.join(cmd)}\n")
            logs.append(f"STDOUT:\n{result.stdout}\n")
            logs.append(f"STDERR:\n{result.stderr}\n")
            
            if result.returncode != 0:
                raise Exception(f"iverilog failed with code {result.returncode}")
            
            # Run simulation
            cmd = ["vvp", str(work_dir / "sim.vvp")]
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=settings.WORKER_TIMEOUT
            )
            
            logs.append(f"Command: {' '.join(cmd)}\n")
            logs.append(f"STDOUT:\n{result.stdout}\n")
            logs.append(f"STDERR:\n{result.stderr}\n")
        
        # TODO: Upload artifacts to MinIO
        artifacts_path = f"jobs/{job_id}/artifacts"
        
        # Update job with success
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.logs = "\n".join(logs)
        job.artifacts_path = artifacts_path
        self.db.commit()
        
        logger.info(f"Simulation job {job_id} completed successfully")
        
        return {
            "status": "success",
            "job_id": job_id,
            "artifacts_path": artifacts_path
        }
    
    except Exception as e:
        logger.error(f"Simulation job {job_id} failed: {str(e)}")
        
        # Update job with failure
        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.error_message = str(e)
        job.logs = "\n".join(logs) if logs else ""
        self.db.commit()
        
        return {
            "status": "error",
            "job_id": job_id,
            "message": str(e)
        }


def update_build_progress(db, job, step_name, progress_percent=None, completed_steps=None):
    """
    Update job progress in database

    Args:
        db: Database session
        job: Job model instance
        step_name: Current step name
        progress_percent: Optional overall progress percentage
        completed_steps: Optional list of completed step names
    """
    job.current_step = step_name

    progress_data = job.progress_data or {}
    progress_data["current_step"] = step_name

    if progress_percent is not None:
        progress_data["progress_percent"] = progress_percent

    if completed_steps is not None:
        progress_data["completed_steps"] = completed_steps

    progress_data["steps_info"] = LIBRELANE_STEPS

    job.progress_data = progress_data
    db.commit()
    logger.info(f"Job {job.id}: {step_name} ({progress_percent}%)")


def append_job_logs(db, job, new_logs):
    """Append logs to job and commit"""
    if job.logs:
        job.logs += new_logs
    else:
        job.logs = new_logs
    db.commit()


# LibreLane build flow steps
LIBRELANE_STEPS = [
    {"name": "initialization", "label": "Initialization", "description": "Setting up build environment"},
    {"name": "synthesis", "label": "Synthesis", "description": "Converting RTL to gate-level netlist"},
    {"name": "floorplan", "label": "Floorplan", "description": "Planning chip layout"},
    {"name": "placement", "label": "Placement", "description": "Placing standard cells"},
    {"name": "cts", "label": "Clock Tree Synthesis", "description": "Building clock distribution network"},
    {"name": "routing", "label": "Routing", "description": "Routing signal connections"},
    {"name": "gdsii", "label": "GDSII Generation", "description": "Generating final layout"},
    {"name": "drc", "label": "DRC", "description": "Design Rule Check"},
    {"name": "lvs", "label": "LVS", "description": "Layout vs Schematic verification"},
    {"name": "completion", "label": "Completion", "description": "Finalizing build artifacts"},
]


def detect_librelane_step(log_line):
    """
    Detect LibreLane step from log output

    Returns: (step_name, step_label) or (None, None)
    """
    log_lower = log_line.lower()

    step_patterns = {
        "initialization": ["starting librelane", "initializing", "setup"],
        "synthesis": ["running synthesis", "yosys", "synthesizing"],
        "floorplan": ["floorplanning", "floor plan", "init_fp"],
        "placement": ["placement", "global placement", "detailed placement"],
        "cts": ["clock tree synthesis", "cts", "tritoncts"],
        "routing": ["routing", "global routing", "detailed routing", "fastroute"],
        "gdsii": ["generating gds", "gdsii", "magic", "final layout"],
        "drc": ["design rule check", "drc", "magic drc"],
        "lvs": ["layout vs schematic", "lvs", "netgen"],
        "completion": ["build complete", "finishing", "success"],
    }

    for step_name, patterns in step_patterns.items():
        for pattern in patterns:
            if pattern in log_lower:
                step_info = next((s for s in LIBRELANE_STEPS if s["name"] == step_name), None)
                if step_info:
                    return (step_name, step_info["label"])

    return (None, None)


@celery_app.task(bind=True, base=DatabaseTask)
def run_build(self, job_id: int):
    """
    Execute LibreLane RTL-to-GDSII build task in Docker container

    Args:
        job_id: Database ID of the job to execute

    Returns:
        dict: Job results including status and artifacts path
    """
    logger.info(f"Starting LibreLane build job {job_id}")

    # Get job from database
    job = self.db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.error(f"Job {job_id} not found")
        return {"status": "error", "message": "Job not found"}

    logs = []
    completed_steps = []
    current_step_name = "initialization"

    try:
        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.celery_task_id = self.request.id
        self.db.commit()

        # Get project files
        project = job.project
        config = job.config or {}

        # Create work directory structure
        work_dir = Path(settings.STORAGE_BASE_PATH) / f"job_{job_id}"
        work_dir.mkdir(parents=True, exist_ok=True)

        design_dir = work_dir / "design"
        design_dir.mkdir(exist_ok=True)

        runs_dir = work_dir / "runs"
        runs_dir.mkdir(exist_ok=True)

        logs.append(f"=== LibreLane ASIC Build Flow ===\n")
        logs.append(f"Job ID: {job_id}\n")
        logs.append(f"Project: {project.name}\n")
        logs.append(f"Work directory: {work_dir}\n\n")

        # Extract LibreLane configuration
        design_name = config.get("design_name", project.name)
        pdk = config.get("pdk", "sky130_fd_sc_hd")
        verilog_files = config.get("verilog_files", [])
        use_docker = config.get("use_docker", True)
        docker_image = config.get("docker_image", "ghcr.io/librelane/librelane:latest")

        config_log = f"Configuration:\n"
        config_log += f"  Design: {design_name}\n"
        config_log += f"  PDK: {pdk}\n"
        config_log += f"  Docker: {use_docker}\n"
        config_log += f"  Image: {docker_image}\n\n"
        logs.append(config_log)
        append_job_logs(self.db, job, config_log)

        # Write project files to design directory
        logs.append("Copying project files from storage...\n")
        written_files = []
        for file in project.files:
            file_path = design_dir / file.filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                # Check if file is stored in MinIO
                if file.use_minio and file.minio_bucket and file.minio_key:
                    # Download from MinIO
                    file_content = storage_service.download_file(file.minio_bucket, file.minio_key)
                    file_path.write_bytes(file_content)
                    logs.append(f"  - {file.filepath} (from MinIO: {file.minio_key})\n")
                elif file.content:
                    # Fall back to legacy content field
                    file_path.write_text(file.content)
                    logs.append(f"  - {file.filepath} (from database)\n")
                else:
                    logs.append(f"  ! Skipping {file.filepath} (no content available)\n")
                    continue

                written_files.append(file.filepath)

            except Exception as e:
                error_msg = f"Failed to copy file {file.filepath}: {str(e)}"
                logs.append(f"  ! {error_msg}\n")
                logger.error(error_msg)

        if not written_files:
            raise Exception("No files found in project. Please upload design files before starting a build.")

        # If no verilog_files specified, auto-detect all Verilog/SystemVerilog files
        if not verilog_files:
            verilog_extensions = ('.v', '.sv', '.vh')
            verilog_files = [f for f in written_files if f.endswith(verilog_extensions)]
            if not verilog_files:
                raise Exception(f"No Verilog files found in project. Expected files with extensions: {', '.join(verilog_extensions)}")
            logs.append(f"Auto-detected Verilog files: {', '.join(verilog_files)}\n")

        logs.append(f"\nVerilog files for synthesis: {', '.join(verilog_files)}\n\n")

        # Create LibreLane config.json
        librelane_config = {
            "DESIGN_NAME": design_name,
            "VERILOG_FILES": [f"dir::design/{vf}" for vf in verilog_files],
            "CLOCK_PERIOD": config.get("clock_period", "10"),
            "CLOCK_PORT": config.get("clock_port", "clk"),
            "PDK": pdk,
            "STD_CELL_LIBRARY": config.get("std_cell_library", pdk),
            "FP_CORE_UTIL": config.get("fp_core_util", 50),
            "FP_ASPECT_RATIO": config.get("fp_aspect_ratio", 1.0),
            "PL_TARGET_DENSITY": float(config.get("pl_target_density", "0.5")),
            "PL_RANDOM_SEED": config.get("pl_random_seed", 42),
            "SYNTH_STRATEGY": config.get("synth_strategy", "AREA 0"),
            "SYNTH_MAX_FANOUT": config.get("synth_max_fanout", 10),
            "GRT_REPAIR_ANTENNAS": config.get("grt_repair_antennas", True),
            "DRT_OPT_ITERS": config.get("drt_opt_iters", 64),
            "RUN_DRC": config.get("run_drc", True),
            "RUN_LVS": config.get("run_lvs", True),
        }

        # Add optional configurations
        if "die_area" in config:
            librelane_config["DIE_AREA"] = config["die_area"]
        if "core_area" in config:
            librelane_config["CORE_AREA"] = config["core_area"]

        # Add extra args if provided
        if "extra_args" in config:
            librelane_config.update(config["extra_args"])

        # Write config.json
        import json
        config_file = work_dir / "config.json"
        config_file.write_text(json.dumps(librelane_config, indent=2))

        init_log = "Generated LibreLane config.json\n\n=== Starting ASIC Flow ===\n\n"
        logs.append(init_log)
        append_job_logs(self.db, job, init_log)

        # Initialize progress tracking
        update_build_progress(self.db, job, "initialization", 0, completed_steps)

        # Run LibreLane
        if use_docker:
            # Run LibreLane in Docker container
            start_log = f"Running LibreLane in Docker container: {docker_image}\n\n"
            logs.append(start_log)
            append_job_logs(self.db, job, start_log)

            # Docker command to run LibreLane
            cmd = [
                "docker", "run",
                "--rm",
                "-v", f"{work_dir}:/work",
                "-w", "/work",
                docker_image,
                "--dockerized",
                f"--pdk-root=/root/.ciel",
                "/work/config.json"
            ]

            cmd_log = f"Command: {' '.join(cmd)}\n\n=== LibreLane Output ===\n"
            logs.append(cmd_log)
            append_job_logs(self.db, job, cmd_log)

            # Execute LibreLane flow with real-time output processing
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Process output line by line
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break

                output_lines.append(line)
                logs.append(line)

                # Append logs every 10 lines or when step changes
                if len(output_lines) >= 10:
                    append_job_logs(self.db, job, ''.join(output_lines))
                    output_lines = []

                # Detect step changes
                detected_step, step_label = detect_librelane_step(line)
                if detected_step and detected_step != current_step_name:
                    # Mark previous step as complete
                    if current_step_name not in completed_steps:
                        completed_steps.append(current_step_name)

                    # Update to new step
                    current_step_name = detected_step
                    progress_percent = int((len(completed_steps) / len(LIBRELANE_STEPS)) * 100)
                    update_build_progress(self.db, job, current_step_name, progress_percent, completed_steps)

                    step_change_log = f"\n>>> Step Changed: {step_label} <<<\n"
                    append_job_logs(self.db, job, step_change_log)

            # Append any remaining logs
            if output_lines:
                append_job_logs(self.db, job, ''.join(output_lines))

            # Wait for process to complete
            returncode = process.wait(timeout=settings.WORKER_TIMEOUT)

            if returncode != 0:
                raise Exception(f"LibreLane failed with exit code {returncode}")

        else:
            # Run LibreLane locally (requires LibreLane installation)
            start_log = "Running LibreLane locally\n\n"
            logs.append(start_log)
            append_job_logs(self.db, job, start_log)

            cmd = [
                "python3", "-m", "librelane",
                f"--pdk-root={settings.PDK_ROOT}",
                str(config_file)
            ]

            cmd_log = f"Command: {' '.join(cmd)}\n\n=== LibreLane Output ===\n"
            logs.append(cmd_log)
            append_job_logs(self.db, job, cmd_log)

            # Execute LibreLane flow with real-time output processing
            process = subprocess.Popen(
                cmd,
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Process output line by line
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break

                output_lines.append(line)
                logs.append(line)

                # Append logs every 10 lines or when step changes
                if len(output_lines) >= 10:
                    append_job_logs(self.db, job, ''.join(output_lines))
                    output_lines = []

                # Detect step changes
                detected_step, step_label = detect_librelane_step(line)
                if detected_step and detected_step != current_step_name:
                    # Mark previous step as complete
                    if current_step_name not in completed_steps:
                        completed_steps.append(current_step_name)

                    # Update to new step
                    current_step_name = detected_step
                    progress_percent = int((len(completed_steps) / len(LIBRELANE_STEPS)) * 100)
                    update_build_progress(self.db, job, current_step_name, progress_percent, completed_steps)

                    step_change_log = f"\n>>> Step Changed: {step_label} <<<\n"
                    append_job_logs(self.db, job, step_change_log)

            # Append any remaining logs
            if output_lines:
                append_job_logs(self.db, job, ''.join(output_lines))

            # Wait for process to complete
            returncode = process.wait(timeout=settings.WORKER_TIMEOUT)

            if returncode != 0:
                raise Exception(f"LibreLane failed with exit code {returncode}")

        # Check for output artifacts
        completion_log = "\n\n=== Build Complete ===\n"
        completion_log += "Checking for output artifacts...\n"
        logs.append(completion_log)
        append_job_logs(self.db, job, completion_log)

        # Mark all steps as complete
        if current_step_name not in completed_steps:
            completed_steps.append(current_step_name)
        update_build_progress(self.db, job, "completion", 100, completed_steps)

        # Find the run directory (LibreLane creates runs/RUN_<timestamp>)
        run_dirs = list(runs_dir.glob("RUN_*"))
        artifacts_log = ""
        if run_dirs:
            latest_run = max(run_dirs, key=lambda p: p.stat().st_mtime)
            artifacts_log += f"Latest run: {latest_run.name}\n"

            # Check for GDSII
            gds_files = list(latest_run.rglob("*.gds"))
            if gds_files:
                artifacts_log += f"Generated GDSII files:\n"
                for gds in gds_files:
                    artifacts_log += f"  - {gds.relative_to(work_dir)}\n"

            # Check for reports
            reports_dir = latest_run / "reports"
            if reports_dir.exists():
                artifacts_log += f"\nGenerated reports:\n"
                for report in reports_dir.rglob("*"):
                    if report.is_file():
                        artifacts_log += f"  - {report.relative_to(work_dir)}\n"

        # TODO: Upload artifacts to MinIO
        artifacts_path = f"jobs/{job_id}/artifacts"
        artifacts_log += f"\nArtifacts will be stored at: {artifacts_path}\n"

        logs.append(artifacts_log)
        append_job_logs(self.db, job, artifacts_log)

        # Update job with success
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.artifacts_path = artifacts_path
        self.db.commit()

        logger.info(f"Build job {job_id} completed successfully")

        return {
            "status": "success",
            "job_id": job_id,
            "artifacts_path": artifacts_path
        }

    except subprocess.TimeoutExpired:
        error_msg = f"Build timed out after {settings.WORKER_TIMEOUT} seconds"
        logger.error(f"Build job {job_id} timed out")
        error_log = f"\n\nERROR: {error_msg}\n"
        append_job_logs(self.db, job, error_log)

        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.error_message = error_msg
        self.db.commit()

        return {
            "status": "error",
            "job_id": job_id,
            "message": error_msg
        }

    except Exception as e:
        logger.error(f"Build job {job_id} failed: {str(e)}")
        error_log = f"\n\nERROR: {str(e)}\n"
        append_job_logs(self.db, job, error_log)

        # Update job with failure
        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.error_message = str(e)
        self.db.commit()

        return {
            "status": "error",
            "job_id": job_id,
            "message": str(e)
        }
