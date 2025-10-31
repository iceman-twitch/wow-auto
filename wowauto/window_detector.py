"""Window detection utilities for World of Warcraft."""
import win32gui


def get_active_window_title() -> str:
    """Get the title of the currently active window."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(hwnd)
    except Exception:
        return ""


class WindowDetector:
    """Detects if World of Warcraft is the active window."""
    
    def __init__(self, target_window_titles: list = None, check_interval: float = 1.0):
        """
        Initialize window detector.
        
        Args:
            target_window_titles: List of window titles to check for (default: ["World of Warcraft"])
            check_interval: How often to check window status in seconds
        """
        self._target_window_titles = target_window_titles or ["World of Warcraft"]
        self._check_interval = check_interval
    
    def is_target_window_active(self) -> bool:
        """Check if World of Warcraft is the active window."""
        # Disabled window checking - always return True
        return True
        
        # Original code (disabled):
        # try:
        #     current_title = get_active_window_title()
        #     for target in self._target_window_titles:
        #         if target.lower() in current_title.lower():
        #             return True
        #     return False
        # except Exception:
        #     return False
    
    @property
    def check_interval(self) -> float:
        """Get the window check interval."""
        return self._check_interval
