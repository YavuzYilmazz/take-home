import requests
import time
from typing import List, Dict, Any
from datetime import datetime
import re
from pathlib import Path
import logging
from time import sleep

from .db import InMemoryDB
from .models import JobModel, CompanyResponse, JobsResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s %(asctime)s - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# This is a proof-of-concept script for the take-home project.
# It contains several issues that the candidate is expected to identify and fix.
BASE_URL = "http://127.0.0.1:5005"

def fetch_company_list() -> List[str]:
    """Fetches the list of companies from the API using CompanyResponse model."""
    logger.info("Fetching list of companies...")
    try:
        response = requests.get(f"{BASE_URL}/companies", timeout=10)
        response.raise_for_status() # Will raise an exception for 4xx/5xx errors
        data = response.json()
        
        # Use CompanyResponse model for validation
        company_response = CompanyResponse(companies=data.get("companies", []))
        
        logger.info(f"Discovered {len(company_response.companies)} companies.")
        return company_response.companies
    except requests.RequestException as e:
        logger.error(f"Error: A network request failed while fetching companies: {e}")
        return []


class APIClient:
    def __init__(self, max_retries=3):
        self._request_count = 0
        self.max_retries = max_retries

    def _make_request_with_retry(self, url, params, timeout=30):
        """Make HTTP request with retry logic for 500 errors"""
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(url, params=params, timeout=timeout)
                self._request_count += 1
                
                if response.status_code == 200:
                    return response
                elif response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.max_retries:
                        wait_time = (2 ** attempt) * 1  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(f"HTTP {response.status_code} error, attempt {attempt + 1}/{self.max_retries + 1}. Retrying in {wait_time}s...")
                        sleep(wait_time)
                        continue
                    else:
                        logger.error(f"HTTP {response.status_code} error after {self.max_retries} retries")
                        return response
                else:
                    # Client error (4xx) - don't retry
                    logger.error(f"HTTP {response.status_code} client error - not retrying")
                    return response
                    
            except requests.RequestException as e:
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) * 1
                    logger.warning(f"Network error on attempt {attempt + 1}/{self.max_retries + 1}: {e}. Retrying in {wait_time}s...")
                    sleep(wait_time)
                    continue
                else:
                    logger.error(f"Network error after {self.max_retries} retries: {e}")
                    raise
        
        return None

    def fetch_company_jobs(self, company: str) -> List[Dict[str, Any]]:
        """
        Fetches job listings for a specific company (with pagination, retry logic, and rate limiting).
        """
        all_jobs = []
        page_token = None
        page_num = 1
        
        logger.info(f"Fetching jobs for {company}...")
        
        while True:
            params = {"company": company}
            if page_token:
                params["pageToken"] = page_token
            
            try:
                response = self._make_request_with_retry(f"{BASE_URL}/jobs", params)
                
                if response and response.status_code == 200:
                    data = response.json()
                    jobs = data.get("jobs", [])
                    all_jobs.extend(jobs)
                    
                    logger.info(f"  Page {page_num}: Found {len(jobs)} jobs")
                    
                    # Check if there are more pages
                    page_token = data.get("nextPageToken")
                    if not page_token:
                        break
                    
                    page_num += 1
                    
                else:
                    error_msg = f"Failed to fetch jobs for {company}"
                    if response:
                        error_msg += f" - HTTP {response.status_code}"
                    logger.error(error_msg)
                    break
                    
            except requests.RequestException as e:
                logger.error(f"Network request failed for {company}: {e}")
                break
        
        logger.info(f"  Total: {len(all_jobs)} jobs for {company}")
        if all_jobs:
            logger.info("")  # Empty line for spacing
        return all_jobs


