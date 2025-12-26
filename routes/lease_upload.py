"""
Lease Upload routes for the Lease Clause Classifier API.
Handles PDF uploads with status tracking and batch processing.
"""

import os
import tempfile
import threading
import time
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId

from utils import log_success, log_error
from storage import (
    upload_to_azure_storage,
    download_from_azure_storage,
    save_to_local_storage,
    read_from_local_storage
)
from db import get_mongo_client, serialize_document

lease_upload_bp = Blueprint('lease_upload', __name__)

# Lease status constants
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_PROCESSED = "processed"
STATUS_FAILED = "failed"

# Collection name for lease uploads
LEASE_UPLOADS_COLLECTION = "lease_uploads"

# Batch processing configuration
BATCH_SIZE = 2  # Process 2 files at a time

# Default input folders path
DEFAULT_INPUT_FOLDERS_PATH = "input_folders"

# Lock for batch processing to ensure only one batch runs at a time
processing_lock = threading.Lock()
is_processing = False


def log_step(step_name, **kwargs):
    """Helper function to log processing steps with consistent formatting."""
    log_success(f"[STEP] {step_name}", **kwargs)


def log_step_error(step_name, **kwargs):
    """Helper function to log processing step errors with consistent formatting."""
    log_error(f"[STEP ERROR] {step_name}", **kwargs)


def get_lease_collection(config):
    """Get the lease uploads MongoDB collection."""
    log_step("Getting MongoDB collection", collection=LEASE_UPLOADS_COLLECTION)

    mongo_config = config.get("mongodb", {})
    mongo_uri = os.environ.get('MONGODB_URI') or mongo_config.get("uri", "")
    mongo_db = mongo_config.get("database", "")

    if not mongo_uri or not mongo_db:
        log_step_error("MongoDB configuration missing", has_uri=bool(mongo_uri), has_db=bool(mongo_db))
        return None, None

    client = get_mongo_client(mongo_uri)
    if client is None:
        log_step_error("Failed to get MongoDB client")
        return None, None

    db = client[mongo_db]
    collection = db[LEASE_UPLOADS_COLLECTION]
    log_step("MongoDB collection obtained successfully", database=mongo_db, collection=LEASE_UPLOADS_COLLECTION)
    return client, collection


@lease_upload_bp.route('/leases/upload', methods=['POST'])
def upload_lease():
    """
    Upload a lease PDF to storage and save metadata in the lease_uploads collection.

    Request:
        - Form data with 'pdf' file

    Response:
        JSON with upload details and lease ID.
    """
    try:
        log_step("Starting single lease upload", endpoint="/leases/upload")
        config = current_app.config.get('APP_CONFIG', {})

        # Step 1: Validate request
        log_step("Validating upload request")
        if 'pdf' not in request.files:
            log_step_error("No PDF file in request", endpoint="/leases/upload")
            return jsonify({"error": "No PDF file provided"}), 400

        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            log_step_error("Empty filename", endpoint="/leases/upload")
            return jsonify({"error": "No file selected"}), 400

        if not pdf_file.filename.lower().endswith('.pdf'):
            log_step_error("Invalid file type", endpoint="/leases/upload", filename=pdf_file.filename)
            return jsonify({"error": "File must be a PDF"}), 400

        original_filename = pdf_file.filename
        log_step("Request validated", filename=original_filename)

        # Step 2: Get storage configuration
        log_step("Loading storage configuration")
        storage_config = config.get("azure_storage", {})
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING') or storage_config.get("connection_string", "")
        container_name = storage_config.get("container_name", "lease-pdfs")
        local_config = config.get("local_storage", {})
        local_path = local_config.get("path", "mnt/cp-files")
        log_step("Storage configuration loaded",
                 has_azure=bool(connection_string),
                 local_path=local_path)

        # Step 3: Read file data
        log_step("Reading file data", filename=original_filename)
        file_data = pdf_file.read()
        file_size = len(file_data)
        log_step("File data read", filename=original_filename, size_bytes=file_size)

        # Step 4: Upload to storage
        log_step("Starting storage upload", filename=original_filename)
        storage_name = None
        storage_location = None
        storage_type = None

        if connection_string:
            log_step("Attempting Azure storage upload", filename=original_filename)
            storage_name, storage_location = upload_to_azure_storage(
                file_data, original_filename, connection_string, container_name
            )
            if storage_name:
                storage_type = "azure"
                log_step("Azure storage upload successful",
                         filename=original_filename,
                         storage_name=storage_name)

        if not storage_name:
            log_step("Attempting local storage upload", filename=original_filename)
            storage_name, storage_location = save_to_local_storage(
                file_data, original_filename, local_path
            )
            if storage_name:
                storage_type = "local"
                log_step("Local storage upload successful",
                         filename=original_filename,
                         storage_name=storage_name)

        if storage_name is None:
            log_step_error("All storage uploads failed", filename=original_filename)
            return jsonify({"error": "Failed to upload file"}), 500

        # Step 5: Save to MongoDB
        log_step("Saving lease metadata to MongoDB", filename=original_filename)
        client, collection = get_lease_collection(config)
        if collection is None:
            log_step_error("MongoDB not configured", endpoint="/leases/upload")
            return jsonify({"error": "Database not configured"}), 500

        try:
            lease_doc = {
                "original_filename": original_filename,
                "storage_name": storage_name,
                "storage_location": storage_location,
                "storage_type": storage_type,
                "status": STATUS_PENDING,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "processed_at": None,
                "result_id": None,
                "error_message": None
            }

            result = collection.insert_one(lease_doc)
            lease_id = str(result.inserted_id)
            log_step("Lease metadata saved to MongoDB",
                     lease_id=lease_id,
                     filename=original_filename,
                     status=STATUS_PENDING)

            log_step("Single lease upload completed successfully",
                     endpoint="/leases/upload",
                     lease_id=lease_id,
                     filename=original_filename,
                     storage_type=storage_type)

            return jsonify({
                "message": "Lease uploaded successfully",
                "lease_id": lease_id,
                "original_filename": original_filename,
                "storage_name": storage_name,
                "storage_type": storage_type,
                "status": STATUS_PENDING
            }), 201

        finally:
            if client:
                client.close()

    except Exception as e:
        log_step_error("Lease upload failed with exception", endpoint="/leases/upload", error=str(e))
        return jsonify({"error": str(e)}), 500


