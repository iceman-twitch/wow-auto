"""Sequence loader for JSON configuration files."""
import json
from pathlib import Path
from typing import Any, Dict, List


class SequenceLoader:
    """Loads sequence definitions from JSON files."""
    
    def __init__(self):
        """Initialize sequence loader."""
        self.data: Dict[str, Any] = {}
    
    def load_file(self, path: str) -> List[str]:
        """
        Load sequences from a JSON file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            List of sequence names loaded
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON format is invalid
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)
        with p.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict) and "sequences" in payload and isinstance(payload["sequences"], dict):
            self.data.update(payload["sequences"])
        elif isinstance(payload, dict):
            self.data.update(payload)
        else:
            raise ValueError("Unsupported JSON top-level: expected object with sequences")
        return list(self.data.keys())
    
    def list_sequences(self) -> List[str]:
        """Get list of all loaded sequence names."""
        return list(self.data.keys())
    
    def get_sequence(self, name: str) -> Any:
        """
        Get sequence definition by name.
        
        Args:
            name: Sequence name
            
        Returns:
            Sequence definition (list or dict)
            
        Raises:
            KeyError: If sequence doesn't exist
        """
        if name not in self.data:
            raise KeyError(name)
        return self.data[name]
