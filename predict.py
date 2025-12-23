"""
Prediction script for classifying lease clauses.
"""

import argparse
import sys

from lease_classifier import LeaseClauseClassifier
from lease_classifier.sample_data import get_clause_descriptions


def main():
    parser = argparse.ArgumentParser(description='Classify lease clauses')
    parser.add_argument('--model', type=str, default='lease_classifier_model.joblib',
                        help='Path to the trained model')
    parser.add_argument('--text', type=str, nargs='+',
                        help='Text to classify (can provide multiple)')
    parser.add_argument('--file', type=str,
                        help='File containing texts to classify (one per line)')
    parser.add_argument('--show-proba', action='store_true',
                        help='Show probability scores for all classes')
    parser.add_argument('--top-k', type=int, default=3,
                        help='Show top K predictions when using --show-proba')
    args = parser.parse_args()

    # Load model
    print(f"Loading model from: {args.model}")
    try:
        classifier = LeaseClauseClassifier.load(args.model)
    except FileNotFoundError:
        print(f"Error: Model file '{args.model}' not found.")
        print("Please train a model first using: python train.py")
        sys.exit(1)

    # Get texts to classify
    texts = []
    if args.text:
        texts.extend(args.text)
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            texts.extend([line.strip() for line in f if line.strip()])

    if not texts:
        print("Error: No text provided. Use --text or --file to provide input.")
        sys.exit(1)

    # Get clause descriptions
    descriptions = get_clause_descriptions()

    # Classify each text
    print("\n" + "="*60)
    for i, text in enumerate(texts, 1):
        print(f"\nText {i}: {text[:100]}{'...' if len(text) > 100 else ''}")
        print("-" * 40)

        if args.show_proba:
            proba = classifier.predict_proba(text)
            sorted_proba = sorted(proba.items(), key=lambda x: x[1], reverse=True)
            print(f"Top {args.top_k} predictions:")
            for j, (clause_type, prob) in enumerate(sorted_proba[:args.top_k], 1):
                print(f"  {j}. {clause_type}: {prob:.4f}")
                print(f"     ({descriptions.get(clause_type, 'No description')})")
        else:
            prediction = classifier.predict(text)
            print(f"Classification: {prediction}")
            print(f"Description: {descriptions.get(prediction, 'No description')}")

    print("\n" + "="*60)


if __name__ == '__main__':
    main()
