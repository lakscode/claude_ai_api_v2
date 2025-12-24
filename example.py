"""
Lease Clause Classifier - Classify clauses from PDF files.
Extracts field values using OpenAI after classification.
Outputs results in JSON format.
"""

import os
import sys
import json
import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from lease_classifier import LeaseClauseClassifier, PDFReader, DataLoader
from output_generator import generate_outputs

# Default config file path
DEFAULT_CONFIG_FILE = "config.ini"

# Global loggers
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
        success_logger = logging.getLogger('cli_success')
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
        error_logger = logging.getLogger('cli_error')
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

        print(f"Logging initialized: {log_dir}")
    except Exception as e:
        print(f"Failed to setup logging: {str(e)}", file=sys.stderr)


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
    """
    Load configuration from INI file.

    Args:
        config_file: Path to config file (default: config.ini)

    Returns:
        Dictionary with configuration values
    """
    import configparser

    config_path = Path(config_file or DEFAULT_CONFIG_FILE)

    # Default configuration
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
            "api_version": "2024-02-15-preview",
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

            # Parse model section
            if parser.has_section('model'):
                default_config['model']['path'] = parser.get('model', 'path', fallback=default_config['model']['path'])
                default_config['model']['train_data'] = parser.get('model', 'train_data', fallback=default_config['model']['train_data'])
                default_config['model']['mapping'] = parser.get('model', 'mapping', fallback=default_config['model']['mapping'])
                default_config['model']['fields'] = parser.get('model', 'fields', fallback=default_config['model']['fields'])

            # Parse pdf section
            if parser.has_section('pdf'):
                default_config['pdf']['min_length'] = parser.getint('pdf', 'min_length', fallback=default_config['pdf']['min_length'])

            # Parse provider section
            if parser.has_section('provider'):
                default_config['provider'] = parser.get('provider', 'default', fallback=default_config['provider'])

            # Parse openai section
            if parser.has_section('openai'):
                default_config['openai']['api_key'] = parser.get('openai', 'api_key', fallback=default_config['openai']['api_key'])
                default_config['openai']['gpt_model'] = parser.get('openai', 'gpt_model', fallback=default_config['openai']['gpt_model'])

            # Parse azure_openai section
            if parser.has_section('azure_openai'):
                default_config['azure_openai']['default_model'] = parser.get('azure_openai', 'default_model', fallback=default_config['azure_openai']['default_model'])
                default_config['azure_openai']['api_version'] = parser.get('azure_openai', 'api_version', fallback=default_config['azure_openai']['api_version'])

            # Parse azure_openai model subsections (e.g., azure_openai.gpt-4.1)
            for section in parser.sections():
                if section.startswith('azure_openai.'):
                    model_name = section.replace('azure_openai.', '')
                    default_config['azure_openai']['models'][model_name] = {
                        'endpoint': parser.get(section, 'endpoint', fallback=''),
                        'api_key': parser.get(section, 'api_key', fallback=''),
                        'deployment': parser.get(section, 'deployment', fallback=''),
                        'description': parser.get(section, 'description', fallback=''),
                        'api_version': parser.get(section, 'api_version', fallback='')
                    }

            # Parse azure_storage section
            if parser.has_section('azure_storage'):
                default_config['azure_storage']['connection_string'] = parser.get('azure_storage', 'connection_string', fallback=default_config['azure_storage']['connection_string'])
                default_config['azure_storage']['container_name'] = parser.get('azure_storage', 'container_name', fallback=default_config['azure_storage']['container_name'])

            # Parse local_storage section
            if parser.has_section('local_storage'):
                default_config['local_storage']['path'] = parser.get('local_storage', 'path', fallback=default_config['local_storage']['path'])

            # Parse mongodb section
            if parser.has_section('mongodb'):
                default_config['mongodb']['uri'] = parser.get('mongodb', 'uri', fallback=default_config['mongodb']['uri'])
                default_config['mongodb']['database'] = parser.get('mongodb', 'database', fallback=default_config['mongodb']['database'])
                default_config['mongodb']['collection'] = parser.get('mongodb', 'collection', fallback=default_config['mongodb']['collection'])

            # Parse api section
            if parser.has_section('api'):
                default_config['api']['host'] = parser.get('api', 'host', fallback=default_config['api']['host'])
                default_config['api']['port'] = parser.getint('api', 'port', fallback=default_config['api']['port'])
                default_config['api']['debug'] = parser.getboolean('api', 'debug', fallback=default_config['api']['debug'])

            # Parse logging section
            if parser.has_section('logging'):
                default_config['logging']['path'] = parser.get('logging', 'path', fallback=default_config['logging']['path'])
                default_config['logging']['success_file'] = parser.get('logging', 'success_file', fallback=default_config['logging']['success_file'])
                default_config['logging']['error_file'] = parser.get('logging', 'error_file', fallback=default_config['logging']['error_file'])
                default_config['logging']['max_bytes'] = parser.getint('logging', 'max_bytes', fallback=default_config['logging']['max_bytes'])
                default_config['logging']['backup_count'] = parser.getint('logging', 'backup_count', fallback=default_config['logging']['backup_count'])

            log_success("Configuration loaded", config_file=str(config_path))
            return default_config
        else:
            log_error("Config file not found, using defaults", config_file=str(config_path))
    except configparser.Error as e:
        log_error("Invalid INI config file", config_file=str(config_path), error=str(e))
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
    """
    Create OpenAI client based on provider.

    Args:
        provider: 'openai' or 'azure'
        api_key: API key
        azure_endpoint: Azure OpenAI endpoint (required for Azure)
        azure_api_version: Azure API version (required for Azure)

    Returns:
        OpenAI client instance or None if failed
    """
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

    # Common date patterns to try
    date_patterns = [
        # ISO format
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
        # DD/MM/YYYY or DD-MM-YYYY
        (r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', None),  # Handle specially
        # Month DD, YYYY
        (r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', None),  # Handle specially
        # DD Month YYYY
        (r'(\d{1,2})\s+(\w+)\s+(\d{4})', None),  # Handle specially
    ]

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


def save_to_local_storage(file_path, local_storage_path):
    """
    Copy PDF file to local storage.

    Args:
        file_path: Path to the source PDF file.
        local_storage_path: Local storage directory path.

    Returns:
        Tuple of (file_name, full_path) or (None, None) if failed.
    """
    import uuid
    import shutil

    try:
        log_success("Saving file to local storage", file_path=file_path, storage_path=local_storage_path)

        storage_dir = Path(local_storage_path)
        storage_dir.mkdir(parents=True, exist_ok=True)

        original_name = Path(file_path).name
        unique_name = f"{uuid.uuid4()}_{original_name}"
        dest_path = storage_dir / unique_name

        shutil.copy2(file_path, dest_path)

        log_success("File saved to local storage", unique_name=unique_name, dest_path=str(dest_path))
        return unique_name, str(dest_path.absolute())

    except FileNotFoundError:
        log_error("Source file not found for local storage", file_path=file_path)
        return None, None
    except PermissionError as e:
        log_error("Permission denied saving to local storage", storage_path=local_storage_path, error=str(e))
        return None, None
    except Exception as e:
        log_error("Local storage save failed", file_path=file_path, error=str(e))
        return None, None


def save_to_mongodb(output, mongo_uri, mongo_db, mongo_collection):
    """
    Save output to MongoDB database.

    Args:
        output: Dictionary containing the classification results.
        mongo_uri: MongoDB connection URI.
        mongo_db: Database name.
        mongo_collection: Collection name.

    Returns:
        Inserted document ID or None if failed.
    """
    try:
        log_success("Saving to MongoDB", database=mongo_db, collection=mongo_collection)

        from pymongo import MongoClient
        from datetime import datetime, timezone

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        # Add timestamp to output
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


def process_single_pdf(pdf_path, classifier, name_to_id, fields, openai_client,
                       deployment_name, extract_fields, min_length, local_path,
                       mongo_uri, mongo_db, mongo_collection):
    """
    Process a single PDF file and return the classification results.

    Args:
        pdf_path: Path to the PDF file.
        classifier: Trained classifier instance.
        name_to_id: Mapping of clause names to IDs.
        fields: List of fields for extraction.
        openai_client: OpenAI client instance.
        deployment_name: Model deployment name.
        extract_fields: Whether to extract fields.
        min_length: Minimum clause length.
        local_path: Local storage path.
        mongo_uri: MongoDB URI.
        mongo_db: MongoDB database name.
        mongo_collection: MongoDB collection name.

    Returns:
        Dictionary with classification results or None if failed.
    """
    try:
        pdf_path = Path(pdf_path)
        log_success("Processing PDF", pdf=str(pdf_path.name))

        # Initialize API call counter for this file
        api_call_counter = {'count': 0}

        # Save PDF to local storage
        storage_name, storage_location = save_to_local_storage(str(pdf_path), local_path)
        if storage_name:
            log_success("PDF saved to local storage", storage_name=storage_name, path=local_path)
        else:
            log_error("Failed to save PDF to local storage", pdf=str(pdf_path), path=local_path)

        # Extract clauses from PDF
        try:
            log_success("Extracting clauses from PDF", pdf=str(pdf_path.name))
            test_clauses = PDFReader.extract_clauses(str(pdf_path), min_length=min_length)

            if not test_clauses:
                full_text = PDFReader.read_pdf(str(pdf_path))
                test_clauses = [s.strip() for s in full_text.split('.') if len(s.strip()) > min_length]

            if not test_clauses:
                log_error("No text could be extracted from PDF", pdf=str(pdf_path))
                return None

            log_success("Clauses extracted from PDF", pdf=str(pdf_path.name), clauses_count=len(test_clauses))
        except Exception as e:
            log_error("Failed to extract clauses from PDF", pdf=str(pdf_path), error=str(e))
            return None

        # Classify each clause and group by predicted type
        clauses_dict = {}  # Group clauses by type
        clauses_for_extraction = []

        log_success("Classifying clauses", pdf=str(pdf_path.name), total_clauses=len(test_clauses))
        for idx, clause in enumerate(test_clauses):
            try:
                prediction = classifier.predict(clause)
                proba = classifier.predict_proba(clause)
                confidence = proba[prediction]

                # Get mapping ID for the predicted type
                type_id = name_to_id.get(prediction, None)

                # Group clauses by predicted type (similar to fields grouping)
                if prediction not in clauses_dict:
                    clauses_dict[prediction] = {
                        "type": prediction,
                        "type_id": type_id,
                        "values": []
                    }

                # Add clause to the values array for this type
                clauses_dict[prediction]["values"].append({
                    "clause_index": idx,
                    "text": clause,
                    "confidence": round(confidence, 4)
                })

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

        # Convert clauses dict to list
        clauses_results = list(clauses_dict.values())

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
                log_error("Batch field extraction error", pdf=str(pdf_path.name), error=str(e))

        # Calculate total individual clauses processed
        total_individual_clauses = sum(len(c["values"]) for c in clauses_results)

        # Build output JSON
        output = {
            "pdf_file": str(pdf_path.name),
            "storage_type": "local",
            "storage_name": storage_name,
            "storage_location": storage_location,
            "total_clauses": total_individual_clauses,
            "total_clause_types": len(clauses_results),
            "total_fields": len(fields_results),
            "openai_api_calls": api_call_counter['count'],
            "field_extraction_enabled": extract_fields,
            "clauses": clauses_results,
            "fields": fields_results
        }

        # Save to MongoDB if configured
        mongo_id = None
        if mongo_uri and mongo_db:
            mongo_id = save_to_mongodb(output.copy(), mongo_uri, mongo_db, mongo_collection)
            if mongo_id:
                output["_id"] = mongo_id

        log_success("PDF processing complete", pdf=str(pdf_path.name),
                   clause_types=len(clauses_results), total_clauses=total_individual_clauses,
                   fields=len(fields_results))
        return output

    except Exception as e:
        log_error("PDF processing failed", pdf=str(pdf_path), error=str(e))
        return None


def main():
    parser = argparse.ArgumentParser(description='Classify lease clauses from PDF files in a folder')
    parser.add_argument('input_folder', type=str,
                        help='Path to folder containing PDF files (required)')
    parser.add_argument('--config', type=str, default='config.ini',
                        help='Path to config file (default: config.ini)')
    parser.add_argument('--output', type=str, default='output_files',
                        help='Output folder for result files (default: output_files)')
    parser.add_argument('--no-fields', action='store_true',
                        help='Skip field extraction with OpenAI')
    parser.add_argument('--gpt-model', type=str, default=None,
                        choices=['gpt-4.1', 'gpt-5'],
                        help='GPT model to use: gpt-4.1 or gpt-5 (overrides config)')
    args = parser.parse_args()

    # Load configuration from file
    config = load_config(args.config)

    # Setup logging
    log_config = config.get("logging", {})
    setup_logging(log_config)

    # Check if input folder exists
    input_folder = Path(args.input_folder)
    if not input_folder.exists():
        log_error("Input folder not found", folder=args.input_folder)
        print(json.dumps({"error": f"Input folder not found: {args.input_folder}"}), file=sys.stderr)
        sys.exit(1)

    if not input_folder.is_dir():
        log_error("Input path is not a folder", path=args.input_folder)
        print(json.dumps({"error": f"Input path is not a folder: {args.input_folder}"}), file=sys.stderr)
        sys.exit(1)

    # Find all PDF files in the folder (use set to avoid duplicates on case-insensitive filesystems)
    pdf_files_set = set(input_folder.glob("*.pdf")) | set(input_folder.glob("*.PDF"))
    pdf_files = sorted(pdf_files_set, key=lambda x: x.name.lower())

    if not pdf_files:
        log_error("No PDF files found in folder", folder=args.input_folder)
        print(json.dumps({"error": f"No PDF files found in folder: {args.input_folder}"}), file=sys.stderr)
        sys.exit(1)

    log_success("Found PDF files", folder=args.input_folder, count=len(pdf_files))

    # Get settings from config
    model_file = config["model"]["path"]
    train_data = config["model"]["train_data"]
    mapping_file = config["model"]["mapping"]
    fields_file = config["model"]["fields"]
    min_length = config["pdf"]["min_length"]

    # Get provider setting (azure or openai)
    provider = config.get("provider", "azure")

    # Get Azure OpenAI settings
    azure_config = config.get("azure_openai", {})
    azure_api_version = azure_config.get("api_version", "2024-02-15-preview")
    azure_models = azure_config.get("models", {})

    # Determine which model to use
    if provider == 'azure':
        # For Azure, use --gpt-model arg, or default_model from azure_openai, or first available model
        gpt_model = args.gpt_model or azure_config.get("default_model", "")
        if not gpt_model and azure_models:
            gpt_model = list(azure_models.keys())[0]
    else:
        # For regular OpenAI
        gpt_model = args.gpt_model or config["openai"].get("gpt_model", "gpt-4o-mini")

    # Get API key, endpoint, and deployment based on provider
    openai_api_key = ""
    azure_endpoint = ""
    azure_deployment = ""

    if provider == 'azure':
        # Get model-specific config from azure_openai.models
        if gpt_model in azure_models:
            model_config = azure_models[gpt_model]
            openai_api_key = os.environ.get('AZURE_OPENAI_API_KEY') or model_config.get("api_key", "")
            azure_endpoint = model_config.get("endpoint", "")
            azure_deployment = model_config.get("deployment", "")
            # Use model-specific api_version if available, otherwise use default
            azure_api_version = model_config.get("api_version", azure_api_version)
        else:
            print(f"Warning: Model '{gpt_model}' not found in azure_openai.models config", file=sys.stderr)
    else:
        # Regular OpenAI
        openai_api_key = os.environ.get('OPENAI_API_KEY') or config["openai"].get("api_key", "")

    # Check if OpenAI is available for field extraction
    openai_available = True
    if provider == 'azure' and not azure_endpoint:
        openai_available = False
        print("Warning: Azure OpenAI endpoint not configured. Field extraction will be disabled.", file=sys.stderr)
    elif provider == 'openai' and not openai_api_key:
        openai_available = False
        print("Warning: OpenAI API key not configured. Field extraction will be disabled.", file=sys.stderr)

    extract_fields = not args.no_fields and openai_api_key and openai_available

    # Create OpenAI client if field extraction is enabled
    openai_client = None
    deployment_name = gpt_model  # Default to model name
    if extract_fields:
        try:
            openai_client = create_openai_client(
                provider=provider,
                api_key=openai_api_key,
                azure_endpoint=azure_endpoint,
                azure_api_version=azure_api_version
            )
            # For Azure, use deployment name if specified
            if provider == 'azure' and azure_deployment:
                deployment_name = azure_deployment
            print(f"OpenAI client created. Provider: {provider}, Model: {deployment_name}")
            log_success("OpenAI client initialized", provider=provider, deployment=deployment_name)
        except Exception as e:
            log_error("Failed to create OpenAI client", error=str(e))
            print(f"Warning: Failed to create OpenAI client: {e}", file=sys.stderr)
            extract_fields = False
            openai_client = None
    else:
        if args.no_fields:
            print("Field extraction disabled (--no-fields flag)")
        elif not openai_api_key:
            print("Field extraction disabled (no API key configured)")
        elif not openai_available:
            print("Field extraction disabled (OpenAI/Azure endpoint not configured)")

    # Load reverse mapping (name -> ID)
    mapping_path = Path(mapping_file)
    name_to_id = {}
    if mapping_path.exists():
        name_to_id = load_reverse_mapping(mapping_file)

    # Load fields mapping
    fields = []
    fields_path = Path(fields_file)
    if fields_path.exists() and extract_fields:
        fields = load_fields_mapping(fields_file)
        print(f"Loaded {len(fields)} field definitions for extraction")

    # Load or train classifier
    model_path = Path(model_file)
    if model_path.exists():
        classifier = LeaseClauseClassifier.load(model_file)
        log_success("Classifier loaded", model=model_file)
    else:
        # Load training data with mapping
        train_path = Path(train_data)

        if not train_path.exists():
            log_error("Training data folder not found", path=train_data)
            print(json.dumps({"error": f"Training data folder not found: {train_data}"}), file=sys.stderr)
            sys.exit(1)

        mapping_for_train = mapping_file if mapping_path.exists() else None
        texts, labels = DataLoader.load_with_mapping(train_data, mapping_for_train)

        if len(texts) == 0:
            log_error("No training data found", path=train_data)
            print(json.dumps({"error": "No training data found"}), file=sys.stderr)
            sys.exit(1)

        classifier = LeaseClauseClassifier(
            kernel='rbf',
            C=1.0,
            max_features=5000
        )
        classifier.fit(texts, labels)
        classifier.save(model_file)
        log_success("Classifier trained and saved", model=model_file, samples=len(texts))

    # Get storage and MongoDB settings
    local_config = config.get("local_storage", {})
    local_path = local_config.get("path", "mnt/cp-files")

    mongo_config = config.get("mongodb", {})
    mongo_uri = os.environ.get('MONGODB_URI') or mongo_config.get("uri", "")
    mongo_db = mongo_config.get("database", "")
    mongo_collection = mongo_config.get("collection", "cube_outputs")

    # Create output folder if specified
    output_folder = None
    if args.output:
        output_folder = Path(args.output)
        output_folder.mkdir(parents=True, exist_ok=True)

    # Process each PDF file
    all_results = []
    successful = 0
    failed = 0

    print(f"Processing {len(pdf_files)} PDF files from {args.input_folder}...")

    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")

        result = process_single_pdf(
            pdf_path=pdf_file,
            classifier=classifier,
            name_to_id=name_to_id,
            fields=fields,
            openai_client=openai_client,
            deployment_name=deployment_name,
            extract_fields=extract_fields,
            min_length=min_length,
            local_path=local_path,
            mongo_uri=mongo_uri,
            mongo_db=mongo_db,
            mongo_collection=mongo_collection
        )

        if result:
            all_results.append(result)
            successful += 1
            api_calls = result.get('openai_api_calls', 0)
            print(f"  -> Processed successfully: {result.get('total_clauses', 0)} clauses, {result.get('total_fields', 0)} fields, {api_calls} OpenAI API calls")
        else:
            failed += 1
            print(f"  -> Failed to process: {pdf_file.name}")

    # Summary
    print(f"\nProcessing complete: {successful} successful, {failed} failed")
    log_success("Batch processing complete", folder=args.input_folder,
               total=len(pdf_files), successful=successful, failed=failed)

    # Save outputs to output folder
    if output_folder and all_results:
        # Save JSON output
        output_file = output_folder / "output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\nJSON results saved to: {output_file}")
        log_success("Results saved to output.json", output_file=str(output_file), total_pdfs=len(all_results))

        # Generate Excel and PDF outputs
        print("\nGenerating Excel and PDF outputs...")
        generated_files = generate_outputs(all_results, str(output_folder), "lease_classification")

        if generated_files.get("excel"):
            log_success("Excel output generated", file=generated_files["excel"])
        if generated_files.get("pdf"):
            log_success("PDF output generated", file=generated_files["pdf"])

        print(f"\nAll outputs saved to: {output_folder}")
    elif all_results:
        # If no output folder, print all results to console
        print("\n--- Results ---")
        print(json.dumps(all_results, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
