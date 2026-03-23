import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class JobScheduler:
    def __init__(self):
        self.jobs = {}
        self.running = False
    
    async def start(self):
        self.running = True
        logger.info("Job scheduler started")
        
        while self.running:
            try:
                await self._run_pending_jobs()
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Job scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def stop(self):
        self.running = False
        logger.info("Job scheduler stopped")
    
    async def _run_pending_jobs(self):
        now = datetime.utcnow()
        
        for job_name, job in self.jobs.items():
            if job.get("enabled", True):
                last_run = job.get("last_run")
                interval = job.get("interval_minutes", 60)
                
                if last_run is None or (now - last_run).total_seconds() >= interval * 60:
                    logger.info(f"Running job: {job_name}")
                    try:
                        await job["func"]()
                        job["last_run"] = now
                        job["last_status"] = "success"
                    except Exception as e:
                        logger.error(f"Job {job_name} failed: {e}")
                        job["last_status"] = "failed"
                        job["last_error"] = str(e)
    
    def register_job(self, name: str, func, interval_minutes: int = 60, enabled: bool = True):
        self.jobs[name] = {
            "func": func,
            "interval_minutes": interval_minutes,
            "enabled": enabled,
            "last_run": None,
            "last_status": None,
            "last_error": None,
        }
        logger.info(f"Registered job: {name} (interval: {interval_minutes}min)")
    
    def get_job_status(self, name: str) -> Optional[dict]:
        if name in self.jobs:
            job = self.jobs[name]
            return {
                "name": name,
                "enabled": job["enabled"],
                "last_run": job["last_run"].isoformat() if job["last_run"] else None,
                "last_status": job["last_status"],
                "last_error": job["last_error"],
                "interval_minutes": job["interval_minutes"],
            }
        return None
    
    def list_jobs(self) -> list:
        return [self.get_job_status(name) for name in self.jobs.keys()]


scheduler = JobScheduler()
