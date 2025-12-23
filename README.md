# Lease Clause Classifier

An SVM-based text classifier for categorizing lease document clauses into predefined categories.

## Features

- **SVM Classification**: Uses Support Vector Machine with TF-IDF vectorization
- **10 Clause Categories**: rent_payment, security_deposit, maintenance, termination, utilities, pets, subletting, insurance, default, other
- **Model Persistence**: Save and load trained models
- **Probability Scores**: Get confidence scores for predictions
- **Cross-validation**: Built-in model evaluation

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Using the Example Script

```bash
python example.py
```

### Training a Model

```bash
# Train with default settings
python train.py

# Train with custom parameters
python train.py --kernel linear --C 0.5 --output my_model.joblib

# Train with cross-validation
python train.py --cross-validate
```

### Making Predictions

```bash
# Classify a single clause
python predict.py --text "Rent of $1500 is due on the first of each month"

# Classify multiple clauses
python predict.py --text "Monthly rent is $2000" "No pets allowed"

# Classify from a file
python predict.py --file clauses.txt

# Show probability scores
python predict.py --text "Tenant must maintain insurance" --show-proba
```

## Python API

```python
from lease_classifier import LeaseClauseClassifier
from lease_classifier.sample_data import get_sample_data

# Load data and train
texts, labels = get_sample_data()
classifier = LeaseClauseClassifier(kernel='rbf', C=1.0)
classifier.fit(texts, labels)

# Predict
clause = "Monthly rent of $1500 is due on the first"
prediction = classifier.predict(clause)
print(f"Type: {prediction}")

# Get probabilities
proba = classifier.predict_proba(clause)
print(f"Confidence: {proba[prediction]:.2%}")

# Save/Load model
classifier.save('model.joblib')
loaded = LeaseClauseClassifier.load('model.joblib')
```

## Clause Categories

| Category | Description |
|----------|-------------|
| rent_payment | Rent amounts, due dates, payment methods, late fees |
| security_deposit | Deposits, refunds, deductions, escrow |
| maintenance | Repairs, upkeep, responsibilities |
| termination | Lease ending, notice periods, early termination |
| utilities | Utility payments and services |
| pets | Pet policies and restrictions |
| subletting | Sublease rights and assignments |
| insurance | Renter's insurance requirements |
| default | Breach of lease and remedies |
| other | Miscellaneous provisions |

## Project Structure

```
lease_classifier_project/
├── lease_classifier/
│   ├── __init__.py
│   ├── classifier.py      # Main SVM classifier
│   ├── preprocessor.py    # Text preprocessing
│   └── sample_data.py     # Sample training data
├── train.py               # Training script
├── predict.py             # Prediction script
├── example.py             # Usage example
├── requirements.txt
└── README.md
```

## Customization

### Using Your Own Training Data

```python
from lease_classifier import LeaseClauseClassifier

# Your custom data
texts = ["Your lease clause text...", ...]
labels = ["rent_payment", "maintenance", ...]

classifier = LeaseClauseClassifier()
classifier.fit(texts, labels)
```

### Tuning the Classifier

```python
classifier = LeaseClauseClassifier(
    kernel='rbf',       # 'linear', 'rbf', 'poly', 'sigmoid'
    C=1.0,              # Regularization (higher = less regularization)
    gamma='scale',      # Kernel coefficient
    max_features=5000   # Max TF-IDF features
)
```