def normalize_job_data(job: Dict[str, Any]) -> JobModel:
    """
    Normalizes job data and returns a validated JobModel instance.
    """
    # Extract basic fields
    job_id = job.get('jobId', '')
    title = job.get('title', '')
    company = job.get('company', '')
    description = job.get('description')
    applicants = job.get('applicants', 0)
    
    # Normalize location and extract work type
    location_result = normalize_location(job.get('location'))
    if isinstance(location_result, dict):
        location = location_result['location']
        work_type = location_result['workType']
    else:
        location = location_result
        work_type = "Unknown"
    
    # Normalize posted date
    posted_date = normalize_date(job.get('postedDate'))
    
    # Create and return JobModel (validation happens in __post_init__)
    return JobModel(
        jobId=job_id,
        title=title,
        company=company,
        location=location,
        workType=work_type,
        postedDate=posted_date,
        applicants=applicants,
        description=description
    )


def standardize_location_string(location_str: str) -> str:
    """
    Standardizes location strings like "City, State, Country" to "City, State" or "City, Country"
    """
    if not location_str or ',' not in location_str:
        return location_str
    
    parts = [part.strip() for part in location_str.split(',')]
    
    # If we have 3 parts: City, State, Country
    if len(parts) == 3:
        city, state, country = parts
        country_lower = country.lower()
        if country_lower in ['usa', 'us', 'united states', 'united states of america']:
            return f"{city}, {state}"
        else:
            return f"{city}, {country}"
    
    # If 2 parts or other cases, return as is
    return location_str


def normalize_location(location):
    """
    Normalizes location to standard format: "City, State/Country"
    Returns either a string (normal location) or dict with location and workType
    """
    if not location:
        return "Unknown"
    
    # If it's already a string, clean it up
    if isinstance(location, str):
        location_clean = location.strip()
        if not location_clean:
            return "Unknown"
        
        # Handle special cases - extract work type!
        location_lower = location_clean.lower()
        if location_lower in ['remote']:
            return {"location": "Unknown", "workType": "Remote"}
        elif location_lower in ['on-site', 'onsite', 'on site']:
            return {"location": "Unknown", "workType": "On-site"}
        elif location_lower in ['hybrid']:
            return {"location": "Unknown", "workType": "Hybrid"}
        elif location_lower in ['unknown', 'n/a', 'na', 'not available', 'not specified']:
            return "Unknown"
        
        # Standardize string locations like "City, State, Country"
        location_clean = standardize_location_string(location_clean)
        
        return location_clean
    
    # If it's a dictionary with city and state
    if isinstance(location, dict):
        city = location.get('city', '') or ''
        state = location.get('state', '') or ''
        country = location.get('country', '') or ''
        
        # Ensure they are strings and strip
        city = str(city).strip()
        state = str(state).strip()
        country = str(country).strip()
        
        # Check if city itself is a work type (like Remote, On-site)
        if city:
            city_lower = city.lower()
            if city_lower in ['remote']:
                return {"location": "Unknown", "workType": "Remote"}
            elif city_lower in ['on-site', 'onsite', 'on site']:
                return {"location": "Unknown", "workType": "On-site"}
            elif city_lower in ['hybrid']:
                return {"location": "Unknown", "workType": "Hybrid"}
            elif city_lower in ['unknown', 'n/a', 'na', 'not available', 'not specified']:
                return "Unknown"
        
        # Build location string from components with standardization
        if city and state and country:
            # If we have all three, prefer City, State for US locations
            country_lower = country.lower()
            if country_lower in ['usa', 'us', 'united states', 'united states of america']:
                return f"{city}, {state}"
            else:
                return f"{city}, {country}"
        elif city and state:
            return f"{city}, {state}"
        elif city and country:
            return f"{city}, {country}"
        elif city:
            return city
        elif state:
            return state
        elif country:
            return country
    
    return "Unknown"


