"""
Comprehensive test suite for the job scraper system.
Tests cover data normalization, model validation, and database operations.
"""

from src.swe.db import InMemoryDB
from src.swe.scraper import normalize_job_data, normalize_location, normalize_date
from src.swe.models import JobModel

# --- Provided Example Test ---

def test_database_save_and_upsert():
    """
    A working test to demonstrate the expected behavior of the InMemoryDB.
    Updated to work with JobModel instances instead of raw dictionaries.
    """
    db = InMemoryDB()
    
    # 1. Initial save should insert two new jobs
    initial_jobs = [
        JobModel(jobId="TEST-001", title="Software Engineer", company="TechCorp"),
        JobModel(jobId="TEST-002", title="Data Scientist", company="DataCorp")
    ]
    added_count = db.save_jobs(initial_jobs)
    
    assert added_count == 2, "Should return the count of newly inserted jobs."
    assert db.count() == 2, "Database should contain two jobs after initial save."
    
    # 2. A second save with an existing ID should be an update (upsert)
    updated_jobs = [
        JobModel(jobId="TEST-001", title="Senior Software Engineer", company="TechCorp")
    ]
    added_count_after_update = db.save_jobs(updated_jobs)

    assert added_count_after_update == 0, "Should return 0 as no new jobs were inserted."
    assert db.count() == 2, "Database count should remain 2 after an update."
    
    # 3. Verify that the job was actually updated
    updated_job = db.get_job("TEST-001")
    assert updated_job is not None, "Job should still exist after update."
    assert updated_job.title == "Senior Software Engineer", "Job title should have been updated."


# --- Candidate-Implemented Tests ---

def test_job_model_validation():
    """Test JobModel validation and normalization"""
    # Test valid job model
    job = JobModel(
        jobId="TEST-123",
        title="Software Engineer",
        company="TechCorp",
        location="San Francisco, CA",
        workType="Remote",
        postedDate="2025-01-15",
        applicants=42
    )
    
    assert job.jobId == "TEST-123"
    assert job.workType == "Remote"
    assert job.applicants == 42
    
    # Test invalid work type gets corrected
    job_invalid = JobModel(
        jobId="TEST-456",
        title="Developer",
        company="StartupXYZ",
        workType="InvalidType"  # Should be corrected to "Unknown"
    )
    
    assert job_invalid.workType == "Unknown"
    
    # Test negative applicants get corrected
    job_negative = JobModel(
        jobId="TEST-789",
        title="Analyst",
        company="DataCorp",
        applicants=-5  # Should be corrected to 0
    )
    
    assert job_negative.applicants == 0


def test_normalize_location_with_work_types():
    """Test location normalization and work type extraction"""
    
    # Test remote work type extraction
    result = normalize_location("Remote")
    assert result == {"location": "Unknown", "workType": "Remote"}
    
    # Test on-site variations
    assert normalize_location("On-site") == {"location": "Unknown", "workType": "On-site"}
    assert normalize_location("onsite") == {"location": "Unknown", "workType": "On-site"}
    
    # Test hybrid
    assert normalize_location("hybrid") == {"location": "Unknown", "workType": "Hybrid"}
    
    # Test normal location (string)
    assert normalize_location("New York, NY") == "New York, NY"
    
    # Test US location standardization
    assert normalize_location("San Francisco, California, USA") == "San Francisco, California"
    
    # Test international location
    assert normalize_location("London, England, UK") == "London, UK"
    
    # Test dictionary location
    location_dict = {
        "city": "Austin",
        "state": "Texas",
        "country": "USA"
    }
    assert normalize_location(location_dict) == "Austin, Texas"


