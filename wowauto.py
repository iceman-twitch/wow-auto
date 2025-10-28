import json
import asyncio
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from pynput.keyboard import Controller as KeyboardController, Key, KeyCode
    from pynput.mouse import Controller as MouseController, Button
except Exception:
    KeyboardController = None
    MouseController = None
    Key = None
    KeyCode = None
    Button = None


def _parse_key(key_str: str):
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


def _parse_button(btn_str: Optional[str]):
    if Button is None or btn_str is None:
        return btn_str
    m = btn_str.lower()
    return {"left": Button.left, "right": Button.right, "middle": Button.middle}.get(m, Button.left)


def _get_active_window_title() -> str:
    """Get the title of the currently active window."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(hwnd)
    except Exception:
        return ""


class SequenceRunner:
    """
    Load JSON sequence definitions and run them. Supports periodic runs.
    Only runs when World of Warcraft is the active window.

    JSON formats supported:
    1) sequences map: {"sequences": { "name": [actions] , "name2": {"every": 12, "actions":[...] } } }
    2) top-level map of sequences (same as above)

    Actions examples:
      {"type":"key","action":"press","key":"a"}          # press (down+up)
      {"type":"key","action":"press","key":"left"}       # left arrow key
      {"type":"key","action":"press","key":"up_arrow"}   # up arrow key
      {"type":"key","action":"press","key":"f1"}         # F1 function key
      {"type":"key","action":"press","key":"numpad5"}    # numpad 5
      {"type":"key","action":"press","key":"a","chance":50}  # 50% chance to press
      {"type":"key","action":"press","key":"a","duration":2.5}  # hold for exactly 2.5 seconds (no randomness)
      {"type":"key","action":"down","key":"shift"}
      {"type":"key","action":"up","key":"shift"}
      {"type":"key","action":"hold","key":"space","duration":0.2}
      {"type":"mouse","action":"click","button":"left","x":100,"y":200}
      {"type":"mouse","action":"click","button":"left","x":100,"y":200,"chance":75}  # 75% chance to click
      {"type":"wait","seconds":1.5}
      {"type":"repeat","every":12, "actions":[ ... ]}    # can be used inline but better defined as a sequence with every
    Useful for: press '2' every 12s and press 'r' every 10min:
    {
      "sequences": {
        "press_2": {"every":12, "actions":[ {"type":"key","action":"press","key":"2"} ]},
        "press_r": {"every":600, "actions":[ {"type":"key","action":"press","key":"r"} ]}
      }
    }
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.data: Dict[str, Any] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._last_mouse_pos: Optional[tuple] = None  # Track last mouse position
        self._window_check_interval = 1.0  # Check window every 1 second
        self._target_window_titles = ["World of Warcraft"]  # List of valid window titles
        if not dry_run:
            if KeyboardController is None or MouseController is None:
                raise RuntimeError("pynput is required. Install with: pip install pynput")
            self.kb = KeyboardController()
            self.ms = MouseController()
        else:
            self.kb = None
            self.ms = None

    def _is_target_window_active(self) -> bool:
        """Check if World of Warcraft is the active window."""
        try:
            current_title = _get_active_window_title()
            for target in self._target_window_titles:
                if target.lower() in current_title.lower():
                    return True
            return False
        except Exception:
            return False

    def _check_chance(self, action: Dict[str, Any]) -> bool:
        """Check if action should execute based on chance (1-100). Returns True if no chance specified."""
        chance = action.get("chance")
        if chance is None:
            return True
        chance = int(chance)
        if chance <= 0:
            return False
        if chance >= 100:
            return True
        return random.randint(1, 100) <= chance

    def load_file(self, path: str) -> List[str]:
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
        return list(self.data.keys())

    async def _run_actions_once(self, actions: List[Dict[str, Any]]):
        for act in actions:
            # Check if WoW is still active before each action
            if not self.dry_run and not self._is_target_window_active():
                if self.dry_run:
                    print("[dry] World of Warcraft not active - pausing sequence")
                # Wait for WoW to become active again
                while not self._is_target_window_active():
                    await asyncio.sleep(self._window_check_interval)
                if self.dry_run:
                    print("[dry] World of Warcraft active again - resuming sequence")

            # Check chance - skip action if chance fails
            if not self._check_chance(act):
                if self.dry_run:
                    chance = act.get("chance", 100)
                    print(f"[dry] skipping action due to chance ({chance}%)")
                continue

            atype = str(act.get("type", "key")).lower()
            if atype == "wait":
                secs = float(act.get("seconds", 0))
                # Add randomness: ±10% variation
                secs_random = secs * random.uniform(0.9, 1.1)
                if self.dry_run:
                    chance = act.get("chance", 100)
                    print(f"[dry] wait {secs_random:.3f}s (original: {secs}s) [chance: {chance}%]")
                else:
                    await asyncio.sleep(secs_random)
                continue

            if atype == "key":
                action = str(act.get("action", "press")).lower()
                key_raw = act.get("key")
                key = _parse_key(key_raw)
                duration = act.get("duration")  # Exact duration if specified
                
                # Add human-like delay before key action: 0.05-0.09s
                pre_delay = random.uniform(0.05, 0.09)
                if not self.dry_run:
                    await asyncio.sleep(pre_delay)
                
                if self.dry_run:
                    chance = act.get("chance", 100)
                    duration_info = f" duration={duration}s" if duration else ""
                    print(f"[dry] key {action} {key_raw} (pre-delay: {pre_delay:.3f}s){duration_info} [chance: {chance}%]")
                else:
                    if action == "press":
                        self.kb.press(key)
                        if duration is not None:
                            # Use exact duration (no randomness)
                            await asyncio.sleep(float(duration))
                        else:
                            # Use random key hold time
                            await asyncio.sleep(random.uniform(0.01, 0.03))
                        self.kb.release(key)
                    elif action == "down":
                        self.kb.press(key)
                    elif action == "up":
                        self.kb.release(key)
                    elif action == "hold":
                        if duration is not None:
                            # Use exact duration (no randomness)
                            dur = float(duration)
                        else:
                            # Fall back to old behavior with randomness
                            dur = float(act.get("duration", 0))
                            dur = dur * random.uniform(0.9, 1.1)
                        self.kb.press(key)
                        await asyncio.sleep(dur)
                        self.kb.release(key)
                    else:
                        raise ValueError(f"Unknown key action: {action}")

            elif atype == "mouse":
                action = str(act.get("action", "click")).lower()
                btn = _parse_button(act.get("button", "left"))
                x = act.get("x"); y = act.get("y")
                clicks = int(act.get("clicks", 1))
                interval = float(act.get("interval", 0.0))
                duration = act.get("duration")  # Exact duration if specified
                
                if self.dry_run:
                    chance = act.get("chance", 100)
                    duration_info = f" duration={duration}s" if duration else ""
                    print(f"[dry] mouse {action} {btn} to ({x},{y}) clicks={clicks}{duration_info} [chance: {chance}%]")
                else:
                    # Step 1: Move mouse if needed (without clicking yet)
                    mouse_moved = False
                    if x is not None and y is not None:
                        current_pos = (int(x), int(y))
                        if self._last_mouse_pos != current_pos:
                            self.ms.position = current_pos
                            self._last_mouse_pos = current_pos
                            mouse_moved = True
                    
                    # Step 2: If mouse was moved, wait 0.05-0.09s before clicking (human reaction time)
                    if mouse_moved:
                        move_settle_delay = random.uniform(0.05, 0.09)
                        await asyncio.sleep(move_settle_delay)
                    
                    # Step 3: Now perform the mouse action (click, hold, etc.)
                    if action == "click":
                        for i in range(clicks):
                            self.ms.press(btn)
                            if duration is not None:
                                # Use exact duration (no randomness)
                                await asyncio.sleep(float(duration))
                            else:
                                # Use random click hold time
                                await asyncio.sleep(random.uniform(0.01, 0.03))
                            self.ms.release(btn)
                            if interval and i < clicks - 1:
                                interval_random = interval * random.uniform(0.9, 1.1)
                                await asyncio.sleep(interval_random)
                            elif i < clicks - 1:
                                # Small delay between clicks even without explicit interval
                                await asyncio.sleep(random.uniform(0.05, 0.09))
                    elif action == "down":
                        self.ms.press(btn)
                    elif action == "up":
                        self.ms.release(btn)
                    elif action == "hold":
                        if duration is not None:
                            # Use exact duration (no randomness)
                            dur = float(duration)
                        else:
                            # Fall back to old behavior with randomness
                            dur = float(act.get("duration", 0))
                            dur = dur * random.uniform(0.9, 1.1)
                        self.ms.press(btn)
                        await asyncio.sleep(dur)
                        self.ms.release(btn)
                    else:
                        raise ValueError(f"Unknown mouse action: {action}")

            elif atype == "repeat":
                # inline repeat: run contained actions once, then wait 'every' seconds and repeat count times
                every = float(act.get("every", 0))
                count = act.get("count", None)
                inner = act.get("actions", [])
                runs = int(count) if count is not None else None
                i = 0
                while runs is None or i < runs:
                    await self._run_actions_once(inner)
                    i += 1
                    if every <= 0:
                        break
                    every_random = every * random.uniform(0.9, 1.1)
                    await asyncio.sleep(every_random)

            else:
                if self.dry_run:
                    chance = act.get("chance", 100)
                    print(f"[dry] unknown action type: {atype} [chance: {chance}%]")
                else:
                    raise ValueError(f"Unknown action type: {atype}")

            # per-action delay with randomness: delay to delay*1.1
            delay = float(act.get("delay", 0))
            if delay:
                delay_random = delay * random.uniform(1.0, 1.1)
                if self.dry_run:
                    print(f"[dry] sleep {delay_random:.3f}s (original delay: {delay}s)")
                else:
                    await asyncio.sleep(delay_random)

    async def _periodic_worker(self, name: str, interval: float, actions: List[Dict[str, Any]]):
        # Run first immediately, then wait interval repeatedly with randomness
        try:
            while True:
                # Only run if World of Warcraft is active
                if self.dry_run or self._is_target_window_active():
                    await self._run_actions_once(actions)
                else:
                    # Wait for WoW to become active
                    while not self._is_target_window_active():
                        await asyncio.sleep(self._window_check_interval)
                
                # Add randomness to periodic interval: ±10%
                interval_random = interval * random.uniform(0.9, 1.1)
                await asyncio.sleep(interval_random)
        except asyncio.CancelledError:
            # clean up if needed
            return

    def start_repeating(self, name: str):
        """Start a repeating sequence defined with an 'every' field. Non-blocking."""
        if name not in self.data:
            raise KeyError(name)
        seq = self.data[name]
        if isinstance(seq, list):
            # list w/out interval -> run once
            raise ValueError("Sequence is a list (one-shot). To repeat, define an object with 'every' and 'actions'.")
        every = float(seq.get("every", 0))
        actions = seq.get("actions", [])
        if every <= 0:
            raise ValueError("Invalid 'every' (must be > 0) for repeating sequence")
        if name in self._tasks:
            raise RuntimeError(f"Sequence '{name}' already running")
        task = asyncio.create_task(self._periodic_worker(name, every, actions))
        self._tasks[name] = task
        return task

    def stop(self, name: str):
        t = self._tasks.pop(name, None)
        if t:
            t.cancel()

    def stop_all(self):
        for n, t in list(self._tasks.items()):
            t.cancel()
        self._tasks.clear()

    async def run_once(self, name: str):
        """Run a sequence once (list or object with actions)."""
        if name not in self.data:
            raise KeyError(name)
        seq = self.data[name]
        if isinstance(seq, list):
            actions = seq
        else:
            actions = seq.get("actions", [])
        await self._run_actions_once(actions)

    def run_once_sync(self, name: str):
        asyncio.run(self.run_once(name))

    async def start_all_repeating(self):
        """Start all sequences that define 'every' concurrently."""
        for name, seq in self.data.items():
            if isinstance(seq, dict) and "every" in seq:
                try:
                    self.start_repeating(name)
                except Exception as e:
                    print(f"failed to start {name}: {e}")

    # convenience to run forever (useful for scripts)
    def run_forever(self):
        """Run all repeating sequences and block until cancelled (Ctrl+C)."""
        async def _main():
            await self.start_all_repeating()
            # keep alive while tasks run
            try:
                while True:
                    await asyncio.sleep(3600)
            except asyncio.CancelledError:
                pass

        try:
            asyncio.run(_main())
        except KeyboardInterrupt:
            self.stop_all()


