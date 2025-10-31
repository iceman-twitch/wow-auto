"""Key and button parsing utilities."""
from typing import Optional

try:
    from pynput.keyboard import Key, KeyCode
    from pynput.mouse import Button
except Exception:
    Key = None
    KeyCode = None
    Button = None


def parse_key(key_str: str):
    """Map common names (w,a,s,d, ctrl, shift, etc.) to pynput Key/KeyCode."""
    if Key is None or KeyCode is None:
        return key_str
    s = str(key_str).lower()
    simple = {
        "shift": Key.shift,
        "ctrl": Key.ctrl,
        "control": Key.ctrl,
        "alt": Key.alt,
        "enter": Key.enter,
        "return": Key.enter,
        "space": Key.space,
        "tab": Key.tab,
        "esc": Key.esc,
        "escape": Key.esc,
        "backspace": Key.backspace,
        "delete": Key.delete,
        "left": Key.left,
        "right": Key.right,
        "up": Key.up,
        "down": Key.down,
        # Arrow keys with multiple aliases
        "leftarrow": Key.left,
        "left_arrow": Key.left,
        "arrow_left": Key.left,
        "rightarrow": Key.right,
        "right_arrow": Key.right,
        "arrow_right": Key.right,
        "uparrow": Key.up,
        "up_arrow": Key.up,
        "arrow_up": Key.up,
        "downarrow": Key.down,
        "down_arrow": Key.down,
        "arrow_down": Key.down,
        # Home/End/PageUp/PageDown
        "home": Key.home,
        "end": Key.end,
        "pageup": Key.page_up,
        "page_up": Key.page_up,
        "pgup": Key.page_up,
        "pagedown": Key.page_down,
        "page_down": Key.page_down,
        "pgdn": Key.page_down,
        # Insert/Print Screen
        "insert": Key.insert,
        "ins": Key.insert,
        "printscreen": Key.print_screen,
        "print_screen": Key.print_screen,
        "prtsc": Key.print_screen,
        # Function keys (F1-F12)
        "f1": Key.f1,
        "f2": Key.f2,
        "f3": Key.f3,
        "f4": Key.f4,
        "f5": Key.f5,
        "f6": Key.f6,
        "f7": Key.f7,
        "f8": Key.f8,
        "f9": Key.f9,
        "f10": Key.f10,
        "f11": Key.f11,
        "f12": Key.f12,
        # Numpad keys
        "num0": Key.num_lock,  # This is actually num_lock, fixing below
        "num1": Key.num_lock,  # These need to be fixed
        "num2": Key.num_lock,
        "num3": Key.num_lock,
        "num4": Key.num_lock,
        "num5": Key.num_lock,
        "num6": Key.num_lock,
        "num7": Key.num_lock,
        "num8": Key.num_lock,
        "num9": Key.num_lock,
        "numlock": Key.num_lock,
        "num_lock": Key.num_lock,
        # Basic letter keys
        "w": KeyCode.from_char("w"),
        "a": KeyCode.from_char("a"),
        "s": KeyCode.from_char("s"),
        "d": KeyCode.from_char("d"),
    }
    
    # Handle numpad keys properly
    numpad_keys = {
        "numpad0": KeyCode.from_vk(96),
        "numpad1": KeyCode.from_vk(97),
        "numpad2": KeyCode.from_vk(98),
        "numpad3": KeyCode.from_vk(99),
        "numpad4": KeyCode.from_vk(100),
        "numpad5": KeyCode.from_vk(101),
        "numpad6": KeyCode.from_vk(102),
        "numpad7": KeyCode.from_vk(103),
        "numpad8": KeyCode.from_vk(104),
        "numpad9": KeyCode.from_vk(105),
        "num0": KeyCode.from_vk(96),
        "num1": KeyCode.from_vk(97),
        "num2": KeyCode.from_vk(98),
        "num3": KeyCode.from_vk(99),
        "num4": KeyCode.from_vk(100),
        "num5": KeyCode.from_vk(101),
        "num6": KeyCode.from_vk(102),
        "num7": KeyCode.from_vk(103),
        "num8": KeyCode.from_vk(104),
        "num9": KeyCode.from_vk(105),
    }
    
    # Check simple keys first
    if s in simple:
        return simple[s]
    
    # Check numpad keys
    if s in numpad_keys:
        return numpad_keys[s]
    
    # Single character keys
    if len(s) == 1:
        return KeyCode.from_char(s)
    
    # F-keys: try attribute on Key for any other named key
    if hasattr(Key, s):
        return getattr(Key, s)
    
    return key_str


def parse_button(btn_str: Optional[str]):
    """Parse mouse button string to pynput Button."""
    if Button is None or btn_str is None:
        return btn_str
    m = btn_str.lower()
    return {"left": Button.left, "right": Button.right, "middle": Button.middle}.get(m, Button.left)
