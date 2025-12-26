"""
Standalone example for importing and processing lease PDFs from input folders.

This script demonstrates how to:
1. List available folders in input_folders directory
2. Import PDFs from folders into the system
3. Process the imported files in batches of 2
4. Monitor processing status

Usage:
    python examples/import_from_folders_example.py
    python examples/import_from_folders_example.py --folder client_a
    python examples/import_from_folders_example.py --auto-process
"""

import requests
import time
import argparse
import sys


# API Configuration
API_BASE_URL = "http://localhost:5000"

# Endpoints
LIST_FOLDERS_ENDPOINT = f"{API_BASE_URL}/leases/folders"
IMPORT_FOLDERS_ENDPOINT = f"{API_BASE_URL}/leases/import-from-folders"
PROCESS_ENDPOINT = f"{API_BASE_URL}/leases/process"
STATUS_ENDPOINT = f"{API_BASE_URL}/leases/process/status"
LIST_LEASES_ENDPOINT = f"{API_BASE_URL}/leases"


def list_input_folders(input_path=None):
    """
    List all folders in the input_folders directory.

    Args:
        input_path: Custom path to input_folders (optional)

    Returns:
        Response JSON or None if failed
    """
    print("\n" + "=" * 60)
    print("Listing Input Folders")
    print("=" * 60)

    params = {}
    if input_path:
        params['input_path'] = input_path

    try:
        response = requests.get(LIST_FOLDERS_ENDPOINT, params=params)

        if response.status_code == 200:
            result = response.json()
            print(f"\nInput path: {result.get('input_path')}")
            print(f"Total folders: {result.get('total_folders')}")
            print(f"Total PDF files: {result.get('total_pdf_files')}")

            folders = result.get('folders', [])
            if folders:
                print("\nFolders:")
                print("-" * 40)
                for folder in folders:
                    print(f"  {folder.get('name'):<30} ({folder.get('pdf_count')} PDFs)")
            else:
                print("\nNo folders found.")
                print("Create subfolders inside 'input_folders' and place PDF files in them.")

            return result

        elif response.status_code == 404:
            result = response.json()
            print(f"\nError: {result.get('error')}")
            print(f"Hint: {result.get('hint', '')}")
            return None

        else:
            print(f"\nFailed! Status: {response.status_code}")
            print(f"Error: {response.json().get('error', 'Unknown error')}")
            return None

    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to API server.")
        print("Make sure the server is running at", API_BASE_URL)
        return None