@lease_upload_bp.route('/leases/upload/batch', methods=['POST'])
def upload_leases_batch():
    """
    Upload multiple lease PDFs at once.

    Request:
        - Form data with multiple 'pdf' files

    Response:
        JSON with upload results for each file.
    """
    try:
        log_step("Starting batch lease upload", endpoint="/leases/upload/batch")
        config = current_app.config.get('APP_CONFIG', {})

        # Step 1: Validate request
        log_step("Validating batch upload request")
        if 'pdf' not in request.files:
            log_step_error("No PDF files in request", endpoint="/leases/upload/batch")
            return jsonify({"error": "No PDF files provided"}), 400

        pdf_files = request.files.getlist('pdf')
        if not pdf_files:
            log_step_error("Empty file list", endpoint="/leases/upload/batch")
            return jsonify({"error": "No files selected"}), 400

        log_step("Batch request validated", file_count=len(pdf_files))

        # Step 2: Get storage configuration
        log_step("Loading storage configuration for batch upload")
        storage_config = config.get("azure_storage", {})
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING') or storage_config.get("connection_string", "")
        container_name = storage_config.get("container_name", "lease-pdfs")
        local_config = config.get("local_storage", {})
        local_path = local_config.get("path", "mnt/cp-files")

        # Step 3: Get MongoDB collection
        log_step("Getting MongoDB collection for batch upload")
        client, collection = get_lease_collection(config)
        if collection is None:
            log_step_error("MongoDB not configured for batch upload", endpoint="/leases/upload/batch")
            return jsonify({"error": "Database not configured"}), 500

        results = []
        try:
            for idx, pdf_file in enumerate(pdf_files, 1):
                log_step(f"Processing file {idx}/{len(pdf_files)}", filename=pdf_file.filename)

                if pdf_file.filename == '':
                    log_step_error(f"File {idx}: Empty filename")
                    results.append({
                        "filename": "",
                        "success": False,
                        "error": "No file selected"
                    })
                    continue

                if not pdf_file.filename.lower().endswith('.pdf'):
                    log_step_error(f"File {idx}: Invalid file type", filename=pdf_file.filename)
                    results.append({
                        "filename": pdf_file.filename,
                        "success": False,
                        "error": "File must be a PDF"
                    })
                    continue

                # Read file data
                log_step(f"File {idx}: Reading file data", filename=pdf_file.filename)
                file_data = pdf_file.read()
                original_filename = pdf_file.filename

                # Upload to storage
                log_step(f"File {idx}: Uploading to storage", filename=original_filename)
                storage_name = None
                storage_location = None
                storage_type = None

                if connection_string:
                    storage_name, storage_location = upload_to_azure_storage(
                        file_data, original_filename, connection_string, container_name
                    )
                    if storage_name:
                        storage_type = "azure"
                        log_step(f"File {idx}: Azure upload successful", filename=original_filename)

                if not storage_name:
                    storage_name, storage_location = save_to_local_storage(
                        file_data, original_filename, local_path
                    )
                    if storage_name:
                        storage_type = "local"
                        log_step(f"File {idx}: Local upload successful", filename=original_filename)

                if storage_name is None:
                    log_step_error(f"File {idx}: Storage upload failed", filename=original_filename)
                    results.append({
                        "filename": original_filename,
                        "success": False,
                        "error": "Failed to upload file to storage"
                    })
                    continue

                # Save lease metadata
                log_step(f"File {idx}: Saving to MongoDB", filename=original_filename)
                lease_doc = {
                    "original_filename": original_filename,
                    "storage_name": storage_name,
                    "storage_location": storage_location,
                    "storage_type": storage_type,
                    "status": STATUS_PENDING,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "processed_at": None,
                    "result_id": None,
                    "error_message": None
                }

                insert_result = collection.insert_one(lease_doc)
                lease_id = str(insert_result.inserted_id)

                log_step(f"File {idx}: Upload complete",
                         filename=original_filename,
                         lease_id=lease_id)

                results.append({
                    "filename": original_filename,
                    "success": True,
                    "lease_id": lease_id,
                    "storage_name": storage_name,
                    "storage_type": storage_type,
                    "status": STATUS_PENDING
                })

            successful = sum(1 for r in results if r.get("success"))
            failed = len(results) - successful
            log_step("Batch upload completed",
                     endpoint="/leases/upload/batch",
                     total=len(results),
                     successful=successful,
                     failed=failed)

            return jsonify({
                "message": f"Uploaded {successful} of {len(results)} files",
                "total": len(results),
                "successful": successful,
                "results": results
            }), 201

        finally:
            if client:
                client.close()

    except Exception as e:
        log_step_error("Batch upload failed with exception", endpoint="/leases/upload/batch", error=str(e))
        return jsonify({"error": str(e)}), 500


