"""
Train classifier with custom dataset.
Supports Excel files with text/label columns and ID-to-name mapping.
"""

import argparse
from pathlib import Path
from sklearn.model_selection import train_test_split

from lease_classifier import LeaseClauseClassifier, DataLoader


def main():
    parser = argparse.ArgumentParser(description='Train classifier with custom dataset')
    parser.add_argument('--data', type=str, default='test_data',
                        help='Path to dataset folder or file (default: test_data)')
    parser.add_argument('--mapping', type=str, default='data_mapping/data_mapping.json',
                        help='Path to data_mapping.json for ID-to-name mapping')
    parser.add_argument('--kernel', type=str, default='rbf',
                        choices=['linear', 'rbf', 'poly', 'sigmoid'],
                        help='SVM kernel type')
    parser.add_argument('--C', type=float, default=1.0,
                        help='Regularization parameter')
    parser.add_argument('--output', type=str, default='lease_model.joblib',
                        help='Output path for the trained model')
    parser.add_argument('--test-size', type=float, default=0.2,
                        help='Fraction of data to use for testing')
    parser.add_argument('--cross-validate', action='store_true',
                        help='Perform cross-validation')
    parser.add_argument('--stats', action='store_true',
                        help='Show dataset statistics')
    parser.add_argument('--no-mapping', action='store_true',
                        help='Skip ID-to-name mapping (use raw labels)')
    args = parser.parse_args()

    # Check if mapping file exists
    mapping_file = None
    if not args.no_mapping:
        mapping_path = Path(args.mapping)
        if mapping_path.exists():
            mapping_file = args.mapping
            print(f"Using mapping file: {args.mapping}")
        else:
            print(f"Warning: Mapping file not found: {args.mapping}")
            print("Using raw labels. Use --no-mapping to suppress this warning.")

    # Load custom dataset with mapping
    print(f"\nLoading dataset from: {args.data}")

    if mapping_file:
        texts, labels = DataLoader.load_with_mapping(args.data, mapping_file)
    else:
        texts, labels = DataLoader.load_with_mapping(args.data, None)

    print(f"Loaded {len(texts)} samples")

    # Show statistics
    if args.stats:
        stats = DataLoader.get_dataset_stats(texts, labels)
        print("\nDataset Statistics:")
        print(f"  Total samples: {stats['total_samples']}")
        print(f"  Unique labels: {stats['unique_labels']}")
        print(f"  Avg text length: {stats['avg_text_length']:.1f} chars")
        print("\n  Samples per label:")
        for label, count in sorted(stats['samples_per_label'].items()):
            print(f"    {label}: {count}")
        print()

    # Check minimum samples
    if len(texts) < 10:
        print("Warning: Very small dataset. Consider adding more training samples.")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=args.test_size, random_state=42
    )
    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")

    # Create classifier
    classifier = LeaseClauseClassifier(kernel=args.kernel, C=args.C)

    # Cross-validation
    if args.cross_validate and len(texts) >= 10:
        print("\nPerforming 5-fold cross-validation...")
        cv_results = classifier.cross_validate(texts, labels, cv=5)
        print(f"CV Accuracy: {cv_results['mean']:.4f} (+/- {cv_results['std']*2:.4f})")

    # Train
    print(f"\nTraining with {args.kernel} kernel...")
    classifier.fit(X_train, y_train)
    print("Training complete!")

    # Evaluate
    if len(X_test) > 0:
        print("\nEvaluating on test set...")
        results = classifier.evaluate(X_test, y_test)
        print(f"Test Accuracy: {results['accuracy']:.4f}")
        print("\nClassification Report:")
        print(results['classification_report'])

    # Save
    classifier.save(args.output)
    print(f"\nModel saved to: {args.output}")

    # Print learned classes
    print(f"\nLearned clause types ({len(classifier.classes_)}):")
    for cls in sorted(classifier.classes_):
        print(f"  - {cls}")


if __name__ == '__main__':
    main()
