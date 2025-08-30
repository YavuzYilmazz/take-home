from asyncio.log import logger
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import asdict

from .models import JobModel, DatabaseMetadata, DatabaseExport

class InMemoryDB:
    """Simple in-memory database for job storage using JobModel."""
    
    def __init__(self) -> None:
        self.jobs: Dict[str, JobModel] = {}  # jobId -> JobModel

    def save_jobs(self, jobs: List[JobModel]) -> int:
        """
        Upsert jobs by jobId.
        Returns number of new inserts (not updates).
        """
        new_inserts = 0
        
        for job in jobs:
            if not job.jobId:
                continue  # Skip jobs without jobId
                
            # Check if this is a new job (insert) or update
            if job.jobId not in self.jobs:
                new_inserts += 1
                
            # Save/update the job
            self.jobs[job.jobId] = job
            
        return new_inserts

    def get_job(self, job_id: str) -> Optional[JobModel]:
        """Get job by ID."""
        return self.jobs.get(job_id)
        
    def count(self) -> int:
        """Total number of jobs stored."""
        return len(self.jobs)
        
    def clear(self) -> None:
        """Clear all stored jobs."""
        self.jobs.clear()

    def save_to_file(self, filepath: Path) -> None:
        """Save all jobs to a JSON file using structured models."""
        try:
            # Create directory if it doesn't exist
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Create structured export using models
            metadata = DatabaseMetadata(
                total_jobs=len(self.jobs),
                saved_at=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            export_data = DatabaseExport(
                metadata=metadata,
                jobs=list(self.jobs.values())
            )
            
            # Convert to dict for JSON serialization
            data = asdict(export_data)
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Successfully saved {len(self.jobs)} jobs to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving to file {filepath}: {e}")
            raise

    def load_from_file(self, filepath: Path) -> None:
        """Load jobs from a JSON file and convert to JobModel instances."""
        try:
            if not filepath.exists():
                logger.warning(f"File {filepath} does not exist. Starting with empty database.")
                return
                
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Load jobs from file and convert to JobModel instances
            jobs_data = data.get("jobs", [])
            self.clear()  # Clear existing data
            
            for job_dict in jobs_data:
                try:
                    # Create JobModel from dict
                    job = JobModel(**job_dict)
                    if job.jobId:
                        self.jobs[job.jobId] = job
                except Exception as e:
                    logger.warning(f"Failed to load job {job_dict.get('jobId', 'unknown')}: {e}")
                    continue

            logger.info(f"Successfully loaded {len(self.jobs)} jobs from {filepath}")

        except Exception as e:
            logger.error(f"Error loading from file {filepath}: {e}")
            raise

    def get_all_jobs(self) -> List[JobModel]:
        """Get all jobs as a list of JobModel instances."""
        return list(self.jobs.values())
        
    def get_total_applicants(self) -> int:
        """Calculate total number of applicants across all jobs."""
        total = 0
        for job in self.jobs.values():
            if isinstance(job.applicants, (int, float)):
                total += job.applicants
        return total