@lease_upload_bp.route('/leases', methods=['GET'])
def get_leases():
    """
    Get all uploaded leases with optional filtering by status.

    Query params:
        - status: Filter by status (pending, processing, processed, failed)
        - page: Page number (default: 1)
        - limit: Items per page (default: 20)

    Response:
        JSON with list of leases and pagination info.
    """
    try:
        log_step("Getting leases list", endpoint="/leases")
        config = current_app.config.get('APP_CONFIG', {})

        status_filter = request.args.get('status', None)
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        skip = (page - 1) * limit

        log_step("Query parameters", status_filter=status_filter, page=page, limit=limit)

        client, collection = get_lease_collection(config)
        if collection is None:
            log_step_error("MongoDB not configured", endpoint="/leases")
            return jsonify({"error": "Database not configured"}), 500

        try:
            # Build query
            query = {}
            if status_filter:
                query["status"] = status_filter

            # Get total count
            log_step("Counting documents", query=str(query))
            total = collection.count_documents(query)

            # Get leases with pagination
            log_step("Fetching leases", skip=skip, limit=limit)
            leases = list(collection.find(query)
                         .sort("created_at", -1)
                         .skip(skip)
                         .limit(limit))

            # Serialize documents
            serialized_leases = [serialize_document(lease) for lease in leases]

            log_step("Leases retrieved successfully",
                     total=total,
                     returned=len(serialized_leases),
                     page=page)

            return jsonify({
                "leases": serialized_leases,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }), 200

        finally:
            if client:
                client.close()

    except Exception as e:
        log_step_error("Get leases failed", endpoint="/leases", error=str(e))
        return jsonify({"error": str(e)}), 500


@lease_upload_bp.route('/leases/<lease_id>', methods=['GET'])
def get_lease(lease_id):
    """
    Get a specific lease by ID.

    Response:
        JSON with lease details.
    """
    try:
        log_step("Getting lease by ID", lease_id=lease_id)
        config = current_app.config.get('APP_CONFIG', {})

        client, collection = get_lease_collection(config)
        if collection is None:
            log_step_error("MongoDB not configured", endpoint=f"/leases/{lease_id}")
            return jsonify({"error": "Database not configured"}), 500

        try:
            log_step("Querying lease from MongoDB", lease_id=lease_id)
            try:
                lease = collection.find_one({"_id": ObjectId(lease_id)})
            except Exception:
                lease = collection.find_one({"_id": lease_id})

            if not lease:
                log_step_error("Lease not found", lease_id=lease_id)
                return jsonify({"error": "Lease not found"}), 404

            log_step("Lease retrieved successfully", lease_id=lease_id, status=lease.get("status"))
            return jsonify(serialize_document(lease)), 200

        finally:
            if client:
                client.close()

    except Exception as e:
        log_step_error("Get lease failed", endpoint=f"/leases/{lease_id}", error=str(e))
        return jsonify({"error": str(e)}), 500


