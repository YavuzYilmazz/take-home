import argparse
import requests
import sys
import json


def get_args():
    parser = argparse.ArgumentParser(description="Run the mock API server.")
    parser.add_argument("--base_url", default="http://127.0.0.1:5005", type=str, help="The base URL for the mock API server")
    return parser.parse_args()


def test_companies_endpoint():
    """
    Tests the new /companies endpoint to ensure the API is running
    and can provide a list of companies to test against.
    """
    args = get_args()
    companies_url = f"{args.base_url}/companies"
    print(f"--> Testing endpoint: {companies_url}")
    try:
        response = requests.get(companies_url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            companies = data.get("companies")
            if companies and isinstance(companies, list) and len(companies) > 0:
                print(f"Success! Received {len(companies)} companies.")
                # Return the first company for the next test
                return companies[0]
            else:
                print("Failure! /companies endpoint returned a valid response but no companies list.")
                return None
        else:
            print(f"\nFailure! The server responded with an error.")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"\nFailure! Could not connect to the server: {e}")
        return None

def test_jobs_endpoint(company_name: str):
    """
    Tests the /jobs endpoint using a dynamically fetched company name.
    """
    args = get_args()
    jobs_url = f"{args.base_url}/jobs"
    print(f"\n--> Testing endpoint: {jobs_url} (for company: '{company_name}')")
    try:
        page_token = None
        params = {"company": company_name}
        if page_token:
            params["pageToken"] = page_token
        response = requests.get(jobs_url, params=params, timeout=60)

        if response.status_code == 200:
            print(f"Success! The mock API server responded correctly for the /jobs endpoint.")
            print(f"Status Code: {response.status_code}")
            data = response.json()
            job_count = len(data.get("jobs", []))
            print(f"Received {job_count} job(s) for company '{company_name}'.")
            print("\n--- Sample Response ---")
            print(f"{json.dumps(data, indent=2)}")
            return True
        else:
            print(f"\nFailure! The server responded with an error.")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"\nFailure! Could not connect to the server: {e}")
        return False


def main():
    """
    Main function to run the API connection tests.
    """
    print("="*50)
    print("Attempting to connect to the mock API server...")
    print("="*50)

    test_company = test_companies_endpoint()

    if not test_company:
        print("\nAPI connection test failed at the /companies endpoint.")
        print("Please ensure the 'mock_api_server' is running.")
        sys.exit(1)

    success = test_jobs_endpoint(test_company)

    if success:
        print("\n" + "="*50)
        print("API Connection Test Passed!")
        print("="*50)
    else:
        print("\nAPI connection test failed at the /jobs endpoint.")
        sys.exit(1)


if __name__ == "__main__":
    main()