def test_normalize_date_formats():
    """Test date normalization with various formats"""
    
    # Test ISO format (already correct)
    assert normalize_date("2025-01-15") == "2025-01-15"
    
    # Test month name format
    assert normalize_date("January 15, 2025") == "2025-01-15"
    
    # Test MM/dd/yyyy format
    assert normalize_date("01/15/2025") == "2025-01-15"
    
    # Test RFC format
    assert normalize_date("Tue, 15 Jan 2025 10:30:00 +0000") == "2025-01-15"
    
    # Test ISO datetime format
    assert normalize_date("2025-01-15T10:30:00.123456+00:00") == "2025-01-15"
    
    # Test unix timestamp (seconds)
    assert normalize_date(1736942400) == "2025-01-15"  # Approximate timestamp
    
    # Test invalid formats
    assert normalize_date("invalid-date") == "Unknown"
    assert normalize_date("") == "Unknown"
    assert normalize_date(None) == "Unknown"
    assert normalize_date("n/a") == "Unknown"


def test_normalize_job_data_integration():
    """Test complete job data normalization pipeline"""
    
    # Test job with various data formats
    raw_job = {
        "jobId": "JOB-12345",
        "title": "Senior Python Developer",
        "company": "TechStartup",
        "location": {"city": "Seattle", "state": "Washington", "country": "USA"},
        "postedDate": "January 20, 2025",
        "applicants": 75,
        "description": "Exciting opportunity for a Python developer"
    }
    
    job_model = normalize_job_data(raw_job)
    
    # Verify all fields are correctly normalized
    assert job_model.jobId == "JOB-12345"
    assert job_model.title == "Senior Python Developer"
    assert job_model.company == "TechStartup"
    assert job_model.location == "Seattle, Washington"  # US format
    assert job_model.workType == "Unknown"  # No work type in location
    assert job_model.postedDate == "2025-01-20"  # Normalized date
    assert job_model.applicants == 75
    assert job_model.description == "Exciting opportunity for a Python developer"
    
    # Test job with work type in location
    remote_job = {
        "jobId": "REMOTE-001",
        "title": "Remote Engineer",
        "company": "GlobalCorp",
        "location": "Remote",
        "postedDate": "2025-01-22",
        "applicants": 150
    }
    
    remote_model = normalize_job_data(remote_job)
    assert remote_model.location == "Unknown"
    assert remote_model.workType == "Remote"


def test_database_with_job_models():
    """Test database operations with JobModel instances"""
    
    db = InMemoryDB()
    
    # Create test job models
    jobs = [
        JobModel(
            jobId="MODEL-001",
            title="Backend Engineer",
            company="WebCorp",
            location="Boston, MA",
            workType="Hybrid",
            postedDate="2025-01-25",
            applicants=30
        ),
        JobModel(
            jobId="MODEL-002", 
            title="Frontend Developer",
            company="UICorp",
            location="Unknown",
            workType="Remote",
            postedDate="2025-01-26",
            applicants=25
        )
    ]
    
    # Test saving JobModel instances
    new_count = db.save_jobs(jobs)
    assert new_count == 2
    assert db.count() == 2
    
    # Test retrieval
    retrieved_job = db.get_job("MODEL-001")
    assert isinstance(retrieved_job, JobModel)
    assert retrieved_job.title == "Backend Engineer"
    assert retrieved_job.workType == "Hybrid"
    
    # Test total applicants calculation
    total_applicants = db.get_total_applicants()
    assert total_applicants == 55  # 30 + 25
    
    # Test get all jobs
    all_jobs = db.get_all_jobs()
    assert len(all_jobs) == 2
    assert all(isinstance(job, JobModel) for job in all_jobs)


def run_all_tests():
    """Run all tests and report results"""
    tests = [
        test_database_save_and_upsert,
        test_job_model_validation,
        test_normalize_location_with_work_types,
        test_normalize_date_formats,
        test_normalize_job_data_integration,
        test_database_with_job_models
    ]
    
    passed = 0
    failed = 0
    
    print("=" * 50)
    print("🧪 RUNNING TEST SUITE")
    print("=" * 50)
    
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__} - PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} - FAILED: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)