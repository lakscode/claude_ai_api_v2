"""
Lease Clause Classifier API
Flask REST API for classifying lease clauses from PDF files.
Supports Azure Blob Storage for PDF storage and MongoDB for output storage.
"""

import os
import json
import uuid
import tempfile
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from flask_cors import CORS

from lease_classifier import LeaseClauseClassifier, PDFReader, DataLoader

# Default config file path
DEFAULT_CONFIG_FILE = "config.ini"

# Global variables
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
config = None
classifier = None
success_logger = None
error_logger = None


def setup_logging(log_config):
    """
    Setup logging with separate success and error log files.

    Args:
        log_config: Dictionary with logging configuration.
    """
    global success_logger, error_logger

    try:
        # Get logging settings
        log_path = log_config.get("path", "logs")
        success_file = log_config.get("success_file", "success.log")
        error_file = log_config.get("error_file", "error.log")
        max_bytes = log_config.get("max_bytes", 10485760)  # 10MB default
        backup_count = log_config.get("backup_count", 5)

        # Create logs directory
        log_dir = Path(log_path)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Log format
        log_format = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Setup success logger
        success_logger = logging.getLogger('success')
        success_logger.setLevel(logging.INFO)
        success_logger.handlers = []  # Clear existing handlers
        success_handler = RotatingFileHandler(
            log_dir / success_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        success_handler.setFormatter(log_format)
        success_logger.addHandler(success_handler)

        # Setup error logger
        error_logger = logging.getLogger('error')
        error_logger.setLevel(logging.ERROR)
        error_logger.handlers = []  # Clear existing handlers
        error_handler = RotatingFileHandler(
            log_dir / error_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setFormatter(log_format)
        error_logger.addHandler(error_handler)

        # Also log errors to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        error_logger.addHandler(console_handler)

        print(f"Logging initialized: {log_dir}")
    except Exception as e:
        print(f"Failed to setup logging: {str(e)}")


def log_success(message, **kwargs):
    """Log a success message."""
    if success_logger:
        extra_info = ' | '.join(f'{k}={v}' for k, v in kwargs.items())
        full_message = f"{message} | {extra_info}" if extra_info else message
        success_logger.info(full_message)


def log_error(message, **kwargs):
    """Log an error message."""
    if error_logger:
        extra_info = ' | '.join(f'{k}={v}' for k, v in kwargs.items())
        full_message = f"{message} | {extra_info}" if extra_info else message
        error_logger.error(full_message)


def load_config(config_file=None):
    """Load configuration from INI file."""
    import configparser
    config_path = Path(config_file or DEFAULT_CONFIG_FILE)

    default_config = {
        "model": {
            "path": "lease_model.joblib",
            "train_data": "test_data",
            "mapping": "data_mapping/data_mapping.json",
            "fields": "data_mapping/data_mapping_fields.json"
        },
        "pdf": {
            "min_length": 30
        },
        "provider": "azure",
        "openai": {
            "api_key": "",
            "gpt_model": "gpt-4o-mini"
        },
        "azure_openai": {
            "default_model": "gpt-4.1",
            "api_version": "2025-04-01-preview",
            "models": {}
        },
        "azure_storage": {
            "connection_string": "",
            "container_name": "lease-pdfs"
        },
        "local_storage": {
            "path": "mnt/cp-files"
        },
        "mongodb": {
            "uri": "",
            "database": "",
            "collection": "cube_outputs"
        },
        "api": {
            "host": "0.0.0.0",
            "port": 5000,
            "debug": False
        },
        "logging": {
            "path": "logs",
            "success_file": "success.log",
            "error_file": "error.log",
            "max_bytes": 10485760,
            "backup_count": 5
        }
    }

    try:
        if config_path.exists():
            parser = configparser.ConfigParser()
            parser.read(config_path, encoding='utf-8')

            # Parse each section
            for section in parser.sections():
                # Handle azure_openai model subsections (e.g., azure_openai.gpt-4.1)
                if section.startswith('azure_openai.'):
                    model_name = section.replace('azure_openai.', '')
                    default_config['azure_openai']['models'][model_name] = {
                        'endpoint': parser.get(section, 'endpoint', fallback=''),
                        'api_key': parser.get(section, 'api_key', fallback=''),
                        'deployment': parser.get(section, 'deployment', fallback=''),
                        'description': parser.get(section, 'description', fallback=''),
                        'api_version': parser.get(section, 'api_version', fallback='')
                    }
                elif section == 'model':
                    default_config['model']['path'] = parser.get(section, 'path', fallback=default_config['model']['path'])
                    default_config['model']['train_data'] = parser.get(section, 'train_data', fallback=default_config['model']['train_data'])
                    default_config['model']['mapping'] = parser.get(section, 'mapping', fallback=default_config['model']['mapping'])
                    default_config['model']['fields'] = parser.get(section, 'fields', fallback=default_config['model']['fields'])
                elif section == 'pdf':
                    default_config['pdf']['min_length'] = parser.getint(section, 'min_length', fallback=default_config['pdf']['min_length'])
                elif section == 'provider':
                    default_config['provider'] = parser.get(section, 'default', fallback=default_config['provider'])
                elif section == 'openai':
                    default_config['openai']['api_key'] = parser.get(section, 'api_key', fallback=default_config['openai']['api_key'])
                    default_config['openai']['gpt_model'] = parser.get(section, 'gpt_model', fallback=default_config['openai']['gpt_model'])
                elif section == 'azure_openai':
                    default_config['azure_openai']['default_model'] = parser.get(section, 'default_model', fallback=default_config['azure_openai']['default_model'])
                    default_config['azure_openai']['api_version'] = parser.get(section, 'api_version', fallback=default_config['azure_openai']['api_version'])
                elif section == 'azure_storage':
                    default_config['azure_storage']['connection_string'] = parser.get(section, 'connection_string', fallback=default_config['azure_storage']['connection_string'])
                    default_config['azure_storage']['container_name'] = parser.get(section, 'container_name', fallback=default_config['azure_storage']['container_name'])
                elif section == 'local_storage':
                    default_config['local_storage']['path'] = parser.get(section, 'path', fallback=default_config['local_storage']['path'])
                elif section == 'mongodb':
                    default_config['mongodb']['uri'] = parser.get(section, 'uri', fallback=default_config['mongodb']['uri'])
                    default_config['mongodb']['database'] = parser.get(section, 'database', fallback=default_config['mongodb']['database'])
                    default_config['mongodb']['collection'] = parser.get(section, 'collection', fallback=default_config['mongodb']['collection'])
                elif section == 'api':
                    default_config['api']['host'] = parser.get(section, 'host', fallback=default_config['api']['host'])
                    default_config['api']['port'] = parser.getint(section, 'port', fallback=default_config['api']['port'])
                    default_config['api']['debug'] = parser.getboolean(section, 'debug', fallback=default_config['api']['debug'])
                elif section == 'logging':
                    default_config['logging']['path'] = parser.get(section, 'path', fallback=default_config['logging']['path'])
                    default_config['logging']['success_file'] = parser.get(section, 'success_file', fallback=default_config['logging']['success_file'])
                    default_config['logging']['error_file'] = parser.get(section, 'error_file', fallback=default_config['logging']['error_file'])
                    default_config['logging']['max_bytes'] = parser.getint(section, 'max_bytes', fallback=default_config['logging']['max_bytes'])
                    default_config['logging']['backup_count'] = parser.getint(section, 'backup_count', fallback=default_config['logging']['backup_count'])

            log_success("Configuration loaded", config_file=str(config_path))
            return default_config
        else:
            log_error("Config file not found, using defaults", config_file=str(config_path))
    except configparser.Error as e:
        log_error("Invalid INI format in config file", config_file=str(config_path), error=str(e))
    except Exception as e:
        log_error("Failed to load config file", config_file=str(config_path), error=str(e))

    return default_config


def load_reverse_mapping(mapping_file):
    """Load name-to-ID mapping from data_mapping.json."""
    name_to_id = {}
    try:
        log_success("Loading reverse mapping", mapping_file=mapping_file)
        with open(mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            if isinstance(item.get('_id'), dict):
                clause_id = item['_id'].get('$oid', '')
            else:
                clause_id = str(item.get('_id', ''))
            name = item.get('name', '')
            if clause_id and name:
                name_to_id[name] = clause_id
        log_success("Reverse mapping loaded", mapping_file=mapping_file, count=len(name_to_id))
    except FileNotFoundError:
        log_error("Mapping file not found", mapping_file=mapping_file)
    except json.JSONDecodeError as e:
        log_error("Invalid JSON in mapping file", mapping_file=mapping_file, error=str(e))
    except Exception as e:
        log_error("Failed to load reverse mapping", mapping_file=mapping_file, error=str(e))
    return name_to_id


def load_fields_mapping(fields_file):
    """Load fields mapping from data_mapping_fields.json."""
    fields = []
    try:
        log_success("Loading fields mapping", fields_file=fields_file)
        with open(fields_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            if isinstance(item.get('_id'), dict):
                field_id = item['_id'].get('$oid', '')
            else:
                field_id = str(item.get('_id', ''))
            name = item.get('name', '')
            priority = item.get('priority', 'normal')
            if field_id and name:
                fields.append({"id": field_id, "name": name, "priority": priority})
        log_success("Fields mapping loaded", fields_file=fields_file, count=len(fields))
    except FileNotFoundError:
        log_error("Fields file not found", fields_file=fields_file)
    except json.JSONDecodeError as e:
        log_error("Invalid JSON in fields file", fields_file=fields_file, error=str(e))
    except Exception as e:
        log_error("Failed to load fields mapping", fields_file=fields_file, error=str(e))
    return fields


def create_openai_client(provider, api_key, azure_endpoint=None, azure_api_version=None):
    """Create OpenAI client based on provider."""
    try:
        log_success("Creating OpenAI client", provider=provider, endpoint=azure_endpoint or "default")
        if provider == 'azure':
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=azure_endpoint,
                api_version=azure_api_version or "2024-02-15-preview"
            )
            log_success("Azure OpenAI client created", endpoint=azure_endpoint, api_version=azure_api_version)
            return client
        else:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            log_success("OpenAI client created")
            return client
    except ImportError as e:
        log_error("OpenAI library not installed", error=str(e))
        raise
    except Exception as e:
        log_error("Failed to create OpenAI client", provider=provider, error=str(e))
        raise


def format_date_value(value):
    """
    Format date value to MM/DD/YYYY format.

    Args:
        value: Date string in various formats.

    Returns:
        Formatted date string in MM/DD/YYYY format or original value if parsing fails.
    """
    import re
    from datetime import datetime

    if not value or not isinstance(value, str):
        return str(value) if value else ""

    try:
        # Try parsing with dateutil if available
        from dateutil import parser as date_parser
        parsed = date_parser.parse(value, dayfirst=False)
        return parsed.strftime('%m/%d/%Y')
    except Exception:
        pass

    # Manual parsing attempts
    try:
        # Try common formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%B %d, %Y', '%b %d, %Y',
                    '%d %B %Y', '%d %b %Y', '%m-%d-%Y', '%d-%m-%Y']:
            try:
                parsed = datetime.strptime(value.strip(), fmt)
                return parsed.strftime('%m/%d/%Y')
            except ValueError:
                continue
    except Exception:
        pass

    return value


def format_amount_value(value, field_name):
    """
    Format monetary amount with comma separators, 2 decimals, and currency.

    Args:
        value: Amount string or number.
        field_name: Name of the field to determine if it's monetary.

    Returns:
        Formatted amount string or original value.
    """
    import re

    # Keywords that indicate monetary fields
    monetary_keywords = [
        'amount', 'rent', 'deposit', 'fee', 'charge', 'cost', 'price',
        'allowance', 'payment', 'tax', 'insurance', 'liability', 'cap'
    ]

    # Check if this is likely a monetary field
    is_monetary = any(kw in field_name.lower() for kw in monetary_keywords)

    if not is_monetary:
        return str(value) if value else ""

    if not value:
        return ""

    value_str = str(value)

    # Extract currency symbol if present
    currency_match = re.match(r'^([£$€¥₹]|USD|EUR|GBP|INR)?\s*', value_str)
    currency = currency_match.group(1) if currency_match else '$'
    if not currency:
        currency = '$'

    # Remove currency and non-numeric characters except decimal point
    numeric_str = re.sub(r'[^\d.]', '', value_str)

    try:
        # Parse as float and format with commas and 2 decimals
        amount = float(numeric_str)
        formatted = f"{currency}{amount:,.2f}"
        return formatted
    except (ValueError, TypeError):
        return value_str


def extract_fields_batch_with_openai(clauses_data, fields, client, model, api_call_counter=None, batch_size=10):
    """
    Extract field values from multiple clauses in a single OpenAI call.

    Args:
        clauses_data: List of dicts with 'clause_index', 'text', and 'type'.
        fields: List of available fields with id, name, and priority.
        client: OpenAI client instance.
        model: Model name to use.
        api_call_counter: Dictionary to track API calls (optional).
        batch_size: Maximum number of clauses per API call (default: 10).

    Returns:
        List of extracted fields with clause_index, field_id, field_name, and value.
    """
    if not clauses_data:
        return []

    all_results = []

    # Separate high priority and normal priority fields
    high_priority_fields = [f for f in fields if f.get("priority") == "high"]
    normal_priority_fields = [f for f in fields if f.get("priority") != "high"]

    # Build field name to ID mapping for ALL fields
    field_name_to_id = {f["name"]: f["id"] for f in fields}

    # Order fields with high priority first, then normal
    high_priority_names = [f["name"] for f in high_priority_fields]
    normal_priority_names = [f["name"] for f in normal_priority_fields]

    # Mandatory fields that must be extracted if present in the PDF
    mandatory_fields = ["Tenant Name", "Landlord Name", "Property Address"]

    log_success("Fields loaded", high_priority=len(high_priority_names), normal_priority=len(normal_priority_names))

    # Date field keywords
    date_keywords = ['date', 'commencement', 'expiration', 'termination', 'effective', 'signed', 'start', 'end', 'due']

    # Process in batches
    for batch_start in range(0, len(clauses_data), batch_size):
        batch = clauses_data[batch_start:batch_start + batch_size]

        try:
            log_success("Extracting fields with OpenAI (batch)",
                       batch_start=batch_start, batch_size=len(batch), model=model)

            # Build batch prompt
            clauses_text = ""
            for item in batch:
                clauses_text += f"""
---
Clause Index: {item['clause_index']}
Clause Type: {item['type']}
Text: {item['text']}
"""

            # Build prompt with mandatory and high priority fields listed first
            prompt = f"""Analyze the following lease clauses and extract relevant field values from each.

{clauses_text}

MANDATORY fields (MUST extract if found anywhere in the text):
{json.dumps(mandatory_fields, indent=2)}

HIGH PRIORITY fields to extract (focus on these after mandatory):
{json.dumps([f for f in high_priority_names if f not in mandatory_fields], indent=2)}

OTHER fields to extract (extract if found in text):
{json.dumps(normal_priority_names, indent=2)}

Instructions:
1. MANDATORY fields (Tenant Name, Landlord Name, Property Address) MUST be extracted if they exist in the text
2. Extract ALL fields that have clear values mentioned in the text
3. Give priority to HIGH PRIORITY fields - ensure these are extracted if present
4. Also extract OTHER fields if their values are found in the text
5. Return a JSON object where keys are clause indices (as strings) and values are objects with extracted field names and values
6. If a field value is not found in a clause, do not include it
7. For monetary values, extract the numeric amount and currency symbol (e.g., "$1500.00")
8. For dates, extract in the original format found in the text
9. Be precise and only extract explicitly stated information

Return ONLY a valid JSON object in this format:
{{
  "0": {{"Field Name": "value", ...}},
  "1": {{"Field Name": "value", ...}},
  ...
}}"""

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a legal document analyzer. Extract specific field values from lease clauses. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=4000
            )

            # Increment API call counter
            if api_call_counter is not None:
                api_call_counter['count'] = api_call_counter.get('count', 0) + 1

            # Parse the response
            response_text = response.choices[0].message.content.strip()

            # Try to extract JSON from response
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            extracted = json.loads(response_text)

            # Map extracted values to field IDs with formatting
            for clause_idx_str, clause_fields in extracted.items():
                try:
                    clause_idx = int(clause_idx_str)
                except ValueError:
                    continue

                if not isinstance(clause_fields, dict):
                    continue

                for field_name, value in clause_fields.items():
                    if field_name in field_name_to_id and value:
                        # Format based on field type
                        is_date_field = any(kw in field_name.lower() for kw in date_keywords)

                        if is_date_field:
                            formatted_value = format_date_value(value)
                        else:
                            formatted_value = format_amount_value(value, field_name)

                        all_results.append({
                            "clause_index": clause_idx,
                            "field_id": field_name_to_id[field_name],
                            "field_name": field_name,
                            "value": formatted_value
                        })

            log_success("Batch fields extracted successfully",
                       batch_start=batch_start, fields_count=len(all_results))

        except json.JSONDecodeError as e:
            log_error("Failed to parse OpenAI batch response as JSON",
                     batch_start=batch_start, error=str(e))
        except Exception as e:
            log_error("OpenAI batch field extraction failed",
                     batch_start=batch_start, error=str(e))

    return all_results


def save_to_mongodb(output, mongo_uri, mongo_db, mongo_collection):
    """Save output to MongoDB database."""
    try:
        log_success("Saving to MongoDB", database=mongo_db, collection=mongo_collection)
        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        output["created_at"] = datetime.now(timezone.utc)

        result = collection.insert_one(output)
        client.close()

        log_success("MongoDB save successful", document_id=str(result.inserted_id), database=mongo_db)
        return str(result.inserted_id)
    except ImportError as e:
        log_error("pymongo library not installed", error=str(e))
        return None
    except Exception as e:
        log_error("MongoDB save failed", database=mongo_db, collection=mongo_collection, error=str(e))
        return None


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


def load_classifier():
    """Load or train the classifier."""
    global classifier, config

    try:
        model_file = config["model"]["path"]
        model_path = Path(model_file)

        if model_path.exists():
            log_success("Loading classifier from file", model_file=model_file)
            classifier = LeaseClauseClassifier.load(model_file)
            log_success("Classifier loaded successfully", model_file=model_file)
        else:
            log_success("Training new classifier", model_file=model_file)
            train_data = config["model"]["train_data"]
            mapping_file = config["model"]["mapping"]
            train_path = Path(train_data)
            mapping_path = Path(mapping_file)

            if not train_path.exists():
                log_error("Training data folder not found", train_data=train_data)
                raise FileNotFoundError(f"Training data folder not found: {train_data}")

            mapping_for_train = mapping_file if mapping_path.exists() else None
            texts, labels = DataLoader.load_with_mapping(train_data, mapping_for_train)

            if len(texts) == 0:
                log_error("No training data found", train_data=train_data)
                raise ValueError("No training data found")

            classifier = LeaseClauseClassifier(
                kernel='rbf',
                C=1.0,
                max_features=5000
            )
            classifier.fit(texts, labels)
            classifier.save(model_file)
            log_success("Classifier trained and saved", model_file=model_file, samples=len(texts))

        return classifier

    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as e:
        log_error("Failed to load/train classifier", error=str(e))
        raise


def process_pdf(pdf_path, gpt_model=None, extract_fields_enabled=True):
    """
    Process a PDF file and return classification results.

    Args:
        pdf_path: Path to the PDF file.
        gpt_model: GPT model to use (optional).
        extract_fields_enabled: Whether to extract fields using OpenAI.

    Returns:
        Dictionary with classification results.
    """
    global classifier, config

    try:
        log_success("Processing PDF", pdf_path=pdf_path)

        # Get settings
        mapping_file = config["model"]["mapping"]
        fields_file = config["model"]["fields"]
        min_length = config["pdf"]["min_length"]

        # Load mappings
        mapping_path = Path(mapping_file)
        name_to_id = {}
        if mapping_path.exists():
            name_to_id = load_reverse_mapping(mapping_file)

        # Get provider setting (azure or openai) - now a top-level key
        provider = config.get("provider", "azure")

        # Get Azure OpenAI settings
        azure_config = config.get("azure_openai", {})
        azure_api_version = azure_config.get("api_version", "2024-02-15-preview")
        azure_models = azure_config.get("models", {})

        # Determine which model to use
        if provider == 'azure':
            # For Azure, use gpt_model param, or default_model from azure_openai, or first available model
            selected_model = gpt_model or azure_config.get("default_model", "")
            if not selected_model and azure_models:
                selected_model = list(azure_models.keys())[0]
        else:
            # For regular OpenAI
            selected_model = gpt_model or config["openai"].get("gpt_model", "gpt-4o-mini")

        # Get API key, endpoint, and deployment based on provider
        openai_api_key = ""
        azure_endpoint = ""
        azure_deployment = ""

        if provider == 'azure':
            # Get model-specific config from azure_openai.models
            if selected_model in azure_models:
                model_config = azure_models[selected_model]
                openai_api_key = os.environ.get('AZURE_OPENAI_API_KEY') or model_config.get("api_key", "")
                azure_endpoint = model_config.get("endpoint", "")
                azure_deployment = model_config.get("deployment", "")
                # Use model-specific api_version if available, otherwise use default
                azure_api_version = model_config.get("api_version", azure_api_version)
        else:
            # Regular OpenAI
            openai_api_key = os.environ.get('OPENAI_API_KEY') or config["openai"].get("api_key", "")

        extract_fields = extract_fields_enabled and openai_api_key

        # Create OpenAI client
        openai_client = None
        deployment_name = selected_model
        if extract_fields:
            try:
                openai_client = create_openai_client(
                    provider=provider,
                    api_key=openai_api_key,
                    azure_endpoint=azure_endpoint,
                    azure_api_version=azure_api_version
                )
                if provider == 'azure' and azure_deployment:
                    deployment_name = azure_deployment
            except Exception as e:
                log_error("Failed to create OpenAI client, continuing without field extraction", error=str(e))
                extract_fields = False

        # Load fields mapping
        fields = []
        fields_path = Path(fields_file)
        if fields_path.exists() and extract_fields:
            fields = load_fields_mapping(fields_file)

        # Extract clauses from PDF
        try:
            log_success("Extracting clauses from PDF", pdf_path=pdf_path)
            test_clauses = PDFReader.extract_clauses(pdf_path, min_length=min_length)

            if not test_clauses:
                full_text = PDFReader.read_pdf(pdf_path)
                test_clauses = [s.strip() for s in full_text.split('.') if len(s.strip()) > min_length]

            if not test_clauses:
                log_error("No text could be extracted from PDF", pdf_path=pdf_path)
                raise ValueError("No text could be extracted from PDF")

            log_success("Clauses extracted from PDF", pdf_path=pdf_path, clauses_count=len(test_clauses))
        except Exception as e:
            log_error("Failed to extract clauses from PDF", pdf_path=pdf_path, error=str(e))
            raise

        # Initialize API call counter
        api_call_counter = {'count': 0}

        # Classify each clause
        clauses_results = []
        clauses_for_extraction = []

        log_success("Classifying clauses", total_clauses=len(test_clauses))
        for idx, clause in enumerate(test_clauses):
            try:
                prediction = classifier.predict(clause)
                proba = classifier.predict_proba(clause)
                confidence = proba[prediction]

                type_id = name_to_id.get(prediction, None)

                clause_result = {
                    "clause_index": idx,
                    "text": clause,
                    "type": prediction,
                    "type_id": type_id,
                    "confidence": round(confidence, 4)
                }
                clauses_results.append(clause_result)

                # Collect clauses for batch field extraction
                if extract_fields and fields and openai_client:
                    clauses_for_extraction.append({
                        "clause_index": idx,
                        "text": clause,
                        "type": prediction
                    })

            except Exception as e:
                log_error("Clause classification error", clause_index=idx, error=str(e))
                continue

        # Extract fields using OpenAI in batches (reduces API calls)
        fields_results = []
        if clauses_for_extraction:
            try:
                extracted_fields = extract_fields_batch_with_openai(
                    clauses_for_extraction, fields, openai_client, deployment_name,
                    api_call_counter=api_call_counter, batch_size=10
                )
                # Group fields by field_id - merge values into arrays if same field appears multiple times
                fields_dict = {}
                for field in extracted_fields:
                    field_id = field['field_id']
                    field_name = field['field_name']
                    value = field['value']
                    clause_idx = field['clause_index']

                    if field_id not in fields_dict:
                        # First occurrence - initialize with value as array
                        fields_dict[field_id] = {
                            "field_id": field_id,
                            "field_name": field_name,
                            "values": [value],
                            "clause_indices": [clause_idx]
                        }
                    else:
                        # Add to existing field if value is different
                        if value not in fields_dict[field_id]["values"]:
                            fields_dict[field_id]["values"].append(value)
                        if clause_idx not in fields_dict[field_id]["clause_indices"]:
                            fields_dict[field_id]["clause_indices"].append(clause_idx)

                # Convert dict to list
                fields_results = list(fields_dict.values())
            except Exception as e:
                log_error("Batch field extraction error", pdf_path=pdf_path, error=str(e))

        log_success("PDF processing complete", pdf_path=pdf_path,
                   clauses=len(clauses_results), fields=len(fields_results),
                   openai_api_calls=api_call_counter['count'])

        return {
            "total_clauses": len(clauses_results),
            "total_fields": len(fields_results),
            "openai_api_calls": api_call_counter['count'],
            "field_extraction_enabled": extract_fields,
            "clauses": clauses_results,
            "fields": fields_results
        }

    except ValueError:
        raise
    except Exception as e:
        log_error("PDF processing failed", pdf_path=pdf_path, error=str(e))
        raise


# API Routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "Lease Classifier API is running"})


@app.route('/classify', methods=['POST'])
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


@app.route('/classify/file', methods=['POST'])
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


@app.route('/upload', methods=['POST'])
def upload_pdf():
    """
    Upload PDF to Azure Blob Storage or local storage.

    Request:
        - Form data with 'pdf' file

    Response:
        JSON with storage name and location.
    """
    try:
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


@app.route('/models', methods=['GET'])
def list_models():
    """List available GPT models."""
    azure_config = config.get("azure_openai", config.get("azure", {}))
    models = azure_config.get("models", {})

    return jsonify({
        "default_model": config["openai"]["gpt_model"],
        "available_models": list(models.keys())
    })


@app.route('/data', methods=['GET'])
def get_all_data():
    """
    Get all stored classification data from MongoDB.

    Query Parameters:
        - limit: Maximum number of records to return (default: 100, max: 1000)
        - skip: Number of records to skip for pagination (default: 0)
        - sort: Sort order - 'asc' or 'desc' by created_at (default: desc)

    Response:
        JSON with list of all classification results and pagination info.
    """
    try:
        # Get MongoDB settings
        mongo_config = config.get("mongodb", {})
        mongo_uri = os.environ.get('MONGODB_URI') or mongo_config.get("uri", "")
        mongo_db = mongo_config.get("database", "")
        mongo_collection = mongo_config.get("collection", "cube_outputs")

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint="/data")
            return jsonify({"error": "MongoDB not configured"}), 500

        # Get pagination parameters
        limit = min(int(request.args.get('limit', 100)), 1000)
        skip = int(request.args.get('skip', 0))
        sort_order = request.args.get('sort', 'desc')
        sort_direction = -1 if sort_order == 'desc' else 1

        from pymongo import MongoClient
        from bson import ObjectId

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        # Get total count
        total_count = collection.count_documents({})

        # Fetch data with pagination
        cursor = collection.find({}).sort("created_at", sort_direction).skip(skip).limit(limit)

        results = []
        for doc in cursor:
            # Convert ObjectId to string for JSON serialization
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            # Convert datetime to ISO format string
            if 'created_at' in doc:
                doc['created_at'] = doc['created_at'].isoformat() if hasattr(doc['created_at'], 'isoformat') else str(doc['created_at'])
            results.append(doc)

        client.close()

        log_success("Data retrieved from MongoDB", endpoint="/data", count=len(results), total=total_count)

        return jsonify({
            "total": total_count,
            "limit": limit,
            "skip": skip,
            "count": len(results),
            "data": results
        }), 200

    except ImportError as e:
        log_error("pymongo library not installed", endpoint="/data", error=str(e))
        return jsonify({"error": "pymongo library not installed"}), 500
    except Exception as e:
        log_error("Failed to retrieve data", endpoint="/data", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/data/<doc_id>', methods=['GET'])
def get_data_by_id(doc_id):
    """
    Get a specific classification result by document ID.

    Path Parameters:
        - doc_id: MongoDB document ID

    Response:
        JSON with the classification result.
    """
    try:
        # Get MongoDB settings
        mongo_config = config.get("mongodb", {})
        mongo_uri = os.environ.get('MONGODB_URI') or mongo_config.get("uri", "")
        mongo_db = mongo_config.get("database", "")
        mongo_collection = mongo_config.get("collection", "cube_outputs")

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint=f"/data/{doc_id}")
            return jsonify({"error": "MongoDB not configured"}), 500

        from pymongo import MongoClient
        from bson import ObjectId

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        # Try to find by ObjectId
        try:
            doc = collection.find_one({"_id": ObjectId(doc_id)})
        except Exception:
            # If ObjectId conversion fails, try string match
            doc = collection.find_one({"_id": doc_id})

        client.close()

        if not doc:
            log_error("Document not found", endpoint=f"/data/{doc_id}", doc_id=doc_id)
            return jsonify({"error": "Document not found"}), 404

        # Convert ObjectId to string
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        if 'created_at' in doc:
            doc['created_at'] = doc['created_at'].isoformat() if hasattr(doc['created_at'], 'isoformat') else str(doc['created_at'])

        log_success("Document retrieved", endpoint=f"/data/{doc_id}", doc_id=doc_id)

        return jsonify(doc), 200

    except ImportError as e:
        log_error("pymongo library not installed", endpoint=f"/data/{doc_id}", error=str(e))
        return jsonify({"error": "pymongo library not installed"}), 500
    except Exception as e:
        log_error("Failed to retrieve document", endpoint=f"/data/{doc_id}", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/data/search', methods=['GET'])
def search_data():
    """
    Search classification data by PDF filename or field values.

    Query Parameters:
        - filename: Search by PDF filename (partial match)
        - field_name: Search by field name
        - field_value: Search by field value (use with field_name)
        - limit: Maximum number of records (default: 100)

    Response:
        JSON with matching classification results.
    """
    try:
        # Get MongoDB settings
        mongo_config = config.get("mongodb", {})
        mongo_uri = os.environ.get('MONGODB_URI') or mongo_config.get("uri", "")
        mongo_db = mongo_config.get("database", "")
        mongo_collection = mongo_config.get("collection", "cube_outputs")

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint="/data/search")
            return jsonify({"error": "MongoDB not configured"}), 500

        # Get search parameters
        filename = request.args.get('filename', '')
        field_name = request.args.get('field_name', '')
        field_value = request.args.get('field_value', '')
        limit = min(int(request.args.get('limit', 100)), 1000)

        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        # Build query
        query = {}
        if filename:
            query['pdf_file'] = {'$regex': filename, '$options': 'i'}
        if field_name:
            query['fields.field_name'] = {'$regex': field_name, '$options': 'i'}
        if field_value:
            query['fields.values'] = {'$regex': field_value, '$options': 'i'}

        if not query:
            client.close()
            return jsonify({"error": "At least one search parameter required (filename, field_name, or field_value)"}), 400

        # Fetch matching documents
        cursor = collection.find(query).sort("created_at", -1).limit(limit)

        results = []
        for doc in cursor:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            if 'created_at' in doc:
                doc['created_at'] = doc['created_at'].isoformat() if hasattr(doc['created_at'], 'isoformat') else str(doc['created_at'])
            results.append(doc)

        client.close()

        log_success("Search completed", endpoint="/data/search", query=str(query), count=len(results))

        return jsonify({
            "count": len(results),
            "query": {
                "filename": filename or None,
                "field_name": field_name or None,
                "field_value": field_value or None
            },
            "data": results
        }), 200

    except ImportError as e:
        log_error("pymongo library not installed", endpoint="/data/search", error=str(e))
        return jsonify({"error": "pymongo library not installed"}), 500
    except Exception as e:
        log_error("Search failed", endpoint="/data/search", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/data/<doc_id>', methods=['DELETE'])
def delete_data(doc_id):
    """
    Delete a specific classification result by document ID.

    Path Parameters:
        - doc_id: MongoDB document ID

    Response:
        JSON with deletion status.
    """
    try:
        # Get MongoDB settings
        mongo_config = config.get("mongodb", {})
        mongo_uri = os.environ.get('MONGODB_URI') or mongo_config.get("uri", "")
        mongo_db = mongo_config.get("database", "")
        mongo_collection = mongo_config.get("collection", "cube_outputs")

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint=f"/data/{doc_id}")
            return jsonify({"error": "MongoDB not configured"}), 500

        from pymongo import MongoClient
        from bson import ObjectId

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        # Try to delete by ObjectId
        try:
            result = collection.delete_one({"_id": ObjectId(doc_id)})
        except Exception:
            # If ObjectId conversion fails, try string match
            result = collection.delete_one({"_id": doc_id})

        client.close()

        if result.deleted_count == 0:
            log_error("Document not found for deletion", endpoint=f"/data/{doc_id}", doc_id=doc_id)
            return jsonify({"error": "Document not found"}), 404

        log_success("Document deleted", endpoint=f"/data/{doc_id}", doc_id=doc_id)

        return jsonify({
            "message": "Document deleted successfully",
            "doc_id": doc_id
        }), 200

    except ImportError as e:
        log_error("pymongo library not installed", endpoint=f"/data/{doc_id}", error=str(e))
        return jsonify({"error": "pymongo library not installed"}), 500
    except Exception as e:
        log_error("Failed to delete document", endpoint=f"/data/{doc_id}", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/data/stats', methods=['GET'])
def get_data_stats():
    """
    Get statistics about stored classification data.

    Response:
        JSON with database statistics.
    """
    try:
        # Get MongoDB settings
        mongo_config = config.get("mongodb", {})
        mongo_uri = os.environ.get('MONGODB_URI') or mongo_config.get("uri", "")
        mongo_db = mongo_config.get("database", "")
        mongo_collection = mongo_config.get("collection", "cube_outputs")

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint="/data/stats")
            return jsonify({"error": "MongoDB not configured"}), 500

        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        # Get statistics
        total_documents = collection.count_documents({})

        # Aggregate statistics
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_clauses": {"$sum": "$total_clauses"},
                    "total_fields": {"$sum": "$total_fields"},
                    "total_api_calls": {"$sum": "$openai_api_calls"},
                    "avg_clauses": {"$avg": "$total_clauses"},
                    "avg_fields": {"$avg": "$total_fields"}
                }
            }
        ]

        stats_result = list(collection.aggregate(pipeline))

        # Get unique PDF files
        unique_pdfs = len(collection.distinct("pdf_file"))

        # Get date range
        oldest = collection.find_one({}, sort=[("created_at", 1)])
        newest = collection.find_one({}, sort=[("created_at", -1)])

        client.close()

        stats = {
            "total_documents": total_documents,
            "unique_pdfs": unique_pdfs,
            "database": mongo_db,
            "collection": mongo_collection
        }

        if stats_result:
            agg = stats_result[0]
            stats["total_clauses_processed"] = agg.get("total_clauses", 0)
            stats["total_fields_extracted"] = agg.get("total_fields", 0)
            stats["total_api_calls"] = agg.get("total_api_calls", 0)
            stats["avg_clauses_per_doc"] = round(agg.get("avg_clauses", 0), 2)
            stats["avg_fields_per_doc"] = round(agg.get("avg_fields", 0), 2)

        if oldest and 'created_at' in oldest:
            stats["oldest_record"] = oldest['created_at'].isoformat() if hasattr(oldest['created_at'], 'isoformat') else str(oldest['created_at'])
        if newest and 'created_at' in newest:
            stats["newest_record"] = newest['created_at'].isoformat() if hasattr(newest['created_at'], 'isoformat') else str(newest['created_at'])

        log_success("Stats retrieved", endpoint="/data/stats", total=total_documents)

        return jsonify(stats), 200

    except ImportError as e:
        log_error("pymongo library not installed", endpoint="/data/stats", error=str(e))
        return jsonify({"error": "pymongo library not installed"}), 500
    except Exception as e:
        log_error("Failed to retrieve stats", endpoint="/data/stats", error=str(e))
        return jsonify({"error": str(e)}), 500


