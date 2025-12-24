"""
Lease Clause Classifier API
Flask REST API for classifying lease clauses from PDF files.
Supports Azure Blob Storage for PDF storage and MongoDB for output storage.
"""

import os
import json
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from lease_classifier import LeaseClauseClassifier, PDFReader, DataLoader

from utils import (
    setup_logging,
    load_config,
    load_reverse_mapping,
    load_fields_mapping,
    format_date_value,
    format_amount_value,
    log_success,
    log_error
)
from routes import health_bp, classify_bp, data_bp, clauses_bp, fields_bp, auth_bp, users_bp
from swagger import swagger_ui_blueprint, swagger_spec, SWAGGER_URL

# Default config file path
DEFAULT_CONFIG_FILE = "config.ini"

# Global variables
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
config = None
classifier = None


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

        # Classify each clause and group by predicted type
        clauses_dict = {}  # Group clauses by type
        clauses_for_extraction = []

        log_success("Classifying clauses", total_clauses=len(test_clauses))
        for idx, clause in enumerate(test_clauses):
            try:
                prediction = classifier.predict(clause)
                proba = classifier.predict_proba(clause)
                confidence = proba[prediction]

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
                log_error("Batch field extraction error", pdf_path=pdf_path, error=str(e))

        # Calculate total individual clauses processed
        total_individual_clauses = sum(len(c["values"]) for c in clauses_results)

        log_success("PDF processing complete", pdf_path=pdf_path,
                   clause_types=len(clauses_results), total_clauses=total_individual_clauses,
                   fields=len(fields_results), openai_api_calls=api_call_counter['count'])

        return {
            "total_clauses": total_individual_clauses,
            "total_clause_types": len(clauses_results),
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

        # Store config and process_pdf function in app config for routes to access
        app.config['APP_CONFIG'] = config
        app.config['PROCESS_PDF_FUNC'] = process_pdf

        # Register blueprints
        app.register_blueprint(health_bp)
        app.register_blueprint(classify_bp)
        app.register_blueprint(data_bp)
        app.register_blueprint(clauses_bp)
        app.register_blueprint(fields_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(users_bp)

        # Register Swagger UI blueprint
        app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

        # Swagger JSON endpoint
        @app.route('/api/swagger.json')
        def swagger_json():
            """Return the Swagger/OpenAPI specification as JSON."""
            return jsonify(swagger_spec)

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
