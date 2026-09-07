"""
Public Dataset Loader Interface & Utilities.

Provides abstract data loading and streaming for external business datasets.
Includes sample generation for offline CI and reproducible testing.
"""

from abc import ABC, abstractmethod
import csv
import json
import os
from typing import List, Dict, Any, Generator, Optional
from backend.data.schema import Invoice, Vendor


class BaseDatasetAdapter(ABC):
    """Abstract base class for converting an external dataset into canonical models."""

    @abstractmethod
    def adapt_invoices(self, raw_data_path: str, limit: Optional[int] = None) -> List[Invoice]:
        """Convert external invoice rows into canonical Invoice objects."""
        pass

    @abstractmethod
    def adapt_vendors(self, raw_data_path: str) -> List[Vendor]:
        """Extract unique vendors and map to canonical Vendor objects."""
        pass


class PublicDataLoader:
    """Manages raw dataset acquisition, caching, and adapter invocation."""

    def __init__(self, raw_data_dir: str = "data/raw"):
        self.raw_data_dir = raw_data_dir
        os.makedirs(raw_data_dir, exist_ok=True)

    def load_csv(self, filepath: str, encoding: str = "utf-8") -> List[Dict[str, Any]]:
        """Read CSV records safely."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Public dataset file not found: {filepath}")
        
        with open(filepath, mode="r", encoding=encoding, errors="replace") as f:
            reader = csv.DictReader(f)
            return [row for row in reader]

    def stream_csv(self, filepath: str, chunk_size: int = 1000) -> Generator[List[Dict[str, Any]], None, None]:
        """Stream large CSV datasets in chunks to conserve memory."""
        with open(filepath, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            chunk = []
            for row in reader:
                chunk.append(row)
                if len(chunk) >= chunk_size:
                    yield chunk
                    chunk = []
            if chunk:
                yield chunk
