"""
Storage functions for the Lease Clause Classifier API.
Handles Azure Blob Storage and local file storage operations.
"""

import os
import uuid
from pathlib import Path

from utils import log_success, log_error


def upload_to_azure_storage(file_data, filename, connection_string, container_name):
    """
    Upload PDF file to Azure Blob Storage.

    Args:
        file_data: File bytes to upload.
        filename: Original filename.
        connection_string: Azure Storage connection string.
        container_name: Blob container name.

    Returns:
        Tuple of (blob_name, blob_url) or (None, None) if failed.
    """
    try:
        log_success("Uploading to Azure Storage", filename=filename, container=container_name)
        from azure.storage.blob import BlobServiceClient

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        # Create container if not exists
        try:
            container_client.create_container()
        except Exception:
            pass  # Container already exists

        # Generate unique blob name
        blob_name = f"{uuid.uuid4()}_{filename}"
        blob_client = container_client.get_blob_client(blob_name)

        # Upload file
        blob_client.upload_blob(file_data, overwrite=True)

        log_success("Azure Storage upload successful", blob_name=blob_name, container=container_name)
        return blob_name, blob_client.url

    except ImportError as e:
        log_error("Azure Storage library not installed", error=str(e))
        return None, None
    except Exception as e:
        log_error("Azure Storage upload failed", container=container_name, error=str(e))
        return None, None


def download_from_azure_storage(blob_name, connection_string, container_name):
    """
    Download PDF file from Azure Blob Storage.

    Args:
        blob_name: Name of the blob to download.
        connection_string: Azure Storage connection string.
        container_name: Blob container name.

    Returns:
        File bytes or None if failed.
    """
    try:
        log_success("Downloading from Azure Storage", blob_name=blob_name, container=container_name)
        from azure.storage.blob import BlobServiceClient

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container_name, blob_name)

        data = blob_client.download_blob().readall()
        log_success("Azure Storage download successful", blob_name=blob_name)
        return data

    except ImportError as e:
        log_error("Azure Storage library not installed", error=str(e))
        return None
    except Exception as e:
        log_error("Azure Storage download failed", blob_name=blob_name, container=container_name, error=str(e))
        return None


def save_to_local_storage(file_data, filename, local_path):
    """
    Save PDF file to local storage.

    Args:
        file_data: File bytes to save.
        filename: Original filename.
        local_path: Local storage directory path.

    Returns:
        Tuple of (file_name, file_path) or (None, None) if failed.
    """
    try:
        log_success("Saving to local storage", filename=filename, path=local_path)

        # Create directory if not exists
        storage_dir = Path(local_path)
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        unique_name = f"{uuid.uuid4()}_{filename}"
        file_path = storage_dir / unique_name

        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_data)

        log_success("Local storage save successful", filename=unique_name, path=local_path)
        return unique_name, str(file_path.absolute())

    except PermissionError as e:
        log_error("Permission denied saving to local storage", path=local_path, error=str(e))
        return None, None
    except Exception as e:
        log_error("Local storage save failed", path=local_path, error=str(e))
        return None, None


def read_from_local_storage(file_name, local_path):
    """
    Read PDF file from local storage.

    Args:
        file_name: Name of the file to read.
        local_path: Local storage directory path.

    Returns:
        File bytes or None if failed.
    """
    try:
        log_success("Reading from local storage", filename=file_name, path=local_path)
        file_path = Path(local_path) / file_name

        if not file_path.exists():
            log_error("File not found in local storage", filename=file_name, path=local_path)
            return None

        with open(file_path, 'rb') as f:
            data = f.read()

        log_success("Local storage read successful", filename=file_name)
        return data

    except PermissionError as e:
        log_error("Permission denied reading from local storage", filename=file_name, path=local_path, error=str(e))
        return None
    except Exception as e:
        log_error("Local storage read failed", filename=file_name, path=local_path, error=str(e))
        return None
