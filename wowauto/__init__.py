"""
WoWAuto - Sequence Runner

A powerful JSON-based automation system for World of Warcraft.
"""

__version__ = "2.0.0"

from .sequence_runner import SequenceRunner
from .sequence_loader import SequenceLoader
from .action_executor import ActionExecutor
from .window_detector import WindowDetector

__all__ = [
    "SequenceRunner",
    "SequenceLoader",
    "ActionExecutor",
    "WindowDetector",
]
