from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class JobModel:
    """Data model for job postings"""
    
    jobId: str
    title: str
    company: str
    location: str = "Unknown"
    workType: str = "Unknown"
    postedDate: str = "Unknown"
    applicants: int = 0
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization"""
        # Validate work type
        valid_work_types = ["Remote", "On-site", "Hybrid", "Unknown"]
        if self.workType not in valid_work_types:
            self.workType = "Unknown"
        
        # Validate applicants count
        if not isinstance(self.applicants, int) or self.applicants < 0:
            self.applicants = 0
        
        # Validate posted date format
        if self.postedDate != "Unknown":
            try:
                datetime.strptime(self.postedDate, "%Y-%m-%d")
            except ValueError:
                self.postedDate = "Unknown"


@dataclass
class CompanyResponse:
    """Model for companies API response"""
    companies: List[str] = field(default_factory=list)


@dataclass
class JobsResponse:
    """Model for jobs API response"""
    jobs: List[dict] = field(default_factory=list)
    nextPageToken: Optional[str] = None


@dataclass
class DatabaseMetadata:
    """Model for database metadata"""
    total_jobs: int
    saved_at: str


@dataclass
class DatabaseExport:
    """Model for complete database export"""
    metadata: DatabaseMetadata
    jobs: List[JobModel] = field(default_factory=list)