import json
import time
from pathlib import Path
from typing import List, Dict, Optional

class InMemoryDB:
    """Simple in-memory database for job storage."""
    
    def __init__(self) -> None:
        self.jobs: Dict[str, Dict] = {}  # jobId -> job data

    def save_jobs(self, jobs: List[Dict]) -> int:
        """
        Upsert jobs by jobId.
        Returns number of new inserts (not updates).
        """
        new_inserts = 0
        
        for job in jobs:
            job_id = job.get('jobId')
            if not job_id:
                continue  # Skip jobs without jobId
                
            # Check if this is a new job (insert) or update
            if job_id not in self.jobs:
                new_inserts += 1
                
            # Save/update the job
            self.jobs[job_id] = job.copy()
            
        return new_inserts

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID."""
        return self.jobs.get(job_id)
        
    def count(self) -> int:
        """Total number of jobs stored."""
        return len(self.jobs)
        
    def clear(self) -> None:
        """Clear all stored jobs."""
        self.jobs.clear()

    def save_to_file(self, filepath: Path) -> None:
        """Save all jobs to a JSON file."""
        try:
            # Create directory if it doesn't exist
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for saving
            data = {
                "metadata": {
                    "total_jobs": len(self.jobs),
                    "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                "jobs": list(self.jobs.values())
            }
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            print(f"Successfully saved {len(self.jobs)} jobs to {filepath}")
            
        except Exception as e:
            print(f"Error saving to file {filepath}: {e}")
            raise

    def load_from_file(self, filepath: Path) -> None:
        """Load jobs from a JSON file."""
        try:
            if not filepath.exists():
                print(f"File {filepath} does not exist. Starting with empty database.")
                return
                
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Load jobs from file
            jobs = data.get("jobs", [])
            self.clear()  # Clear existing data
            
            for job in jobs:
                job_id = job.get('jobId')
                if job_id:
                    self.jobs[job_id] = job
                    
            print(f"Successfully loaded {len(self.jobs)} jobs from {filepath}")
            
        except Exception as e:
            print(f"Error loading from file {filepath}: {e}")
            raise

    def get_all_jobs(self) -> List[Dict]:
        """Get all jobs as a list."""
        return list(self.jobs.values())
        
    def get_total_applicants(self) -> int:
        """Calculate total number of applicants across all jobs."""
        total = 0
        for job in self.jobs.values():
            applicants = job.get('applicants', 0)
            if isinstance(applicants, (int, float)):
                total += applicants
        return total