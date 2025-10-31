"""Settings management for formauto."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Default settings folder -> %USERPROFILE%\Documents\wowautopy\settings.json
DEFAULT_SETTINGS_DIR = Path.home() / "Documents" / "wowautopy"
DEFAULT_SETTINGS_FILE = DEFAULT_SETTINGS_DIR / "settings.json"


class SettingsManager:
    """Manages loading and saving of formauto settings."""
    
    def __init__(self, settings_dir: Optional[Path] = None, settings_file: Optional[Path] = None):
        """
        Initialize settings manager.
        
        Args:
            settings_dir: Directory for settings (default: Documents/wowautopy)
            settings_file: Settings file path (default: settings_dir/settings.json)
        """
        self.settings_dir = settings_dir or DEFAULT_SETTINGS_DIR
        self.settings_file = settings_file or DEFAULT_SETTINGS_FILE
        self._ensure_settings_location()
    
    def _ensure_settings_location(self):
        """Ensure settings dir and default file exist; on failure, fall back to home\\wautopy."""
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            if not self.settings_file.exists():
                default_settings = {
                    "json_path": "",
                    "selected_sequences": [],
                    "toggle_key": "f8",
                    "is_running": False,
                }
                self.settings_file.write_text(json.dumps(default_settings, indent=2), encoding="utf-8")
        except Exception:
            fallback = Path.home() / "wautopy"
            try:
                fallback.mkdir(parents=True, exist_ok=True)
                fb_file = fallback / "settings.json"
                if not fb_file.exists():
                    fb_file.write_text(json.dumps({
                        "json_path": "",
                        "selected_sequences": [],
                        "toggle_key": "f8",
                        "is_running": False,
                    }, indent=2), encoding="utf-8")
                self.settings_dir = fallback
                self.settings_file = fb_file
            except Exception:
                pass
    
    def save(self, json_path: str, selected_sequences: List[str], toggle_key: str, is_running: bool) -> Path:
        """
        Save settings to file.
        
        Args:
            json_path: Path to JSON sequence file
            selected_sequences: List of selected sequence names
            toggle_key: Global hotkey for toggling
            is_running: Current running state
            
        Returns:
            Path to saved settings file
            
        Raises:
            Exception: If save fails
        """
        settings = {
            "json_path": json_path,
            "selected_sequences": selected_sequences,
            "toggle_key": toggle_key,
            "is_running": is_running,
        }
        
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise Exception(f"Failed to create settings folder: {e}")

        try:
            self.settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
        except Exception as e:
            raise Exception(f"Failed to write settings: {e}")
        
        return self.settings_file
    
    def load(self) -> Optional[Dict[str, Any]]:
        """
        Load settings from file.
        
        Returns:
            Settings dict or None if load fails
        """
        candidates = [self.settings_file, self.settings_dir / "settings.json"]
        for c in candidates:
            if c.exists():
                try:
                    data = json.loads(c.read_text(encoding="utf-8"))
                    # Update settings file path to the one we found
                    self.settings_file = c
                    self.settings_dir = c.parent
                    return data
                except Exception:
                    continue
        return None