@lease_upload_bp.route('/leases/<lease_id>', methods=['DELETE'])
def delete_lease(lease_id):
    """
    Delete a lease upload record.

    Response:
        JSON with deletion confirmation.
    """
    try:
        log_step("Deleting lease", lease_id=lease_id)
        config = current_app.config.get('APP_CONFIG', {})

        client, collection = get_lease_collection(config)
        if collection is None:
            log_step_error("MongoDB not configured", endpoint=f"/leases/{lease_id}")
            return jsonify({"error": "Database not configured"}), 500

        try:
            log_step("Executing delete operation", lease_id=lease_id)
            try:
                result = collection.delete_one({"_id": ObjectId(lease_id)})
            except Exception:
                result = collection.delete_one({"_id": lease_id})

            if result.deleted_count == 0:
                log_step_error("Lease not found for deletion", lease_id=lease_id)
                return jsonify({"error": "Lease not found"}), 404

            log_step("Lease deleted successfully", lease_id=lease_id)
            return jsonify({"message": "Lease deleted successfully"}), 200

        finally:
            if client:
                client.close()

    except Exception as e:
        log_step_error("Delete lease failed", endpoint=f"/leases/{lease_id}", error=str(e))
        return jsonify({"error": str(e)}), 500


@lease_upload_bp.route('/leases/process', methods=['POST'])
def trigger_processing():
    """
    Trigger batch processing of pending leases.
    Processes 2 files at a time, waits for completion, then processes next 2.

    Response:
        JSON with processing status.
    """
    global is_processing

    try:
        log_step("Processing trigger requested", endpoint="/leases/process")
        config = current_app.config.get('APP_CONFIG', {})
        process_pdf = current_app.config.get('PROCESS_PDF_FUNC')

        # Check if already processing
        if is_processing:
            log_step("Processing already in progress, skipping")
            return jsonify({
                "message": "Processing already in progress",
                "status": "running"
            }), 200

        client, collection = get_lease_collection(config)
        if collection is None:
            log_step_error("MongoDB not configured", endpoint="/leases/process")
            return jsonify({"error": "Database not configured"}), 500

        try:
            # Count pending leases
            log_step("Counting pending leases")
            pending_count = collection.count_documents({"status": STATUS_PENDING})
            log_step("Pending lease count", count=pending_count)

            if pending_count == 0:
                log_step("No pending leases to process")
                return jsonify({
                    "message": "No pending leases to process",
                    "pending": 0
                }), 200

            # Start background processing
            log_step("Starting background processing thread",
                     pending_count=pending_count,
                     batch_size=BATCH_SIZE)
            app = current_app._get_current_object()
            thread = threading.Thread(
                target=process_leases_batch,
                args=(app, config, process_pdf)
            )
            thread.daemon = True
            thread.start()

            log_step("Processing started successfully",
                     endpoint="/leases/process",
                     pending=pending_count,
                     batch_size=BATCH_SIZE)

            return jsonify({
                "message": "Processing started",
                "pending": pending_count,
                "batch_size": BATCH_SIZE
            }), 202

        finally:
            if client:
                client.close()

    except Exception as e:
        log_step_error("Processing trigger failed", endpoint="/leases/process", error=str(e))
        return jsonify({"error": str(e)}), 500


@lease_upload_bp.route('/leases/process/status', methods=['GET'])
def get_processing_status():
    """
    Get the current processing status.

    Response:
        JSON with processing status and counts.
    """
    global is_processing

    try:
        log_step("Getting processing status", endpoint="/leases/process/status")
        config = current_app.config.get('APP_CONFIG', {})

        client, collection = get_lease_collection(config)
        if collection is None:
            return jsonify({"error": "Database not configured"}), 500

        try:
            log_step("Counting leases by status")
            pending = collection.count_documents({"status": STATUS_PENDING})
            processing = collection.count_documents({"status": STATUS_PROCESSING})
            processed = collection.count_documents({"status": STATUS_PROCESSED})
            failed = collection.count_documents({"status": STATUS_FAILED})

            log_step("Status counts retrieved",
                     is_processing=is_processing,
                     pending=pending,
                     processing=processing,
                     processed=processed,
                     failed=failed)

            return jsonify({
                "is_processing": is_processing,
                "counts": {
                    "pending": pending,
                    "processing": processing,
                    "processed": processed,
                    "failed": failed,
                    "total": pending + processing + processed + failed
                }
            }), 200

        finally:
            if client:
                client.close()

    except Exception as e:
        log_step_error("Get processing status failed", endpoint="/leases/process/status", error=str(e))
        return jsonify({"error": str(e)}), 500


