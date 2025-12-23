"""
Mapping loader for clause ID to name mapping.
Loads mapping from data_mapping.json file.
"""

import json
from pathlib import Path


class MappingLoader:
    """Load and manage clause ID to name mappings."""

    def __init__(self, mapping_file=None):
        """
        Initialize the mapping loader.

        Args:
            mapping_file: Path to data_mapping.json file.
                         If None, uses default path: data_mapping/data_mapping.json
        """
        if mapping_file is None:
            # Default path relative to project root
            self.mapping_file = Path(__file__).parent.parent / "data_mapping" / "data_mapping.json"
        else:
            self.mapping_file = Path(mapping_file)

        self._id_to_name = {}
        self._name_to_id = {}
        self._load_mapping()

    def _load_mapping(self):
        """Load mapping from JSON file."""
        if not self.mapping_file.exists():
            raise FileNotFoundError(f"Mapping file not found: {self.mapping_file}")

        with open(self.mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            # Handle MongoDB ObjectId format
            if isinstance(item.get('_id'), dict):
                clause_id = item['_id'].get('$oid', '')
            else:
                clause_id = str(item.get('_id', ''))

            name = item.get('name', '')

            if clause_id and name:
                self._id_to_name[clause_id] = name
                # Create normalized name for reverse lookup
                normalized_name = self._normalize_name(name)
                self._name_to_id[normalized_name] = clause_id

    def _normalize_name(self, name):
        """Normalize clause name for consistent lookup."""
        return name.lower().strip().replace(' ', '_').replace('-', '_')

    def get_name(self, clause_id):
        """
        Get clause name from ID.

        Args:
            clause_id: The clause ID (MongoDB ObjectId string).

        Returns:
            Clause name or None if not found.
        """
        return self._id_to_name.get(str(clause_id))

    def get_id(self, name):
        """
        Get clause ID from name.

        Args:
            name: The clause name.

        Returns:
            Clause ID or None if not found.
        """
        normalized = self._normalize_name(name)
        return self._name_to_id.get(normalized)

    def get_all_mappings(self):
        """
        Get all ID to name mappings.

        Returns:
            Dictionary of {id: name} mappings.
        """
        return self._id_to_name.copy()

    def get_all_names(self):
        """
        Get list of all clause names.

        Returns:
            List of clause names.
        """
        return list(self._id_to_name.values())

    def get_all_ids(self):
        """
        Get list of all clause IDs.

        Returns:
            List of clause IDs.
        """
        return list(self._id_to_name.keys())

    def map_labels(self, labels):
        """
        Convert list of label IDs to label names.

        Args:
            labels: List of clause IDs.

        Returns:
            List of clause names.
        """
        mapped = []
        for label in labels:
            name = self.get_name(label)
            if name:
                mapped.append(name)
            else:
                # Keep original if not found in mapping
                mapped.append(str(label))
        return mapped

    def __len__(self):
        """Return number of mappings."""
        return len(self._id_to_name)

    def __contains__(self, item):
        """Check if ID or name exists in mapping."""
        return item in self._id_to_name or self._normalize_name(item) in self._name_to_id
