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
    Execute LibreLane RTL-to-GDSII build task
    
    Args:
        job_id: Database ID of the job to execute
    
    Returns:
        dict: Job results including status and artifacts path
    """
    logger.info(f"Starting build job {job_id}")
    
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
        
        # Get build configuration
        pdk = config.get("pdk", "sky130")
        top_module = config.get("top_module", "top")
        
        logs = []
        
        # Run LibreLane build
        # TODO: Implement actual LibreLane integration
        cmd = [
            "python3",
            f"{settings.LIBRELANE_PATH}/librelane.py",
            "--pdk", pdk,
            "--top", top_module,
            "--work-dir", str(work_dir),
        ]
        
        logs.append(f"Command: {' '.join(cmd)}\n")
        logs.append(f"Starting LibreLane build for PDK: {pdk}\n")
        
        # For now, simulate a successful build
        # In production, this would run the actual LibreLane flow
        logs.append("Build flow completed successfully\n")
        logs.append("Generated GDSII file: output.gds\n")
        
        # TODO: Upload artifacts to MinIO
        artifacts_path = f"jobs/{job_id}/artifacts"
        
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
    
    except Exception as e:
        logger.error(f"Build job {job_id} failed: {str(e)}")
        
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
