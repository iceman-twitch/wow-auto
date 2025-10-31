"""
FormAuto - GUI for WoW Automation

A graphical interface for managing and running WoW automation sequences.
"""

__version__ = "2.0.0"

from .settings_form import SettingsForm
from .background_runner import BackgroundRunner
from .key_listener import GlobalKeyListener
from .settings_manager import SettingsManager
from .stop_window import StopWindow

__all__ = [
    "SettingsForm",
    "BackgroundRunner",
    "GlobalKeyListener",
    "SettingsManager",
    "StopWindow",
]