@lease_upload_bp.route('/leases/import-from-folders', methods=['POST'])
def import_from_folders():
    """
    Import PDF files from folders placed inside the input_folders directory.
    Scans all subfolders recursively and uploads any PDF files found.

    Request JSON (optional):
        {
            "input_path": "custom/path/to/input_folders",  # Optional, defaults to "input_folders"
            "folder_name": "specific_folder",  # Optional, process only this subfolder
            "auto_process": true  # Optional, automatically trigger processing after import
        }

    Response:
        JSON with import results.
    """
    try:
        log_step("Starting import from folders", endpoint="/leases/import-from-folders")
        config = current_app.config.get('APP_CONFIG', {})

        # Step 1: Parse request data
        log_step("Parsing request data")
        data = request.get_json() or {}
        input_path = data.get('input_path', DEFAULT_INPUT_FOLDERS_PATH)
        folder_name = data.get('folder_name', None)
        auto_process = data.get('auto_process', False)

        log_step("Request parameters",
                 input_path=input_path,
                 folder_name=folder_name,
                 auto_process=auto_process)

        # Step 2: Resolve and validate path
        log_step("Resolving input path")
        if not os.path.isabs(input_path):
            input_path = os.path.join(os.getcwd(), input_path)
        log_step("Resolved input path", path=input_path)

        if not os.path.exists(input_path):
            log_step_error("Input directory not found", path=input_path)
            return jsonify({
                "error": f"Input folders directory not found: {input_path}",
                "hint": "Create the 'input_folders' directory and place folders containing PDF files inside it."
            }), 404

        if not os.path.isdir(input_path):
            log_step_error("Path is not a directory", path=input_path)
            return jsonify({"error": f"Path is not a directory: {input_path}"}), 400

        # Step 3: Get storage configuration
        log_step("Loading storage configuration")
        storage_config = config.get("azure_storage", {})
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING') or storage_config.get("connection_string", "")
        container_name = storage_config.get("container_name", "lease-pdfs")
        local_config = config.get("local_storage", {})
        local_path = local_config.get("path", "mnt/cp-files")
        log_step("Storage configuration loaded", has_azure=bool(connection_string))

        # Step 4: Get MongoDB collection
        log_step("Getting MongoDB collection")
        client, collection = get_lease_collection(config)
        if collection is None:
            log_step_error("MongoDB not configured", endpoint="/leases/import-from-folders")
            return jsonify({"error": "Database not configured"}), 500

        try:
            results = {
                "folders_scanned": [],
                "files_found": 0,
                "files_imported": 0,
                "files_skipped": 0,
                "files_failed": 0,
                "details": []
            }

            # Step 5: Determine folders to scan
            log_step("Determining folders to scan")
            if folder_name:
                folder_path = os.path.join(input_path, folder_name)
                if not os.path.exists(folder_path):
                    log_step_error("Specified folder not found", folder=folder_name)
                    return jsonify({"error": f"Folder not found: {folder_name}"}), 404
                folders_to_scan = [(folder_name, folder_path)]
                log_step("Scanning specific folder", folder=folder_name)
            else:
                folders_to_scan = []
                for item in os.listdir(input_path):
                    item_path = os.path.join(input_path, item)
                    if os.path.isdir(item_path):
                        folders_to_scan.append((item, item_path))
                log_step("Found folders to scan", count=len(folders_to_scan))

            if not folders_to_scan:
                log_step("No folders found in input directory")
                return jsonify({
                    "message": "No folders found in input_folders directory",
                    "input_path": input_path,
                    **results
                }), 200

            # Step 6: Process each folder
            for folder_idx, (current_folder_name, folder_path) in enumerate(folders_to_scan, 1):
                log_step(f"Processing folder {folder_idx}/{len(folders_to_scan)}",
                         folder=current_folder_name)
                results["folders_scanned"].append(current_folder_name)

                # Find all PDF files recursively
                log_step("Scanning for PDF files", folder=current_folder_name)
                pdf_files = []
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            pdf_files.append(os.path.join(root, file))

                log_step("PDF files found in folder",
                         folder=current_folder_name,
                         count=len(pdf_files))
                results["files_found"] += len(pdf_files)

                # Process each PDF file
                for file_idx, pdf_path in enumerate(pdf_files, 1):
                    relative_path = os.path.relpath(pdf_path, input_path)
                    original_filename = os.path.basename(pdf_path)

                    log_step(f"Processing file {file_idx}/{len(pdf_files)} in {current_folder_name}",
                             file=relative_path)

                    try:
                        # Check if file already imported
                        log_step("Checking if file already imported", file=relative_path)
                        existing = collection.find_one({
                            "source_path": pdf_path,
                            "status": {"$in": [STATUS_PENDING, STATUS_PROCESSING, STATUS_PROCESSED]}
                        })

                        if existing:
                            log_step("File already imported, skipping",
                                     file=relative_path,
                                     existing_id=str(existing["_id"]))
                            results["files_skipped"] += 1
                            results["details"].append({
                                "file": relative_path,
                                "status": "skipped",
                                "reason": "Already imported",
                                "existing_id": str(existing["_id"])
                            })
                            continue

                        # Read file data
                        log_step("Reading file data", file=relative_path)
                        with open(pdf_path, 'rb') as f:
                            file_data = f.read()
                        log_step("File data read", file=relative_path, size_bytes=len(file_data))

                        # Upload to storage
                        log_step("Uploading to storage", file=relative_path)
                        storage_name = None
                        storage_location = None
                        storage_type = None

                        if connection_string:
                            log_step("Attempting Azure upload", file=relative_path)
                            storage_name, storage_location = upload_to_azure_storage(
                                file_data, original_filename, connection_string, container_name
                            )
                            if storage_name:
                                storage_type = "azure"
                                log_step("Azure upload successful", file=relative_path)

                        if not storage_name:
                            log_step("Attempting local storage upload", file=relative_path)
                            storage_name, storage_location = save_to_local_storage(
                                file_data, original_filename, local_path
                            )
                            if storage_name:
                                storage_type = "local"
                                log_step("Local storage upload successful", file=relative_path)

                        if not storage_name:
                            log_step_error("Storage upload failed", file=relative_path)
                            results["files_failed"] += 1
                            results["details"].append({
                                "file": relative_path,
                                "status": "failed",
                                "reason": "Storage upload failed"
                            })
                            continue

                        # Save lease metadata to MongoDB
                        log_step("Saving to MongoDB", file=relative_path)
                        lease_doc = {
                            "original_filename": original_filename,
                            "source_path": pdf_path,
                            "source_folder": current_folder_name,
                            "storage_name": storage_name,
                            "storage_location": storage_location,
                            "storage_type": storage_type,
                            "status": STATUS_PENDING,
                            "created_at": datetime.now(timezone.utc),
                            "updated_at": datetime.now(timezone.utc),
                            "processed_at": None,
                            "result_id": None,
                            "error_message": None
                        }

                        insert_result = collection.insert_one(lease_doc)
                        lease_id = str(insert_result.inserted_id)

                        log_step("File imported successfully",
                                 file=relative_path,
                                 lease_id=lease_id,
                                 storage_type=storage_type)

                        results["files_imported"] += 1
                        results["details"].append({
                            "file": relative_path,
                            "status": "imported",
                            "lease_id": lease_id,
                            "storage_type": storage_type
                        })

                    except Exception as e:
                        log_step_error("File import failed", file=relative_path, error=str(e))
                        results["files_failed"] += 1
                        results["details"].append({
                            "file": relative_path,
                            "status": "failed",
                            "reason": str(e)
                        })

            # Step 7: Log summary
            log_step("Import from folders completed",
                     endpoint="/leases/import-from-folders",
                     folders_scanned=len(results["folders_scanned"]),
                     files_found=results["files_found"],
                     files_imported=results["files_imported"],
                     files_skipped=results["files_skipped"],
                     files_failed=results["files_failed"])

            response_data = {
                "message": f"Import completed: {results['files_imported']} files imported",
                "input_path": input_path,
                **results
            }

            # Step 8: Auto-trigger processing if requested
            if auto_process and results["files_imported"] > 0:
                log_step("Auto-processing requested, starting processing")
                process_pdf = current_app.config.get('PROCESS_PDF_FUNC')
                if process_pdf and not is_processing:
                    app = current_app._get_current_object()
                    thread = threading.Thread(
                        target=process_leases_batch,
                        args=(app, config, process_pdf)
                    )
                    thread.daemon = True
                    thread.start()
                    response_data["processing_started"] = True
                    log_step("Auto-processing started")
                else:
                    response_data["processing_started"] = False
                    response_data["processing_note"] = "Processing already in progress" if is_processing else "Process function not available"
                    log_step("Auto-processing not started", reason=response_data["processing_note"])

            return jsonify(response_data), 200

        finally:
            if client:
                client.close()

    except Exception as e:
        log_step_error("Import from folders failed", endpoint="/leases/import-from-folders", error=str(e))
        return jsonify({"error": str(e)}), 500


