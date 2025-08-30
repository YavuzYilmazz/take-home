import requests
import time
from typing import List, Dict, Any
from datetime import datetime
import re

# This is a proof-of-concept script for the take-home project.
# It contains several issues that the candidate is expected to identify and fix.
BASE_URL = "http://127.0.0.1:5005"

def fetch_company_list() -> List[str]:
    """Fetches the list of companies from the API."""
    print("Fetching list of companies...")
    try:
        response = requests.get(f"{BASE_URL}/companies", timeout=10)
        response.raise_for_status() # Will raise an exception for 4xx/5xx errors
        data = response.json()
        companies = data.get("companies", [])
        print(f"Discovered {len(companies)} companies.")
        return companies
    except requests.RequestException as e:
        print(f"Error: A network request failed while fetching companies: {e}")
        return []


class APIClient:
    def __init__(self):
        self._request_count = 0

    def fetch_company_jobs(self, company: str) -> List[Dict[str, Any]]:
        """
        Fetches job listings for a specific company (with pagination).
        """
        all_jobs = []
        page_token = None
        page_num = 1
        
        print(f"Fetching jobs for {company}...")
        
        while True:
            params = {"company": company}
            if page_token:
                params["pageToken"] = page_token
            
            try:
                response = requests.get(f"{BASE_URL}/jobs", params=params, timeout=30)
                self._request_count += 1
                
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get("jobs", [])
                    all_jobs.extend(jobs)
                    
                    print(f"  Page {page_num}: Found {len(jobs)} jobs")
                    
                    # Check if there are more pages
                    page_token = data.get("nextPageToken")
                    if not page_token:
                        break
                    
                    page_num += 1
                    
                else:
                    print(f"  Received HTTP {response.status_code} error for {company}.")
                    break
                    
            except requests.RequestException as e:
                print(f"  A network request failed for {company}: {e}.")
                break
        
        print(f"  Total: {len(all_jobs)} jobs for {company} \n")
        return all_jobs


def normalize_job_data(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes job data by standardizing location and date formats.
    """
    normalized_job = job.copy()
    
    # Normalize location
    normalized_job['location'] = normalize_location(job.get('location'))
    
    # Normalize posted date
    normalized_job['postedDate'] = normalize_date(job.get('postedDate'))
    
    return normalized_job


def normalize_location(location) -> str:
    """
    Normalizes location to standard format: "City, State/Country"
    """
    if not location:
        return "Unknown"
    
    # If it's already a string, return as is
    if isinstance(location, str):
        return location if location.strip() else "Unknown"
    
    # If it's a dictionary with city and state
    if isinstance(location, dict):
        city = location.get('city', '')
        state = location.get('state', '')
        if city and state:
            return f"{city}, {state}"
        elif city:
            return city
        elif state:
            return state
    
    return "Unknown"


def normalize_date(date_value) -> str:
    """
    Normalizes posted date to ISO format: YYYY-MM-DD
    """
    if not date_value:
        return "Unknown"
    
    # If it's a string
    if isinstance(date_value, str):
        if date_value.strip() == "" or date_value == "NaT":
            return "Unknown"
        
        # Try to parse "January 05, 2025" format
        try:
            parsed_date = datetime.strptime(date_value, "%B %d, %Y")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # Try to parse "Tue, 08 Jul 2025 11:25:55 +0000" format
        try:
            parsed_date = datetime.strptime(date_value, "%a, %d %b %Y %H:%M:%S %z")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # Try to parse "02/10/2025" format (MM/dd/yyyy)
        try:
            parsed_date = datetime.strptime(date_value, "%m/%d/%Y")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # Try to parse ISO datetime formats like "2025-04-03T11:25:55.567344+00:00"
        try:
            # Remove microseconds if present and parse
            if 'T' in date_value:
                date_part = date_value.split('T')[0]
                parsed_date = datetime.strptime(date_part, "%Y-%m-%d")
                return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # Check if it's already in YYYY-MM-DD format
        try:
            parsed_date = datetime.strptime(date_value, "%Y-%m-%d")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # If it can't be parsed, return as is
        return date_value
    
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
    print("=== Job Scraper Starting ===")
    start_time = time.time()
    
    companies_to_process = fetch_company_list()
    if not companies_to_process:
        print("No companies to process. Exiting.")
        return

    client = APIClient()
    all_jobs = []
    
    for company in companies_to_process:
        company_jobs = client.fetch_company_jobs(company)
        
        for job in company_jobs:
             all_jobs.append(normalize_job_data(job))
    
    print("\n" + "="*25 + " Results Summary " + "="*25)
    print(f"Total jobs found: {len(all_jobs)}")
    print(f"Total API requests made: {client._request_count}")
    print(f"Total time taken: {time.time() - start_time:.2f}s")
    print("="*70)

if __name__ == "__main__":
    main()