def init_app():
    """Initialize the application."""
    global config, classifier

    try:
        config = load_config()

        # Setup logging
        log_config = config.get("logging", {})
        setup_logging(log_config)
        log_success("Logging initialized", log_path=log_config.get("path", "logs"))

        classifier = load_classifier()

        log_success("API initialized", clause_types=len(classifier.classes_))
        print("Lease Classifier API initialized")
        print(f"Loaded classifier with {len(classifier.classes_)} clause types")

    except FileNotFoundError as e:
        log_error("Initialization failed - File not found", error=str(e))
        print(f"Initialization failed: {str(e)}")
        raise
    except ValueError as e:
        log_error("Initialization failed - Invalid configuration", error=str(e))
        print(f"Initialization failed: {str(e)}")
        raise
    except Exception as e:
        log_error("Initialization failed", error=str(e))
        print(f"Initialization failed: {str(e)}")
        raise


if __name__ == '__main__':
    try:
        init_app()

        api_config = config.get("api", {})
        host = api_config.get("host", "0.0.0.0")
        port = api_config.get("port", 5000)
        debug = api_config.get("debug", False)

        log_success("Starting API server", host=host, port=port)
        print(f"Starting API server on {host}:{port}")
        app.run(host=host, port=port, debug=debug)

    except Exception as e:
        log_error("Failed to start API server", error=str(e))
        print(f"Failed to start API server: {str(e)}")
