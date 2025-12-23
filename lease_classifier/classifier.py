"""
SVM-based classifier for lease clause classification.
"""

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

from .preprocessor import TextPreprocessor


class LeaseClauseClassifier:
    """
    SVM classifier for categorizing lease clauses into predefined categories.

    Supported clause types:
    - rent_payment: Clauses about rent amounts, due dates, payment methods
    - security_deposit: Clauses about deposits, refunds, deductions
    - maintenance: Clauses about repairs, upkeep, responsibilities
    - termination: Clauses about lease ending, notice periods, early termination
    - utilities: Clauses about utility payments and responsibilities
    - pets: Clauses about pet policies and restrictions
    - subletting: Clauses about sublease and assignment rights
    - insurance: Clauses about insurance requirements
    - default: Clauses about breach and remedies
    - other: Miscellaneous clauses
    """

    CLAUSE_TYPES = [
        'rent_payment',
        'security_deposit',
        'maintenance',
        'termination',
        'utilities',
        'pets',
        'subletting',
        'insurance',
        'default',
        'other'
    ]

    def __init__(self, kernel='rbf', C=1.0, gamma='scale', max_features=5000):
        """
        Initialize the classifier.

        Args:
            kernel: SVM kernel type ('linear', 'rbf', 'poly', 'sigmoid').
            C: Regularization parameter.
            gamma: Kernel coefficient for 'rbf', 'poly', 'sigmoid'.
            max_features: Maximum number of TF-IDF features.
        """
        self.kernel = kernel
        self.C = C
        self.gamma = gamma
        self.max_features = max_features
        self.preprocessor = TextPreprocessor()
        self.pipeline = None
        self.classes_ = None
        self._is_fitted = False

    def _create_pipeline(self):
        """Create the sklearn pipeline with TF-IDF and SVM."""
        return Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=self.max_features,
                ngram_range=(1, 2),
                stop_words='english',
                min_df=1,
                max_df=0.95
            )),
            ('svm', SVC(
                kernel=self.kernel,
                C=self.C,
                gamma=self.gamma,
                probability=True,
                random_state=42
            ))
        ])

    def fit(self, texts, labels):
        """
        Train the classifier on labeled data.

        Args:
            texts: List of text strings (lease clauses).
            labels: List of corresponding labels (clause types).

        Returns:
            self
        """
        # Preprocess texts
        cleaned_texts = self.preprocessor.preprocess_batch(texts)

        # Create and fit pipeline
        self.pipeline = self._create_pipeline()
        self.pipeline.fit(cleaned_texts, labels)

        # Store classes
        self.classes_ = self.pipeline.named_steps['svm'].classes_
        self._is_fitted = True

        return self

    def predict(self, texts):
        """
        Predict clause types for new texts.

        Args:
            texts: List of text strings or single text string.

        Returns:
            Predicted labels (array or single label).
        """
        if not self._is_fitted:
            raise RuntimeError("Classifier must be fitted before prediction.")

        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]

        cleaned_texts = self.preprocessor.preprocess_batch(texts)
        predictions = self.pipeline.predict(cleaned_texts)

        return predictions[0] if single_input else predictions

    def predict_proba(self, texts):
        """
        Get probability estimates for each clause type.

        Args:
            texts: List of text strings or single text string.

        Returns:
            Dictionary mapping clause types to probabilities.
        """
        if not self._is_fitted:
            raise RuntimeError("Classifier must be fitted before prediction.")

        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]

        cleaned_texts = self.preprocessor.preprocess_batch(texts)
        probabilities = self.pipeline.predict_proba(cleaned_texts)

        results = []
        for probs in probabilities:
            result = {cls: float(prob) for cls, prob in zip(self.classes_, probs)}
            results.append(result)

        return results[0] if single_input else results

    def evaluate(self, texts, labels):
        """
        Evaluate classifier performance on test data.

        Args:
            texts: List of test text strings.
            labels: List of true labels.

        Returns:
            Dictionary with evaluation metrics.
        """
        if not self._is_fitted:
            raise RuntimeError("Classifier must be fitted before evaluation.")

        cleaned_texts = self.preprocessor.preprocess_batch(texts)
        predictions = self.pipeline.predict(cleaned_texts)

        return {
            'accuracy': accuracy_score(labels, predictions),
            'classification_report': classification_report(labels, predictions),
            'confusion_matrix': confusion_matrix(labels, predictions).tolist()
        }

    def cross_validate(self, texts, labels, cv=5):
        """
        Perform cross-validation.

        Args:
            texts: List of text strings.
            labels: List of labels.
            cv: Number of cross-validation folds.

        Returns:
            Dictionary with cross-validation scores.
        """
        cleaned_texts = self.preprocessor.preprocess_batch(texts)
        pipeline = self._create_pipeline()
        scores = cross_val_score(pipeline, cleaned_texts, labels, cv=cv)

        return {
            'scores': scores.tolist(),
            'mean': float(scores.mean()),
            'std': float(scores.std())
        }

    def save(self, filepath):
        """
        Save the trained model to disk.

        Args:
            filepath: Path to save the model.
        """
        if not self._is_fitted:
            raise RuntimeError("Cannot save an unfitted classifier.")

        model_data = {
            'pipeline': self.pipeline,
            'classes_': self.classes_,
            'config': {
                'kernel': self.kernel,
                'C': self.C,
                'gamma': self.gamma,
                'max_features': self.max_features
            }
        }
        joblib.dump(model_data, filepath)

    @classmethod
    def load(cls, filepath):
        """
        Load a trained model from disk.

        Args:
            filepath: Path to the saved model.

        Returns:
            Loaded LeaseClauseClassifier instance.
        """
        model_data = joblib.load(filepath)

        classifier = cls(**model_data['config'])
        classifier.pipeline = model_data['pipeline']
        classifier.classes_ = model_data['classes_']
        classifier._is_fitted = True

        return classifier
