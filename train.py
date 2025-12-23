"""
Training script for the lease clause classifier.
"""

import argparse
from sklearn.model_selection import train_test_split

from lease_classifier import LeaseClauseClassifier
from lease_classifier.sample_data import get_sample_data


def main():
    parser = argparse.ArgumentParser(description='Train the lease clause classifier')
    parser.add_argument('--kernel', type=str, default='rbf',
                        choices=['linear', 'rbf', 'poly', 'sigmoid'],
                        help='SVM kernel type')
    parser.add_argument('--C', type=float, default=1.0,
                        help='Regularization parameter')
    parser.add_argument('--output', type=str, default='lease_classifier_model.joblib',
                        help='Output path for the trained model')
    parser.add_argument('--test-size', type=float, default=0.2,
                        help='Fraction of data to use for testing')
    parser.add_argument('--cross-validate', action='store_true',
                        help='Perform cross-validation')
    args = parser.parse_args()

    print("Loading sample data...")
    texts, labels = get_sample_data()
    print(f"Loaded {len(texts)} samples")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=args.test_size, random_state=42, stratify=labels
    )
    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")

    # Create and train classifier
    print(f"\nTraining classifier with {args.kernel} kernel...")
    classifier = LeaseClauseClassifier(kernel=args.kernel, C=args.C)

    if args.cross_validate:
        print("\nPerforming 5-fold cross-validation...")
        cv_results = classifier.cross_validate(texts, labels, cv=5)
        print(f"CV Accuracy: {cv_results['mean']:.4f} (+/- {cv_results['std']*2:.4f})")

    # Train on training data
    classifier.fit(X_train, y_train)
    print("Training complete!")

    # Evaluate on test set
    print("\nEvaluating on test set...")
    results = classifier.evaluate(X_test, y_test)
    print(f"Test Accuracy: {results['accuracy']:.4f}")
    print("\nClassification Report:")
    print(results['classification_report'])

    # Save model
    classifier.save(args.output)
    print(f"\nModel saved to: {args.output}")


if __name__ == '__main__':
    main()
