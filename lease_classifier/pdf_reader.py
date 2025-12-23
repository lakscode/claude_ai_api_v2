"""
PDF reader utility for extracting lease clauses from PDF documents.
"""

import re
from pathlib import Path


class PDFReader:
    """Read and extract text/clauses from PDF files."""

    @staticmethod
    def read_pdf(filepath):
        """
        Read entire text content from a PDF file.

        Args:
            filepath: Path to PDF file.

        Returns:
            Full text content as string.
        """
        import fitz  # PyMuPDF

        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"PDF file not found: {filepath}")

        text = ""
        with fitz.open(filepath) as doc:
            for page in doc:
                text += page.get_text()

        return text

    @staticmethod
    def normalize_text(text):
        """
        Normalize text by joining broken lines into complete sentences.

        Args:
            text: Raw text from PDF.

        Returns:
            Normalized text with complete sentences.
        """
        # Replace hyphenated line breaks (word-\nbreak -> wordbreak)
        text = re.sub(r'-\n', '', text)

        # Replace single newlines that break sentences (not followed by uppercase or number)
        # Keep newlines that likely start new sentences/paragraphs
        text = re.sub(r'\n(?![A-Z0-9\(\)\[\]\•\-\*\d])', ' ', text)

        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)

        # Replace multiple newlines with double newline (paragraph break)
        text = re.sub(r'\n\s*\n+', '\n\n', text)

        # Join lines that end without sentence-ending punctuation
        lines = text.split('\n')
        joined_lines = []
        buffer = ""

        for line in lines:
            line = line.strip()
            if not line:
                if buffer:
                    joined_lines.append(buffer.strip())
                    buffer = ""
                continue

            # Check if previous buffer ended mid-sentence
            if buffer:
                # If buffer doesn't end with sentence-ending punctuation, join
                if not re.search(r'[.!?:;]\s*$', buffer):
                    buffer = buffer + ' ' + line
                else:
                    joined_lines.append(buffer.strip())
                    buffer = line
            else:
                buffer = line

        if buffer:
            joined_lines.append(buffer.strip())

        return '\n'.join(joined_lines)

    @staticmethod
    def extract_clauses(filepath, min_length=20):
        """
        Extract individual clauses from a PDF file.
        Joins broken lines into complete sentences before splitting.

        Args:
            filepath: Path to PDF file.
            min_length: Minimum character length for a clause.

        Returns:
            List of extracted clause strings.
        """
        text = PDFReader.read_pdf(filepath)
        # Normalize to join broken lines
        text = PDFReader.normalize_text(text)
        return PDFReader.split_into_clauses(text, min_length)

    @staticmethod
    def split_into_clauses(text, min_length=20):
        """
        Split text into individual clauses (complete sentences).

        Args:
            text: Raw text content.
            min_length: Minimum character length for a clause.

        Returns:
            List of clause strings.
        """
        # First normalize the text
        text = PDFReader.normalize_text(text)

        clauses = []

        # Split by paragraph breaks first
        paragraphs = re.split(r'\n\n+', text)

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if paragraph starts with section number (e.g., "1.", "1.1", "(a)")
            section_match = re.match(r'^(\d+\.?\d*\.?|\([a-z0-9]+\)|[a-z]\))\s*', para, re.IGNORECASE)

            if section_match:
                # This is a numbered section - treat whole paragraph as one clause
                clause = para.strip()
                if len(clause) >= min_length:
                    clauses.append(clause)
            else:
                # Split by sentence endings followed by space and capital letter
                # But keep the period with the sentence
                sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', para)

                for sent in sentences:
                    sent = sent.strip()
                    if len(sent) >= min_length:
                        clauses.append(sent)

        # If no clauses found, try simpler splitting
        if not clauses:
            # Just split by periods followed by space
            simple_split = re.split(r'\.\s+', text)
            for part in simple_split:
                part = part.strip()
                if part and not part.endswith('.'):
                    part = part + '.'
                if len(part) >= min_length:
                    clauses.append(part)

        return clauses

    @staticmethod
    def extract_clauses_by_keywords(filepath, keywords=None):
        """
        Extract clauses that contain specific keywords.

        Args:
            filepath: Path to PDF file.
            keywords: List of keywords to search for. If None, uses common lease keywords.

        Returns:
            List of clauses containing the keywords.
        """
        if keywords is None:
            keywords = [
                'rent', 'payment', 'deposit', 'security',
                'tenant', 'landlord', 'lease', 'termination',
                'maintenance', 'repair', 'utility', 'utilities',
                'pet', 'animal', 'sublet', 'sublease',
                'insurance', 'default', 'breach', 'eviction'
            ]

        clauses = PDFReader.extract_clauses(filepath)

        # Filter clauses containing any keyword
        matched = []
        for clause in clauses:
            clause_lower = clause.lower()
            if any(keyword in clause_lower for keyword in keywords):
                matched.append(clause)

        return matched

    @staticmethod
    def read_pages(filepath, start_page=0, end_page=None):
        """
        Read specific pages from a PDF.

        Args:
            filepath: Path to PDF file.
            start_page: Starting page (0-indexed).
            end_page: Ending page (exclusive). None for all remaining.

        Returns:
            Text content from specified pages.
        """
        import fitz

        filepath = Path(filepath)
        text = ""

        with fitz.open(filepath) as doc:
            if end_page is None:
                end_page = len(doc)

            for page_num in range(start_page, min(end_page, len(doc))):
                text += doc[page_num].get_text()

        return text

    @staticmethod
    def extract_sentences(filepath, min_length=20):
        """
        Extract complete sentences from a PDF file.
        Alias for extract_clauses with better sentence handling.

        Args:
            filepath: Path to PDF file.
            min_length: Minimum character length for a sentence.

        Returns:
            List of complete sentences.
        """
        return PDFReader.extract_clauses(filepath, min_length)