def import_from_folders(folder_name=None, auto_process=False, input_path=None):
    """
    Import PDF files from input folders.

    Args:
        folder_name: Specific folder to import from (optional)
        auto_process: Whether to automatically start processing
        input_path: Custom path to input_folders (optional)

    Returns:
        Response JSON or None if failed
    """
    print("\n" + "=" * 60)
    print("Importing PDFs from Folders")
    print("=" * 60)

    payload = {
        "auto_process": auto_process
    }

    if folder_name:
        payload["folder_name"] = folder_name
        print(f"Importing from folder: {folder_name}")

    if input_path:
        payload["input_path"] = input_path

    print(f"Auto-process: {auto_process}")

    try:
        response = requests.post(
            IMPORT_FOLDERS_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()

            print(f"\n{result.get('message')}")
            print(f"\nInput path: {result.get('input_path')}")
            print(f"Folders scanned: {', '.join(result.get('folders_scanned', []))}")
            print(f"\nSummary:")
            print(f"  Files found:    {result.get('files_found', 0)}")
            print(f"  Files imported: {result.get('files_imported', 0)}")
            print(f"  Files skipped:  {result.get('files_skipped', 0)}")
            print(f"  Files failed:   {result.get('files_failed', 0)}")

            if result.get('processing_started'):
                print(f"\nProcessing started automatically!")
            elif 'processing_started' in result and not result['processing_started']:
                print(f"\nProcessing not started: {result.get('processing_note', 'Unknown reason')}")

            # Show details
            details = result.get('details', [])
            if details:
                print(f"\nDetails:")
                print("-" * 60)
                for item in details:
                    status = item.get('status')
                    file = item.get('file')
                    if status == 'imported':
                        print(f"  [IMPORTED] {file}")
                        print(f"             Lease ID: {item.get('lease_id')}")
                    elif status == 'skipped':
                        print(f"  [SKIPPED]  {file}")
                        print(f"             Reason: {item.get('reason')}")
                    elif status == 'failed':
                        print(f"  [FAILED]   {file}")
                        print(f"             Reason: {item.get('reason')}")

            return result

        elif response.status_code == 404:
            result = response.json()
            print(f"\nError: {result.get('error')}")
            if 'hint' in result:
                print(f"Hint: {result.get('hint')}")
            return None

        else:
            print(f"\nFailed! Status: {response.status_code}")
            print(f"Error: {response.json().get('error', 'Unknown error')}")
            return None

    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to API server.")
        print("Make sure the server is running at", API_BASE_URL)
        return None


def trigger_processing():
    """
    Trigger batch processing of pending leases.
    """
    print("\n" + "=" * 60)
    print("Triggering Batch Processing")
    print("=" * 60)

    try:
        response = requests.post(PROCESS_ENDPOINT)
        result = response.json()

        print(f"\nMessage: {result.get('message')}")
        if 'pending' in result:
            print(f"Pending files: {result.get('pending')}")
        if 'batch_size' in result:
            print(f"Batch size: {result.get('batch_size')}")

        return result

    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to API server.")
        return None


def get_processing_status():
    """
    Get current processing status.
    """
    try:
        response = requests.get(STATUS_ENDPOINT)

        if response.status_code == 200:
            result = response.json()
            return result
        else:
            return None

    except requests.exceptions.ConnectionError:
        return None


def print_status(status):
    """Print processing status in a formatted way."""
    if not status:
        print("Could not get status")
        return

    counts = status.get('counts', {})
    is_processing = status.get('is_processing', False)

    print(f"\nProcessing: {'Yes' if is_processing else 'No'}")
    print(f"  Pending:    {counts.get('pending', 0)}")
    print(f"  Processing: {counts.get('processing', 0)}")
    print(f"  Processed:  {counts.get('processed', 0)}")
    print(f"  Failed:     {counts.get('failed', 0)}")
    print(f"  Total:      {counts.get('total', 0)}")


def monitor_processing(interval=5, max_wait=300):
    """
    Monitor processing status until complete.

    Args:
        interval: Seconds between status checks
        max_wait: Maximum seconds to wait
    """
    print("\n" + "=" * 60)
    print("Monitoring Processing Status")
    print("=" * 60)
    print(f"Checking every {interval} seconds (max wait: {max_wait}s)")

    start_time = time.time()
    last_processed = 0

    while True:
        status = get_processing_status()

        if not status:
            print("\nCould not get status. Retrying...")
            time.sleep(interval)
            continue

        counts = status.get('counts', {})
        is_processing = status.get('is_processing', False)
        pending = counts.get('pending', 0)
        processing = counts.get('processing', 0)
        processed = counts.get('processed', 0)

        # Show progress
        elapsed = int(time.time() - start_time)
        print(f"\r[{elapsed:3d}s] Pending: {pending}, Processing: {processing}, "
              f"Processed: {processed}, Running: {is_processing}    ", end='')

        # Check if done
        if not is_processing and pending == 0 and processing == 0:
            print(f"\n\nProcessing complete!")
            print_status(status)
            break

        # Check if new files were processed
        if processed > last_processed:
            print(f"\n      -> {processed - last_processed} file(s) processed")
            last_processed = processed

        # Check timeout
        if time.time() - start_time > max_wait:
            print(f"\n\nTimeout reached ({max_wait}s). Current status:")
            print_status(status)
            break

        time.sleep(interval)


def list_leases(status_filter=None, limit=10):
    """
    List leases with optional status filter.
    """
    params = {'limit': limit}
    if status_filter:
        params['status'] = status_filter

    try:
        response = requests.get(LIST_LEASES_ENDPOINT, params=params)

        if response.status_code == 200:
            result = response.json()
            return result
        return None

    except requests.exceptions.ConnectionError:
        return None


def show_results():
    """Show final results after processing."""
    print("\n" + "=" * 60)
    print("Final Results")
    print("=" * 60)

    # Get processed leases
    result = list_leases(status_filter='processed', limit=20)
    if result:
        leases = result.get('leases', [])
        print(f"\nProcessed leases ({result.get('total', 0)} total):")
        print("-" * 60)
        for lease in leases[:10]:  # Show first 10
            print(f"  {lease.get('original_filename')}")
            print(f"    ID: {lease.get('_id')}")
            print(f"    Source: {lease.get('source_folder', 'N/A')}")
            print(f"    Result ID: {lease.get('result_id', 'N/A')}")
            print()

    # Get failed leases
    result = list_leases(status_filter='failed', limit=10)
    if result and result.get('total', 0) > 0:
        leases = result.get('leases', [])
        print(f"\nFailed leases ({result.get('total', 0)} total):")
        print("-" * 60)
        for lease in leases:
            print(f"  {lease.get('original_filename')}")
            print(f"    Error: {lease.get('error_message', 'Unknown')}")
            print()


def main():
    """Main function demonstrating the folder import workflow."""
    parser = argparse.ArgumentParser(
        description='Import and process lease PDFs from input folders'
    )
    parser.add_argument(
        '--folder', '-f',
        help='Specific folder to import from'
    )
    parser.add_argument(
        '--auto-process', '-a',
        action='store_true',
        help='Automatically start processing after import'
    )
    parser.add_argument(
        '--monitor', '-m',
        action='store_true',
        help='Monitor processing until complete'
    )
    parser.add_argument(
        '--input-path', '-p',
        help='Custom path to input_folders directory'
    )
    parser.add_argument(
        '--list-only', '-l',
        action='store_true',
        help='Only list folders, do not import'
    )
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Only show current processing status'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Lease Import from Folders Example")
    print("=" * 60)

    # Status only mode
    if args.status:
        status = get_processing_status()
        print_status(status)
        return

    # List folders
    folders_result = list_input_folders(args.input_path)

    if args.list_only:
        return

    if not folders_result:
        print("\nCannot proceed without input folders.")
        print("\nSetup instructions:")
        print("1. Create 'input_folders' directory in the project root")
        print("2. Create subfolders inside it (e.g., 'client_a', 'client_b')")
        print("3. Place PDF files in those subfolders")
        print("4. Run this script again")
        return

    if folders_result.get('total_pdf_files', 0) == 0:
        print("\nNo PDF files found in input folders.")
        print("Add PDF files to the subfolders and try again.")
        return

    # Import from folders
    import_result = import_from_folders(
        folder_name=args.folder,
        auto_process=args.auto_process,
        input_path=args.input_path
    )

    if not import_result:
        return

    # If not auto-processing, ask to trigger manually
    if not args.auto_process and import_result.get('files_imported', 0) > 0:
        print("\n" + "-" * 60)
        response = input("Start processing now? (y/n): ").strip().lower()
        if response == 'y':
            trigger_processing()
            args.monitor = True

    # Monitor if requested or auto-processing
    if args.monitor or args.auto_process:
        if import_result.get('files_imported', 0) > 0 or import_result.get('processing_started'):
            monitor_processing()
            show_results()


def quick_import_and_process(folder_name=None):
    """
    Quick helper function to import and process in one call.

    Args:
        folder_name: Optional specific folder to import

    Example:
        from examples.import_from_folders_example import quick_import_and_process
        quick_import_and_process()  # Import all folders
        quick_import_and_process("client_a")  # Import specific folder
    """
    # List folders first
    list_input_folders()

    # Import with auto-process
    result = import_from_folders(
        folder_name=folder_name,
        auto_process=True
    )

    if result and result.get('files_imported', 0) > 0:
        # Monitor until complete
        monitor_processing()
        show_results()

    return result


if __name__ == "__main__":
    main()