@lease_upload_bp.route('/leases/folders', methods=['GET'])
def list_input_folders():
    """
    List all folders inside the input_folders directory.

    Query params:
        - input_path: Custom path to input_folders (optional)

    Response:
        JSON with list of folders and their PDF file counts.
    """
    try:
        log_step("Listing input folders", endpoint="/leases/folders")
        input_path = request.args.get('input_path', DEFAULT_INPUT_FOLDERS_PATH)

        # Resolve absolute path
        log_step("Resolving path", input_path=input_path)
        if not os.path.isabs(input_path):
            input_path = os.path.join(os.getcwd(), input_path)

        if not os.path.exists(input_path):
            log_step_error("Input directory not found", path=input_path)
            return jsonify({
                "error": f"Input folders directory not found: {input_path}",
                "hint": "Create the 'input_folders' directory and place folders containing PDF files inside it."
            }), 404

        if not os.path.isdir(input_path):
            log_step_error("Path is not a directory", path=input_path)
            return jsonify({"error": f"Path is not a directory: {input_path}"}), 400

        log_step("Scanning folders", path=input_path)
        folders = []
        total_pdfs = 0

        for item in os.listdir(input_path):
            item_path = os.path.join(input_path, item)
            if os.path.isdir(item_path):
                # Count PDF files recursively
                pdf_count = 0
                for root, dirs, files in os.walk(item_path):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            pdf_count += 1

                log_step("Folder scanned", folder=item, pdf_count=pdf_count)
                folders.append({
                    "name": item,
                    "path": item_path,
                    "pdf_count": pdf_count
                })
                total_pdfs += pdf_count

        log_step("Folder listing complete",
                 total_folders=len(folders),
                 total_pdf_files=total_pdfs)

        return jsonify({
            "input_path": input_path,
            "total_folders": len(folders),
            "total_pdf_files": total_pdfs,
            "folders": folders
        }), 200

    except Exception as e:
        log_step_error("List input folders failed", endpoint="/leases/folders", error=str(e))
        return jsonify({"error": str(e)}), 500


