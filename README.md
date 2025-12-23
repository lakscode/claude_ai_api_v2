# Lease Clause Classifier

An SVM-based text classifier for categorizing lease document clauses with field extraction using OpenAI/Azure OpenAI.

## Features

- **SVM Classification**: Uses Support Vector Machine with TF-IDF vectorization
- **PDF Support**: Extract and classify clauses directly from PDF files
- **Field Extraction**: Extract field values (dates, amounts, names, addresses) using OpenAI/Azure OpenAI
- **Batch Processing**: Process multiple PDFs from a folder
- **REST API**: Flask-based API for integration
- **Multiple Storage Options**: Local storage or Azure Blob Storage
- **MongoDB Integration**: Store results in MongoDB

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Configuration is stored in `config.ini`. Copy the example and edit with your settings:

```ini
[model]
path = lease_model.joblib
train_data = test_data
mapping = data_mapping/data_mapping.json
fields = data_mapping/data_mapping_fields.json

[pdf]
min_length = 30

[provider]
# Options: azure, openai
default = azure

[openai]
api_key = your-openai-api-key
gpt_model = gpt-4o-mini

[azure_openai]
default_model = gpt-4.1
api_version = 2025-04-01-preview

[azure_openai.gpt-4.1]
endpoint = https://your-endpoint.openai.azure.com/
api_key = your-azure-api-key
deployment = your-deployment-name
description = GPT-4.1 model
api_version = 2023-03-15-preview

[local_storage]
path = mnt/cp-files

[mongodb]
uri = mongodb://localhost:27017
database = Clause_AI
collection = cube_outputs

[api]
host = 0.0.0.0
port = 5000
debug = false

[logging]
path = logs
success_file = success.log
error_file = error.log
```

---

## Command Line Usage

### Process a Single PDF

```bash
python example.py --pdf path/to/lease.pdf
```

### Process Multiple PDFs from a Folder

```bash
python example.py --input-folder path/to/pdf/folder
```

### Save Results to Output Folder

```bash
python example.py --input-folder path/to/pdfs --output-folder path/to/output
```

Results will be saved to `output.json` in the output folder.

### Specify GPT Model

```bash
python example.py --pdf lease.pdf --gpt-model gpt-5
```

### Disable Field Extraction

```bash
python example.py --pdf lease.pdf --no-fields
```

### Use Custom Config File

```bash
python example.py --pdf lease.pdf --config my_config.ini
```

### Full Command Line Options

```bash
python example.py --help

Options:
  --pdf PATH              Path to a single PDF file to process
  --input-folder PATH     Path to folder containing PDF files
  --output-folder PATH    Path to folder for output results
  --config PATH           Path to config file (default: config.ini)
  --gpt-model MODEL       GPT model to use (gpt-4.1, gpt-5)
  --no-fields            Disable field extraction with OpenAI
```

### Example Output

```json
{
  "pdf_file": "sample_lease.pdf",
  "storage_type": "local",
  "storage_name": "uuid_sample_lease.pdf",
  "total_clauses": 45,
  "total_fields": 12,
  "openai_api_calls": 5,
  "field_extraction_enabled": true,
  "clauses": [
    {
      "clause_index": 0,
      "text": "This Lease Agreement is made...",
      "type": "Preamble",
      "type_id": "5d511...",
      "confidence": 0.9234
    }
  ],
  "fields": [
    {
      "field_id": "64217b1a275caef553ece403",
      "field_name": "Tenant Name",
      "values": ["ABC Corporation"],
      "clause_indices": [0, 2]
    },
    {
      "field_id": "5d9c202e2cf8b955c880360c",
      "field_name": "Term Start Date",
      "values": ["01/01/2025"],
      "clause_indices": [5]
    }
  ]
}
```

---

## REST API Usage

### Start the API Server

```bash
python api.py
```

The server starts on `http://localhost:5000` by default.

### API Endpoints

