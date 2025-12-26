"""
Standalone example for calling the /leases/upload/batch API endpoint.
This script demonstrates how to upload multiple lease PDFs at once.
"""

import requests
import os
import sys


# API Configuration
API_BASE_URL = "http://localhost:5000"
UPLOAD_BATCH_ENDPOINT = f"{API_BASE_URL}/leases/upload/batch"
UPLOAD_SINGLE_ENDPOINT = f"{API_BASE_URL}/leases/upload"
PROCESS_ENDPOINT = f"{API_BASE_URL}/leases/process"
STATUS_ENDPOINT = f"{API_BASE_URL}/leases/process/status"
LIST_LEASES_ENDPOINT = f"{API_BASE_URL}/leases"


def upload_single_lease(pdf_path):
    """
    Upload a single lease PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Response JSON or None if failed
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return None

    print(f"\nUploading single file: {pdf_path}")

    with open(pdf_path, 'rb') as f:
        files = {'pdf': (os.path.basename(pdf_path), f, 'application/pdf')}
        response = requests.post(UPLOAD_SINGLE_ENDPOINT, files=files)

    if response.status_code == 201:
        result = response.json()
        print(f"  Success! Lease ID: {result.get('lease_id')}")
        print(f"  Status: {result.get('status')}")
        return result
    else:
        print(f"  Failed! Status: {response.status_code}")
        print(f"  Error: {response.json().get('error', 'Unknown error')}")
        return None


def upload_multiple_leases(pdf_paths):
    """
    Upload multiple lease PDF files in a single batch request.

    Args:
        pdf_paths: List of paths to PDF files

    Returns:
        Response JSON or None if failed
    """
    # Validate files exist
    valid_files = []
    for path in pdf_paths:
        if os.path.exists(path):
            valid_files.append(path)
        else:
            print(f"Warning: File not found, skipping: {path}")

    if not valid_files:
        print("Error: No valid files to upload")
        return None

    print(f"\nUploading {len(valid_files)} files in batch...")

    # Prepare files for multipart upload
    # Note: 'pdf' is the field name expected by the API
    files = []
    file_handles = []

    try:
        for path in valid_files:
            f = open(path, 'rb')
            file_handles.append(f)
            files.append(('pdf', (os.path.basename(path), f, 'application/pdf')))

        # Make the request
        response = requests.post(UPLOAD_BATCH_ENDPOINT, files=files)

    finally:
        # Close all file handles
        for f in file_handles:
            f.close()

    if response.status_code == 201:
        result = response.json()
        print(f"\nBatch upload completed!")
        print(f"  Total files: {result.get('total')}")
        print(f"  Successful: {result.get('successful')}")
        print(f"\nResults:")
        for item in result.get('results', []):
            if item.get('success'):
                print(f"  ✓ {item.get('filename')} - Lease ID: {item.get('lease_id')}")
            else:
                print(f"  ✗ {item.get('filename')} - Error: {item.get('error')}")
        return result
    else:
        print(f"Batch upload failed! Status: {response.status_code}")
        print(f"Error: {response.json().get('error', 'Unknown error')}")
        return None


def trigger_processing():
    """
    Trigger batch processing of pending leases.
    """
    print("\nTriggering batch processing...")
    response = requests.post(PROCESS_ENDPOINT)

    result = response.json()
    print(f"  Message: {result.get('message')}")
    if 'pending' in result:
        print(f"  Pending files: {result.get('pending')}")
    if 'batch_size' in result:
        print(f"  Batch size: {result.get('batch_size')}")

    return result


def get_processing_status():
    """
    Get current processing status.
    """
    print("\nChecking processing status...")
    response = requests.get(STATUS_ENDPOINT)

    if response.status_code == 200:
        result = response.json()
        print(f"  Is processing: {result.get('is_processing')}")
        counts = result.get('counts', {})
        print(f"  Pending: {counts.get('pending', 0)}")
        print(f"  Processing: {counts.get('processing', 0)}")
        print(f"  Processed: {counts.get('processed', 0)}")
        print(f"  Failed: {counts.get('failed', 0)}")
        print(f"  Total: {counts.get('total', 0)}")
        return result
    else:
        print(f"Failed to get status: {response.status_code}")
        return None


def list_leases(status=None, page=1, limit=10):
    """
    List uploaded leases with optional filtering.

    Args:
        status: Filter by status (pending, processing, processed, failed)
        page: Page number
        limit: Items per page
    """
    params = {'page': page, 'limit': limit}
    if status:
        params['status'] = status

    print(f"\nListing leases (status={status}, page={page})...")
    response = requests.get(LIST_LEASES_ENDPOINT, params=params)

    if response.status_code == 200:
        result = response.json()
        print(f"  Total: {result.get('total')}")
        print(f"  Page: {result.get('page')} of {result.get('total_pages')}")
        print(f"\nLeases:")
        for lease in result.get('leases', []):
            print(f"  - {lease.get('original_filename')}")
            print(f"    ID: {lease.get('_id')}")
            print(f"    Status: {lease.get('status')}")
            print(f"    Created: {lease.get('created_at')}")
        return result
    else:
        print(f"Failed to list leases: {response.status_code}")
        return None


def main():
    """
    Main function demonstrating the lease upload workflow.
    """
    print("=" * 60)
    print("Lease Upload Batch Example")
    print("=" * 60)

    # Example 1: Upload multiple files
    # Replace these paths with actual PDF files
    pdf_files = [
        "sample_lease_1.pdf",
        "sample_lease_2.pdf",
        "sample_lease_3.pdf",
    ]

    # Check if sample files exist, if not create dummy info
    existing_files = [f for f in pdf_files if os.path.exists(f)]

    if not existing_files:
        print("\nNo sample PDF files found in current directory.")
        print("To test, create PDF files or modify the pdf_files list.")
        print("\nExample usage:")
        print('  pdf_files = ["path/to/lease1.pdf", "path/to/lease2.pdf"]')
        print("\nDemonstrating API calls with status check...")

        # Still demonstrate the status and list endpoints
        get_processing_status()
        list_leases()
        return

    # Upload files in batch
    upload_result = upload_multiple_leases(existing_files)

    if upload_result and upload_result.get('successful', 0) > 0:
        # Trigger processing
        trigger_processing()

        # Check status
        import time
        print("\nWaiting 2 seconds before checking status...")
        time.sleep(2)
        get_processing_status()

        # List all leases
        list_leases()


def example_with_custom_files():
    """
    Example showing how to use the functions with custom file paths.
    """
    # Upload specific files
    files_to_upload = [
        r"C:\path\to\lease1.pdf",
        r"C:\path\to\lease2.pdf",
        r"D:\documents\lease3.pdf",
    ]

    # Batch upload
    result = upload_multiple_leases(files_to_upload)

    # Or upload single file
    # result = upload_single_lease(r"C:\path\to\single_lease.pdf")

    # Trigger processing after upload
    if result:
        trigger_processing()


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        # If PDF files are provided as arguments, upload them
        pdf_files = sys.argv[1:]
        print(f"Uploading {len(pdf_files)} files from command line...")
        upload_multiple_leases(pdf_files)
        trigger_processing()
        get_processing_status()
    else:
        # Run the main demo
        main()
