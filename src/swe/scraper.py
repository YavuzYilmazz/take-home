import requests
import time
from typing import List, Dict, Any

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
        Fetches job listings for a specific company.
        """
        page_token = None
        print(f"Fetching jobs for {company}...")
        params = {"company": company}
        if page_token:
            params["pageToken"] = page_token
        
        try:
            response = requests.get(f"{BASE_URL}/jobs", params=params, timeout=30)
            self._request_count += 1
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("jobs", [])
                print(f"  Found {len(jobs)} jobs for {company}.")
                return jobs
            else:
                print(f"  Received HTTP {response.status_code} error for {company}.")
                return []
                
        except requests.RequestException as e:
            print(f"  A network request failed for {company}: {e}.")
            return []


def normalize_job_data(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    A placeholder for data normalization.
    """
    return job


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