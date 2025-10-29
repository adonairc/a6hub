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
        
        # Write project files to work directory
        for file in project.files:
            file_path = work_dir / file.filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if file.content:
                file_path.write_text(file.content)
        
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

        logs.append(f"Configuration:\n")
        logs.append(f"  Design: {design_name}\n")
        logs.append(f"  PDK: {pdk}\n")
        logs.append(f"  Docker: {use_docker}\n")
        logs.append(f"  Image: {docker_image}\n\n")

        # Write project files to design directory
        logs.append("Writing design files...\n")
        written_files = []
        for file in project.files:
            file_path = design_dir / file.filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if file.content:
                file_path.write_text(file.content)
                written_files.append(file.filepath)
                logs.append(f"  - {file.filepath}\n")

        if not written_files:
            raise Exception("No Verilog files found in project")

        # If no verilog_files specified, use all .v files
        if not verilog_files:
            verilog_files = [f for f in written_files if f.endswith('.v')]

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

        logs.append("Generated LibreLane config.json\n\n")
        logs.append("=== Starting ASIC Flow ===\n\n")

        # Run LibreLane
        if use_docker:
            # Run LibreLane in Docker container
            logs.append(f"Running LibreLane in Docker container: {docker_image}\n\n")

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

            logs.append(f"Command: {' '.join(cmd)}\n\n")

            # Execute LibreLane flow
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.WORKER_TIMEOUT
            )

            logs.append("=== LibreLane Output ===\n")
            logs.append(result.stdout)

            if result.stderr:
                logs.append("\n=== Warnings/Errors ===\n")
                logs.append(result.stderr)

            if result.returncode != 0:
                raise Exception(f"LibreLane failed with exit code {result.returncode}")

        else:
            # Run LibreLane locally (requires LibreLane installation)
            logs.append("Running LibreLane locally\n\n")

            cmd = [
                "python3", "-m", "librelane",
                f"--pdk-root={settings.PDK_ROOT}",
                str(config_file)
            ]

            logs.append(f"Command: {' '.join(cmd)}\n\n")

            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=settings.WORKER_TIMEOUT
            )

            logs.append("=== LibreLane Output ===\n")
            logs.append(result.stdout)

            if result.stderr:
                logs.append("\n=== Warnings/Errors ===\n")
                logs.append(result.stderr)

            if result.returncode != 0:
                raise Exception(f"LibreLane failed with exit code {result.returncode}")

        # Check for output artifacts
        logs.append("\n\n=== Build Complete ===\n")
        logs.append("Checking for output artifacts...\n")

        # Find the run directory (LibreLane creates runs/RUN_<timestamp>)
        run_dirs = list(runs_dir.glob("RUN_*"))
        if run_dirs:
            latest_run = max(run_dirs, key=lambda p: p.stat().st_mtime)
            logs.append(f"Latest run: {latest_run.name}\n")

            # Check for GDSII
            gds_files = list(latest_run.rglob("*.gds"))
            if gds_files:
                logs.append(f"Generated GDSII files:\n")
                for gds in gds_files:
                    logs.append(f"  - {gds.relative_to(work_dir)}\n")

            # Check for reports
            reports_dir = latest_run / "reports"
            if reports_dir.exists():
                logs.append(f"\nGenerated reports:\n")
                for report in reports_dir.rglob("*"):
                    if report.is_file():
                        logs.append(f"  - {report.relative_to(work_dir)}\n")

        # TODO: Upload artifacts to MinIO
        artifacts_path = f"jobs/{job_id}/artifacts"

        logs.append(f"\nArtifacts will be stored at: {artifacts_path}\n")

        # Update job with success
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.logs = "\n".join(logs)
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
        logs.append(f"\n\nERROR: {error_msg}\n")

        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.error_message = error_msg
        job.logs = "\n".join(logs)
        self.db.commit()

        return {
            "status": "error",
            "job_id": job_id,
            "message": error_msg
        }

    except Exception as e:
        logger.error(f"Build job {job_id} failed: {str(e)}")
        logs.append(f"\n\nERROR: {str(e)}\n")

        # Update job with failure
        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.error_message = str(e)
        job.logs = "\n".join(logs)
        self.db.commit()

        return {
            "status": "error",
            "job_id": job_id,
            "message": str(e)
        }