def process_leases_batch(app, config, process_pdf_func):
    """
    Background task to process pending leases in batches of 2.
    """
    global is_processing

    log_step("Background batch processing started")

    with processing_lock:
        if is_processing:
            log_step("Processing already in progress, exiting thread")
            return
        is_processing = True
        log_step("Processing lock acquired")

    batch_number = 0
    total_processed = 0
    total_failed = 0

    try:
        with app.app_context():
            while True:
                batch_number += 1
                log_step(f"Starting batch {batch_number}", batch_size=BATCH_SIZE)

                client, collection = get_lease_collection(config)
                if collection is None:
                    log_step_error("MongoDB not configured, stopping batch processing")
                    break

                try:
                    # Get next batch of pending leases
                    log_step(f"Batch {batch_number}: Fetching pending leases")
                    pending_leases = list(collection.find({"status": STATUS_PENDING})
                                         .sort("created_at", 1)
                                         .limit(BATCH_SIZE))

                    if not pending_leases:
                        log_step("No more pending leases, batch processing complete",
                                total_batches=batch_number - 1,
                                total_processed=total_processed,
                                total_failed=total_failed)
                        break

                    log_step(f"Batch {batch_number}: Processing {len(pending_leases)} leases")

                    # Update status to processing for this batch
                    lease_ids = [lease["_id"] for lease in pending_leases]
                    log_step(f"Batch {batch_number}: Updating status to 'processing'",
                             lease_count=len(lease_ids))

                    collection.update_many(
                        {"_id": {"$in": lease_ids}},
                        {"$set": {
                            "status": STATUS_PROCESSING,
                            "updated_at": datetime.now(timezone.utc)
                        }}
                    )

                    # Process each lease in the batch
                    for idx, lease in enumerate(pending_leases, 1):
                        log_step(f"Batch {batch_number}: Processing lease {idx}/{len(pending_leases)}",
                                 lease_id=str(lease["_id"]),
                                 filename=lease.get("original_filename"))

                        success = process_single_lease(lease, collection, config, process_pdf_func)
                        if success:
                            total_processed += 1
                        else:
                            total_failed += 1

                    log_step(f"Batch {batch_number} complete",
                             processed_in_batch=len(pending_leases),
                             total_processed=total_processed,
                             total_failed=total_failed)

                finally:
                    if client:
                        client.close()

                # Small delay between batches
                log_step(f"Waiting before next batch")
                time.sleep(1)

    except Exception as e:
        log_step_error("Batch processing failed with exception", error=str(e))
    finally:
        is_processing = False
        log_step("Background batch processing finished",
                 total_batches=batch_number,
                 total_processed=total_processed,
                 total_failed=total_failed)


