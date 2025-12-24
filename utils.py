"""
Utility functions for the Lease Clause Classifier API.
Contains logging, configuration, and helper functions.
"""

import os
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

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

    DEFAULT_CONFIG_FILE = "config.ini"
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


def format_date_value(value):
    """
    Format date value to MM/DD/YYYY format.

    Args:
        value: Date string in various formats.

    Returns:
        Formatted date string in MM/DD/YYYY format or original value if parsing fails.
    """
    import re

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