if __name__ == "__main__":
    # Example JSON to place next to this script (example_sequences.json):
    # {
    #   "sequences": {
    #     "press_2_every_12s": {
    #       "every": 12,
    #       "actions": [
    #         {"type":"key","action":"press","key":"2","chance":75}
    #       ]
    #     },
    #     "press_r_every_10min": {
    #       "every": 600,
    #       "actions": [
    #         {"type":"key","action":"press","key":"r","duration":1.5}
    #       ]
    #     },
    #     "wasd_example": [
    #       {"type":"key","action":"press","key":"w","chance":90,"duration":0.5},
    #       {"type":"wait","seconds":0.1},
    #       {"type":"key","action":"press","key":"a","chance":50},
    #       {"type":"wait","seconds":0.1},
    #       {"type":"key","action":"press","key":"s"},
    #       {"type":"wait","seconds":0.1},
    #       {"type":"key","action":"press","key":"d"}
    #     ]
    #   }
    # }
    runner = SequenceRunner(dry_run=True)
    try:
        runner.load_file("example_sequences.json")
        print("Sequences:", runner.list_sequences())
        # start all repeating sequences (dry-run)
        asyncio.run(runner.start_all_repeating())
        # keep running briefly in dry-run to show behaviour
        try:
            asyncio.run(asyncio.sleep(1))
        except Exception:
            pass
    except FileNotFoundError:
        print("Place example_sequences.json next to this script to test.")