def normalize_date(date_value) -> str:
    """
    Normalizes posted date to ISO format: YYYY-MM-DD
    """
    if not date_value:
        return "Unknown"
    
    # If it's a string
    if isinstance(date_value, str):
        date_clean = date_value.strip()
        if not date_clean:
            return "Unknown"
        
        # Handle special cases
        date_lower = date_clean.lower()
        if date_lower in ["nat", "not available", "n/a", "na", "not specified", "unknown"]:
            return "Unknown"
        
        # Try to parse "January 05, 2025" format
        try:
            parsed_date = datetime.strptime(date_clean, "%B %d, %Y")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # Try to parse "Tue, 08 Jul 2025 11:25:55 +0000" format
        try:
            parsed_date = datetime.strptime(date_clean, "%a, %d %b %Y %H:%M:%S %z")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # Try to parse "02/10/2025" format (MM/dd/yyyy)
        try:
            parsed_date = datetime.strptime(date_clean, "%m/%d/%Y")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # Try to parse ISO datetime formats like "2025-04-03T11:25:55.567344+00:00"
        try:
            # Remove microseconds if present and parse
            if 'T' in date_clean:
                date_part = date_clean.split('T')[0]
                parsed_date = datetime.strptime(date_part, "%Y-%m-%d")
                return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # Check if it's already in YYYY-MM-DD format
        try:
            parsed_date = datetime.strptime(date_clean, "%Y-%m-%d")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # If it can't be parsed, return Unknown instead of the invalid string
        return "Unknown"
    
    # If it's a unix timestamp (integer) - handle both seconds and milliseconds
    if isinstance(date_value, (int, float)):
        try:
            # If it's a large number, it might be in milliseconds
            if date_value > 1e10:  # If timestamp is > year 2001 in milliseconds
                timestamp = date_value / 1000  # Convert to seconds
            else:
                timestamp = date_value
            
            parsed_date = datetime.fromtimestamp(timestamp)
            return parsed_date.strftime("%Y-%m-%d")
        except (ValueError, OSError):
            return "Unknown"
    
    return "Unknown"


def main():
    """
    Main scraper function.
    """
    logger.info("=== Job Scraper Starting ===")
    start_time = time.time()
    
    # Initialize database
    db = InMemoryDB()
    
    companies_to_process = fetch_company_list()  # Process all companies
    if not companies_to_process:
        logger.error("No companies to process. Exiting.")
        return

    client = APIClient(max_retries=3)
    
    # Process each company
    successful_companies = 0
    for i, company in enumerate(companies_to_process, 1):
        logger.info(f"Processing company {i}/{len(companies_to_process)}: {company}")
        
        company_jobs = client.fetch_company_jobs(company)
        
        if company_jobs:
            # Normalize all jobs for this company using JobModel
            normalized_jobs = []
            for job in company_jobs:
                try:
                    job_model = normalize_job_data(job)
                    normalized_jobs.append(job_model)
                except Exception as e:
                    logger.warning(f"Failed to normalize job {job.get('jobId', 'unknown')}: {e}")
                    continue
            
            # Save to database
            new_inserts = db.save_jobs(normalized_jobs)
            logger.info(f"  Saved {new_inserts} new jobs from {company} to database")
            successful_companies += 1
        else:
            logger.warning(f"  No jobs found for {company}")
        
        # Add spacing between companies (2 empty lines)
        if i < len(companies_to_process):
            logger.info("")
            logger.info("")
    
    # Save to file (in workspace root, not src directory)
    output_file = Path("../jobs_data.json")
    try:
        db.save_to_file(output_file)
        logger.info(f"Successfully saved data to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save data to file: {e}")
    
    # Generate final summary
    total_jobs = db.count()
    total_applicants = db.get_total_applicants()
    
    logger.info("")  # Empty line before summary
    logger.info("=" * 25 + " Results Summary " + "=" * 25)
    logger.info(f"Total companies processed: {len(companies_to_process)}")
    logger.info(f"Successful companies: {successful_companies}")
    logger.info(f"Total jobs stored: {total_jobs}")
    logger.info(f"Total applicants counted: {total_applicants}")
    logger.info(f"Total API requests made: {client._request_count}")
    logger.info(f"Total time taken: {time.time() - start_time:.2f}s")
    logger.info(f"Average time per company: {(time.time() - start_time) / len(companies_to_process):.2f}s")
    logger.info(f"Data saved to: {output_file}")
    logger.info("="*70)

if __name__ == "__main__":
    main()