#### Health Check

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "message": "Lease Classifier API is running"
}
```

#### Upload and Classify PDF

```bash
curl -X POST http://localhost:5000/classify \
  -F "pdf=@path/to/lease.pdf"
```

With options:
```bash
curl -X POST "http://localhost:5000/classify?gpt_model=gpt-5&no_fields=false" \
  -F "pdf=@lease.pdf"
```

#### Upload PDF Only (without classification)

```bash
curl -X POST http://localhost:5000/upload \
  -F "pdf=@path/to/lease.pdf"
```

Response:
```json
{
  "message": "PDF uploaded successfully",
  "storage_name": "uuid_lease.pdf",
  "storage_location": "/path/to/storage/uuid_lease.pdf",
  "storage_type": "local",
  "original_filename": "lease.pdf"
}
```

#### Classify from Storage

Classify a previously uploaded PDF:

```bash
curl -X POST http://localhost:5000/classify/file \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "uuid_lease.pdf",
    "storage_type": "local",
    "gpt_model": "gpt-4.1",
    "no_fields": false
  }'
```

#### List Available Models

```bash
curl http://localhost:5000/models
```

Response:
```json
{
  "default_model": "gpt-4o-mini",
  "available_models": ["gpt-4.1", "gpt-5"]
}
```

### API Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `gpt_model` | string | GPT model to use (gpt-4.1, gpt-5) |
| `no_fields` | boolean | Set to `true` to disable field extraction |

### Python Requests Example

```python
import requests

# Upload and classify a PDF
with open('lease.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/classify',
        files={'pdf': f},
        params={'gpt_model': 'gpt-4.1'}
    )

result = response.json()
print(f"Clauses: {result['total_clauses']}")
print(f"Fields: {result['total_fields']}")

# Print extracted fields
for field in result['fields']:
    print(f"{field['field_name']}: {field['values']}")
```

### JavaScript/Fetch Example

```javascript
const formData = new FormData();
formData.append('pdf', fileInput.files[0]);

fetch('http://localhost:5000/classify?gpt_model=gpt-4.1', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Clauses:', data.total_clauses);
    console.log('Fields:', data.fields);
});
```

---

## Field Extraction

The system extracts the following field types from lease documents:

### High Priority Fields
- Tenant Name
- Landlord Name
- Property Address
- Term Start Date
- Term End Date
- Monthly Rent Amount
- Annual Rent Amount
- Security Deposit Amount
- Lease Duration
- Rentable Surface Area

### Mandatory Fields
These fields are always extracted if present:
- Tenant Name
- Landlord Name
- Property Address

### Output Format

Fields are returned with values as arrays to handle multiple occurrences:

```json
{
  "field_id": "64217b1a275caef553ece403",
  "field_name": "Tenant Name",
  "values": ["ABC Corp", "ABC Corporation Inc."],
  "clause_indices": [0, 15, 42]
}
```

---

## Project Structure

```
lease_classifier_project/
├── lease_classifier/
│   ├── __init__.py
│   ├── classifier.py      # Main SVM classifier
│   ├── preprocessor.py    # Text preprocessing
│   ├── pdf_reader.py      # PDF text extraction
│   └── data_loader.py     # Data loading utilities
├── data_mapping/
│   ├── data_mapping.json       # Clause type mappings
│   └── data_mapping_fields.json # Field definitions
├── test_data/             # Training data folder
├── api.py                 # Flask REST API
├── example.py             # Command line interface
├── config.ini             # Configuration file
├── requirements.txt
└── README.md
```

## Environment Variables

You can also configure the system using environment variables:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Blob Storage connection string |
| `MONGODB_URI` | MongoDB connection URI |

Environment variables take precedence over config.ini values.

## Logging

Logs are stored in the `logs/` directory:
- `success.log` - Successful operations
- `error.log` - Errors and failures

Log files rotate at 10MB with 5 backups.
