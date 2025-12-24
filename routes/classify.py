"""
Classification routes for the Lease Clause Classifier API.
"""

import os
import tempfile

from flask import Blueprint, request, jsonify, current_app

from utils import log_success, log_error
from storage import (
    upload_to_azure_storage,
    download_from_azure_storage,
    save_to_local_storage,
    read_from_local_storage
)
from db import save_to_mongodb

classify_bp = Blueprint('classify', __name__)


@classify_bp.route('/classify', methods=['POST'])
def classify_pdf():
    """
    Classify lease clauses from uploaded PDF.

    Request:
        - Form data with 'pdf' file
        - Optional query params: gpt_model (gpt-4.1 or gpt-5), no_fields (true/false)

    Response:
        JSON with classification results including clauses and extracted fields.
    """
    try:
        config = current_app.config.get('APP_CONFIG', {})
        process_pdf = current_app.config.get('PROCESS_PDF_FUNC')

        # Check if PDF file is in request
        if 'pdf' not in request.files:
            log_error("Classification failed - No PDF file provided", endpoint="/classify")
            return jsonify({"error": "No PDF file provided"}), 400

        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            log_error("Classification failed - No file selected", endpoint="/classify")
            return jsonify({"error": "No file selected"}), 400

        if not pdf_file.filename.lower().endswith('.pdf'):
            log_error("Classification failed - Invalid file type", endpoint="/classify", filename=pdf_file.filename)
            return jsonify({"error": "File must be a PDF"}), 400

        # Get options
        gpt_model = request.args.get('gpt_model', None)
        no_fields = request.args.get('no_fields', 'false').lower() == 'true'

        # Azure Storage settings
        storage_config = config.get("azure_storage", {})
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING') or storage_config.get("connection_string", "")
        container_name = storage_config.get("container_name", "lease-pdfs")

        # Local storage settings (fallback)
        local_config = config.get("local_storage", {})
        local_path = local_config.get("path", "mnt/cp-files")

        # Read file data
        file_data = pdf_file.read()
        original_filename = pdf_file.filename

        # Upload to Azure Storage if configured, otherwise use local storage
        storage_name = None
        storage_location = None
        storage_type = None

        if connection_string:
            storage_name, storage_location = upload_to_azure_storage(
                file_data, original_filename, connection_string, container_name
            )
            if storage_name:
                storage_type = "azure"

        # Fallback to local storage if Azure not configured or failed
        if not storage_name:
            storage_name, storage_location = save_to_local_storage(
                file_data, original_filename, local_path
            )
            if storage_name:
                storage_type = "local"

        # Save to temp file for processing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name

        try:
            # Process PDF
            result = process_pdf(tmp_path, gpt_model=gpt_model, extract_fields_enabled=not no_fields)

            # Add file info
            result["pdf_file"] = original_filename
            result["storage_type"] = storage_type
            if storage_name:
                result["storage_name"] = storage_name
            if storage_location:
                result["storage_location"] = storage_location

            # Save to MongoDB if configured
            mongo_config = config.get("mongodb", {})
            mongo_uri = os.environ.get('MONGODB_URI') or mongo_config.get("uri", "")
            mongo_db = mongo_config.get("database", "")
            mongo_collection = mongo_config.get("collection", "cube_outputs")

            if mongo_uri and mongo_db:
                mongo_id = save_to_mongodb(result.copy(), mongo_uri, mongo_db, mongo_collection)
                if mongo_id:
                    result["_id"] = mongo_id
                    log_success("MongoDB save successful", endpoint="/classify", mongo_id=mongo_id)

            log_success("Classification successful", endpoint="/classify", filename=original_filename,
                       clauses=result.get("total_clauses", 0), fields=result.get("total_fields", 0),
                       storage_type=storage_type)
            return jsonify(result), 200

        finally:
            # Clean up temp file
            os.unlink(tmp_path)

    except Exception as e:
        log_error("Classification failed", endpoint="/classify", error=str(e))
        return jsonify({"error": str(e)}), 500


