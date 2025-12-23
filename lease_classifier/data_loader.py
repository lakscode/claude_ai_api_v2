"""
Data loader for custom lease clause datasets.
Supports JSON, CSV, and Excel formats with ID-to-name mapping.
"""

import json
import csv
from pathlib import Path


class DataLoader:
    """Load training data from custom dataset files with optional ID mapping."""

    def __init__(self, mapping_file=None):
        """
        Initialize DataLoader with optional mapping file.

        Args:
            mapping_file: Path to data_mapping.json for ID-to-name mapping.
        """
        self.mapping = None
        if mapping_file:
            self._load_mapping(mapping_file)

    def _load_mapping(self, mapping_file):
        """Load ID-to-name mapping from JSON file."""
        mapping_path = Path(mapping_file)
        if not mapping_path.exists():
            raise FileNotFoundError(f"Mapping file not found: {mapping_path}")

        with open(mapping_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.mapping = {}
        for item in data:
            # Handle MongoDB ObjectId format
            if isinstance(item.get('_id'), dict):
                clause_id = item['_id'].get('$oid', '')
            else:
                clause_id = str(item.get('_id', ''))

            name = item.get('name', '')
            if clause_id and name:
                self.mapping[clause_id] = name

    def _map_label(self, label):
        """Map label ID to name if mapping exists."""
        if self.mapping and label in self.mapping:
            return self.mapping[label]
        return label

    def load_excel_with_labels(self, filepath, text_column='text', label_column='label'):
        """
        Load dataset from Excel file with text and label columns.
        Labels are mapped using data_mapping.json if available.

        Args:
            filepath: Path to Excel file.
            text_column: Name of the text column.
            label_column: Name of the label column.

        Returns:
            Tuple of (texts, labels) lists.
        """
        import pandas as pd

        filepath = Path(filepath)
        df = pd.read_excel(filepath, engine='openpyxl')

        texts = []
        labels = []

        for _, row in df.iterrows():
            text = str(row.get(text_column, '')).strip()
            label = str(row.get(label_column, '')).strip()

            if text and text.lower() != 'nan' and label and label.lower() != 'nan':
                # Map label ID to name
                mapped_label = self._map_label(label)
                texts.append(text)
                labels.append(mapped_label)

        return texts, labels

    def load_folder_with_labels(self, folder_path, text_column='text', label_column='label'):
        """
        Load datasets from Excel files in a folder.
        Each Excel file contains 'text' and 'label' columns.
        Labels are mapped using data_mapping.json.

        Args:
            folder_path: Path to folder containing Excel files.
            text_column: Name of the text column.
            label_column: Name of the label column.

        Returns:
            Tuple of (texts, labels) lists.
        """
        import pandas as pd

        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Dataset folder not found: {folder}")

        all_texts = []
        all_labels = []

        # Find all Excel files
        excel_files = list(folder.glob("*.xlsx")) + list(folder.glob("*.xls"))

        if not excel_files:
            raise FileNotFoundError(f"No Excel files found in: {folder}")

        for excel_file in sorted(excel_files):
            # Skip temporary Excel files
            if excel_file.name.startswith('~$'):
                continue

            try:
                df = pd.read_excel(excel_file, engine='openpyxl')
                count = 0

                for _, row in df.iterrows():
                    text = str(row.get(text_column, '')).strip()
                    label = str(row.get(label_column, '')).strip()

                    if text and text.lower() != 'nan' and label and label.lower() != 'nan':
                        # Map label ID to name
                        mapped_label = self._map_label(label)
                        all_texts.append(text)
                        all_labels.append(mapped_label)
                        count += 1

                print(f"Loaded: {excel_file.name} ({count} samples)")

            except Exception as e:
                print(f"Error loading {excel_file.name}: {e}")

        return all_texts, all_labels

    @classmethod
    def load_with_mapping(cls, data_path, mapping_file=None):
        """
        Load dataset with optional ID-to-name mapping.

        Args:
            data_path: Path to dataset folder or file.
            mapping_file: Path to data_mapping.json file.

        Returns:
            Tuple of (texts, labels) lists.
        """
        loader = cls(mapping_file=mapping_file)
        data_path = Path(data_path)

        if data_path.is_dir():
            return loader.load_folder_with_labels(data_path)
        else:
            return loader.load_excel_with_labels(data_path)

    # Keep static methods for backward compatibility
    @staticmethod
    def load_json(filepath):
        """Load dataset from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        training_data = data.get('training_data', data)
        if isinstance(training_data, dict):
            training_data = training_data.get('training_data', [])

        texts = []
        labels = []

        for item in training_data:
            text = item.get('text', '').strip()
            label = item.get('label', '').strip()

            if text and label:
                texts.append(text)
                labels.append(label)

        return texts, labels

    @staticmethod
    def load_csv(filepath, text_column='text', label_column='label'):
        """Load dataset from CSV file."""
        texts = []
        labels = []

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                text = row.get(text_column, '').strip()
                label = row.get(label_column, '').strip()

                if text and label:
                    texts.append(text)
                    labels.append(label)

        return texts, labels

    @staticmethod
    def load(filepath):
        """
        Auto-detect format and load dataset.
        For folder with mapping, use load_with_mapping() instead.
        """
        filepath = Path(filepath)
        extension = filepath.suffix.lower()

        if extension == '.json':
            return DataLoader.load_json(filepath)
        elif extension == '.csv':
            return DataLoader.load_csv(filepath)
        elif extension in ['.xlsx', '.xls']:
            import pandas as pd
            df = pd.read_excel(filepath, engine='openpyxl')
            texts = []
            labels = []
            for _, row in df.iterrows():
                text = str(row.get('text', '')).strip()
                label = str(row.get('label', '')).strip()
                if text and text.lower() != 'nan' and label and label.lower() != 'nan':
                    texts.append(text)
                    labels.append(label)
            return texts, labels
        else:
            raise ValueError(f"Unsupported format: {extension}")

    @staticmethod
    def get_dataset_stats(texts, labels):
        """Get statistics about the dataset."""
        from collections import Counter
        label_counts = Counter(labels)

        return {
            'total_samples': len(texts),
            'unique_labels': len(label_counts),
            'samples_per_label': dict(label_counts),
            'avg_text_length': sum(len(t) for t in texts) / len(texts) if texts else 0,
            'min_text_length': min(len(t) for t in texts) if texts else 0,
            'max_text_length': max(len(t) for t in texts) if texts else 0,
        }

    @staticmethod
    def save_json(filepath, texts, labels):
        """Save dataset to JSON format."""
        data = {
            "metadata": {
                "description": "Lease clause training data",
                "total_samples": len(texts)
            },
            "training_data": [
                {"text": text, "label": label}
                for text, label in zip(texts, labels)
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def save_csv(filepath, texts, labels):
        """Save dataset to CSV format."""
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['text', 'label'])
            for text, label in zip(texts, labels):
                writer.writerow([text, label])
