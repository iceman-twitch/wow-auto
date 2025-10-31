"""Global keyboard listener for hotkey detection."""
from typing import Optional

from pynput import keyboard


class GlobalKeyListener:
    """Global keyboard listener using pynput to detect toggle key anywhere."""
    
    def __init__(self, toggle_callback, toggle_key: str = "á"):
        """
        Initialize global key listener.
        
        Args:
            toggle_callback: Function to call when toggle key is pressed
            toggle_key: Key to listen for (default: "á")
        """
        self.toggle_callback = toggle_callback
        self.toggle_key = toggle_key.lower()
        self._listener: Optional[keyboard.Listener] = None
        
    def start(self):
        """Start listening for global key presses."""
        if self._listener and self._listener.running:
            return
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()
        
    def stop(self):
        """Stop listening for global key presses."""
        if self._listener:
            self._listener.stop()
            self._listener = None
            
    def _on_press(self, key):
        """Handle key press event."""
        try:
            pressed_key = None
            
            # Try to get character
            if hasattr(key, 'char') and key.char is not None:
                pressed_key = key.char.lower()
                
            # Try to get name for special keys
            elif hasattr(key, 'name'):
                pressed_key = key.name.lower()
                
            # Fallback to string representation
            else:
                pressed_key = str(key).replace("Key.", "").replace("'", "").lower()
                
            print(f"Detected key: '{pressed_key}', looking for: '{self.toggle_key}'")
            
            if pressed_key == self.toggle_key:
                print("TOGGLE ACTIVATED!")
                self.toggle_callback()
                
        except Exception as e:
            print(f"Key listener error: {e}")
            
        return None  # Let all keys pass through