@classify_bp.route('/classify/file', methods=['POST'])
def classify_from_storage():
    """
    Classify lease clauses from PDF stored in Azure Blob Storage or local storage.

    Request JSON:
        {
            "file_name": "name of the file in storage",
            "storage_type": "azure" or "local" (optional, auto-detects if not provided),
            "gpt_model": "gpt-4.1" or "gpt-5" (optional),
            "no_fields": false (optional)
        }

    Response:
        JSON with classification results.
    """
    try:
        config = current_app.config.get('APP_CONFIG', {})
        process_pdf = current_app.config.get('PROCESS_PDF_FUNC')

        data = request.get_json()
        if not data or 'file_name' not in data:
            log_error("Classification from storage failed - file_name required", endpoint="/classify/file")
            return jsonify({"error": "file_name is required"}), 400

        file_name = data['file_name']
        storage_type = data.get('storage_type', None)
        gpt_model = data.get('gpt_model', None)
        no_fields = data.get('no_fields', False)

        # Azure Storage settings
        storage_config = config.get("azure_storage", {})
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING') or storage_config.get("connection_string", "")
        container_name = storage_config.get("container_name", "lease-pdfs")

        # Local storage settings
        local_config = config.get("local_storage", {})
        local_path = local_config.get("path", "mnt/cp-files")

        file_data = None
        actual_storage_type = None

        # Try Azure first if specified or auto-detect
        if storage_type == "azure" or (storage_type is None and connection_string):
            file_data = download_from_azure_storage(file_name, connection_string, container_name)
            if file_data:
                actual_storage_type = "azure"

        # Try local storage if Azure failed or local specified
        if file_data is None and (storage_type == "local" or storage_type is None):
            file_data = read_from_local_storage(file_name, local_path)
            if file_data:
                actual_storage_type = "local"

        if file_data is None:
            log_error("Classification from storage failed - File not found", endpoint="/classify/file", filename=file_name)
            return jsonify({"error": f"File not found: {file_name}"}), 404

        # Save to temp file for processing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name

        try:
            # Process PDF
            result = process_pdf(tmp_path, gpt_model=gpt_model, extract_fields_enabled=not no_fields)

            # Add file info
            result["storage_name"] = file_name
            result["storage_type"] = actual_storage_type

            # Save to MongoDB if configured
            mongo_config = config.get("mongodb", {})
            mongo_uri = os.environ.get('MONGODB_URI') or mongo_config.get("uri", "")
            mongo_db = mongo_config.get("database", "")
            mongo_collection = mongo_config.get("collection", "cube_outputs")

            if mongo_uri and mongo_db:
                mongo_id = save_to_mongodb(result.copy(), mongo_uri, mongo_db, mongo_collection)
                if mongo_id:
                    result["_id"] = mongo_id
                    log_success("MongoDB save successful", endpoint="/classify/file", mongo_id=mongo_id)

            log_success("Classification from storage successful", endpoint="/classify/file", filename=file_name,
                       clauses=result.get("total_clauses", 0), fields=result.get("total_fields", 0),
                       storage_type=actual_storage_type)
            return jsonify(result), 200

        finally:
            # Clean up temp file
            os.unlink(tmp_path)

    except Exception as e:
        log_error("Classification from storage failed", endpoint="/classify/file", error=str(e))
        return jsonify({"error": str(e)}), 500


@classify_bp.route('/upload', methods=['POST'])
def upload_pdf():
    """
    Upload PDF to Azure Blob Storage or local storage.

    Request:
        - Form data with 'pdf' file

    Response:
        JSON with storage name and location.
    """
    try:
        config = current_app.config.get('APP_CONFIG', {})

        if 'pdf' not in request.files:
            log_error("Upload failed - No PDF file provided", endpoint="/upload")
            return jsonify({"error": "No PDF file provided"}), 400

        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            log_error("Upload failed - No file selected", endpoint="/upload")
            return jsonify({"error": "No file selected"}), 400

        if not pdf_file.filename.lower().endswith('.pdf'):
            log_error("Upload failed - Invalid file type", endpoint="/upload", filename=pdf_file.filename)
            return jsonify({"error": "File must be a PDF"}), 400

        # Azure Storage settings
        storage_config = config.get("azure_storage", {})
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING') or storage_config.get("connection_string", "")
        container_name = storage_config.get("container_name", "lease-pdfs")

        # Local storage settings (fallback)
        local_config = config.get("local_storage", {})
        local_path = local_config.get("path", "mnt/cp-files")

        # Read file data
        file_data = pdf_file.read()

        # Upload to Azure Storage if configured, otherwise use local storage
        storage_name = None
        storage_location = None
        storage_type = None

        if connection_string:
            storage_name, storage_location = upload_to_azure_storage(
                file_data, pdf_file.filename, connection_string, container_name
            )
            if storage_name:
                storage_type = "azure"

        # Fallback to local storage if Azure not configured or failed
        if not storage_name:
            storage_name, storage_location = save_to_local_storage(
                file_data, pdf_file.filename, local_path
            )
            if storage_name:
                storage_type = "local"

        if storage_name is None:
            log_error("Upload failed - Storage save failed", endpoint="/upload", filename=pdf_file.filename)
            return jsonify({"error": "Failed to upload file"}), 500

        log_success("Upload successful", endpoint="/upload", filename=pdf_file.filename,
                   storage_name=storage_name, storage_type=storage_type)
        return jsonify({
            "message": "PDF uploaded successfully",
            "storage_name": storage_name,
            "storage_location": storage_location,
            "storage_type": storage_type,
            "original_filename": pdf_file.filename
        }), 200

    except Exception as e:
        log_error("Upload failed", endpoint="/upload", error=str(e))
        return jsonify({"error": str(e)}), 500
