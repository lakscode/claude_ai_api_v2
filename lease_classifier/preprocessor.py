"""
Text preprocessing utilities for lease clause classification.
"""

import re
import string


class TextPreprocessor:
    """Preprocessor for cleaning and normalizing lease text."""

    def __init__(self, lowercase=True, remove_punctuation=True, remove_numbers=False):
        """
        Initialize the preprocessor.

        Args:
            lowercase: Convert text to lowercase.
            remove_punctuation: Remove punctuation marks.
            remove_numbers: Remove numerical digits.
        """
        self.lowercase = lowercase
        self.remove_punctuation = remove_punctuation
        self.remove_numbers = remove_numbers

    def clean_text(self, text):
        """
        Clean and normalize input text.

        Args:
            text: Raw input text string.

        Returns:
            Cleaned text string.
        """
        if not isinstance(text, str):
            text = str(text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Convert to lowercase
        if self.lowercase:
            text = text.lower()

        # Remove punctuation
        if self.remove_punctuation:
            text = text.translate(str.maketrans('', '', string.punctuation))

        # Remove numbers
        if self.remove_numbers:
            text = re.sub(r'\d+', '', text)

        # Final cleanup
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def preprocess_batch(self, texts):
        """
        Preprocess a batch of texts.

        Args:
            texts: List of text strings.

        Returns:
            List of cleaned text strings.
        """
        return [self.clean_text(text) for text in texts]
