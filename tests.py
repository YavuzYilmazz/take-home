import pytest
from src.swe.db import InMemoryDB

# --- Provided Example Test ---

def test_database_save_and_upsert():
    """
    A working test to demonstrate the expected behavior of the InMemoryDB.
    This shows how to test the provided database component.
    """
    db = InMemoryDB()
    
    # 1. Initial save should insert two new jobs
    initial_jobs = [
        {"jobId": "TEST-001", "title": "Software Engineer"},
        {"jobId": "TEST-002", "title": "Data Scientist"}
    ]
    added_count = db.save_jobs(initial_jobs)
    
    assert added_count == 2, "Should return the count of newly inserted jobs."
    assert db.count() == 2, "Database should contain two jobs after initial save."
    
    # 2. A second save with an existing ID should be an update (upsert)
    updated_jobs = [
        {"jobId": "TEST-001", "title": "Senior Software Engineer"}
    ]
    added_count_after_update = db.save_jobs(updated_jobs)

    assert added_count_after_update == 0, "Should return 0 as no new jobs were inserted."
    assert db.count() == 2, "Database count should remain 2 after an update."
    
    # 3. Verify that the job was actually updated
    updated_job = db.get_job("TEST-001")
    assert updated_job is not None, "Job should still exist after update."
    assert updated_job["title"] == "Senior Software Engineer", "Job title should have been updated."


# --- Candidate-Implemented Tests ---

# TODO: Candidates should add their own tests below to cover the logic they implement.
#
# We recommend testing the following areas:
#   - Data Normalization: How your code handles various formats for locations and dates.
#   - Filtering Logic: If you implement job filtering, test that it correctly includes/excludes jobs.
#   - Error Handling: How your API client handles non-200 status codes (e.g., 404, 429, 500).
#
# Feel free to add new files for testing different parts of the system if you prefer.