def process_single_lease(lease, collection, config, process_pdf_func):
    """
    Process a single lease PDF.
    Returns True if successful, False otherwise.
    """
    lease_id = lease["_id"]
    storage_name = lease["storage_name"]
    storage_type = lease["storage_type"]
    original_filename = lease["original_filename"]

    log_step("Processing single lease",
             lease_id=str(lease_id),
             filename=original_filename,
             storage_type=storage_type)

    try:
        # Step 1: Get storage settings
        log_step("Getting storage settings", lease_id=str(lease_id))
        storage_config = config.get("azure_storage", {})
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING') or storage_config.get("connection_string", "")
        container_name = storage_config.get("container_name", "lease-pdfs")
        local_config = config.get("local_storage", {})
        local_path = local_config.get("path", "mnt/cp-files")

        # Step 2: Download file from storage
        log_step("Downloading file from storage",
                 lease_id=str(lease_id),
                 storage_type=storage_type,
                 storage_name=storage_name)

        file_data = None
        if storage_type == "azure":
            file_data = download_from_azure_storage(storage_name, connection_string, container_name)
        elif storage_type == "local":
            file_data = read_from_local_storage(storage_name, local_path)

        if not file_data:
            raise Exception(f"Failed to download file from {storage_type} storage")

        log_step("File downloaded successfully",
                 lease_id=str(lease_id),
                 size_bytes=len(file_data))

        # Step 3: Save to temp file for processing
        log_step("Creating temporary file for processing", lease_id=str(lease_id))
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name
        log_step("Temporary file created", lease_id=str(lease_id), temp_path=tmp_path)

        try:
            # Step 4: Process PDF
            log_step("Starting PDF processing", lease_id=str(lease_id), filename=original_filename)
            result = process_pdf_func(tmp_path, extract_fields_enabled=True)
            log_step("PDF processing complete",
                     lease_id=str(lease_id),
                     clauses_found=result.get("total_clauses", 0),
                     fields_found=result.get("total_fields", 0))

            # Step 5: Add file info to result
            result["pdf_file"] = original_filename
            result["storage_type"] = storage_type
            result["storage_name"] = storage_name
            result["lease_upload_id"] = str(lease_id)

            # Step 6: Save result to cube_outputs collection
            log_step("Saving results to cube_outputs", lease_id=str(lease_id))
            mongo_config = config.get("mongodb", {})
            mongo_uri = os.environ.get('MONGODB_URI') or mongo_config.get("uri", "")
            mongo_db = mongo_config.get("database", "")
            mongo_collection = mongo_config.get("collection", "cube_outputs")

            result_id = None
            if mongo_uri and mongo_db:
                from db import save_to_mongodb
                result_id = save_to_mongodb(result.copy(), mongo_uri, mongo_db, mongo_collection)
                log_step("Results saved to cube_outputs",
                         lease_id=str(lease_id),
                         result_id=result_id)

            # Step 7: Update lease status to processed
            log_step("Updating lease status to 'processed'", lease_id=str(lease_id))
            collection.update_one(
                {"_id": lease_id},
                {"$set": {
                    "status": STATUS_PROCESSED,
                    "updated_at": datetime.now(timezone.utc),
                    "processed_at": datetime.now(timezone.utc),
                    "result_id": result_id,
                    "error_message": None
                }}
            )

            log_step("Lease processed successfully",
                     lease_id=str(lease_id),
                     filename=original_filename,
                     result_id=result_id)
            return True

        finally:
            # Clean up temp file
            log_step("Cleaning up temporary file", lease_id=str(lease_id))
            os.unlink(tmp_path)

    except Exception as e:
        log_step_error("Lease processing failed",
                       lease_id=str(lease_id),
                       filename=original_filename,
                       error=str(e))

        # Update lease status to failed
        log_step("Updating lease status to 'failed'", lease_id=str(lease_id))
        collection.update_one(
            {"_id": lease_id},
            {"$set": {
                "status": STATUS_FAILED,
                "updated_at": datetime.now(timezone.utc),
                "error_message": str(e)
            }}
        )
        return False
