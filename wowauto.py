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
        "w": KeyCode.from_char("w"),
        "a": KeyCode.from_char("a"),
        "s": KeyCode.from_char("s"),
        "d": KeyCode.from_char("d"),
    }
    if s in simple:
        return simple[s]
    if len(s) == 1:
        return KeyCode.from_char(s)
    # F-keys: only accept two-character names like 'f1'..'f9' (require length == 2)
    if s.startswith("f") and len(s) >= 2 and s[1].isdigit():
        if hasattr(Key, s):
            return getattr(Key, s)
    # F-keys, numpad etc. try attribute on Key for any other named key
    if hasattr(Key, s):
        return getattr(Key, s)
    return key_str


def _parse_button(btn_str: Optional[str]):
    if Button is None or btn_str is None:
        return btn_str
    m = btn_str.lower()
    return {"left": Button.left, "right": Button.right, "middle": Button.middle}.get(m, Button.left)


class SequenceRunner:
    """
    Load JSON sequence definitions and run them. Supports periodic runs.

    JSON formats supported:
    1) sequences map: {"sequences": { "name": [actions] , "name2": {"every": 12, "actions":[...] } } }
    2) top-level map of sequences (same as above)

    Actions examples:
      {"type":"key","action":"press","key":"a"}          # press (down+up)
      {"type":"key","action":"down","key":"shift"}
      {"type":"key","action":"up","key":"shift"}
      {"type":"key","action":"hold","key":"space","duration":0.2}
      {"type":"mouse","action":"click","button":"left","x":100,"y":200}
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
        if not dry_run:
            if KeyboardController is None or MouseController is None:
                raise RuntimeError("pynput is required. Install with: pip install pynput")
            self.kb = KeyboardController()
            self.ms = MouseController()
        else:
            self.kb = None
            self.ms = None

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
            atype = str(act.get("type", "key")).lower()
            if atype == "wait":
                secs = float(act.get("seconds", 0))
                # Add randomness: ±10% variation
                secs_random = secs * random.uniform(0.9, 1.1)
                if self.dry_run:
                    print(f"[dry] wait {secs_random:.3f}s (original: {secs}s)")
                else:
                    await asyncio.sleep(secs_random)
                continue

            if atype == "key":
                action = str(act.get("action", "press")).lower()
                key_raw = act.get("key")
                key = _parse_key(key_raw)
                
                # Add human-like delay before key action: 0.05-0.09s
                pre_delay = random.uniform(0.05, 0.09)
                if not self.dry_run:
                    await asyncio.sleep(pre_delay)
                
                if self.dry_run:
                    print(f"[dry] key {action} {key_raw} (pre-delay: {pre_delay:.3f}s)")
                else:
                    if action == "press":
                        self.kb.press(key)
                        await asyncio.sleep(random.uniform(0.01, 0.03))  # key hold time
                        self.kb.release(key)
                    elif action == "down":
                        self.kb.press(key)
                    elif action == "up":
                        self.kb.release(key)
                    elif action == "hold":
                        dur = float(act.get("duration", 0))
                        dur_random = dur * random.uniform(0.9, 1.1)
                        self.kb.press(key)
                        await asyncio.sleep(dur_random)
                        self.kb.release(key)
                    else:
                        raise ValueError(f"Unknown key action: {action}")

            elif atype == "mouse":
                action = str(act.get("action", "click")).lower()
                btn = _parse_button(act.get("button", "left"))
                x = act.get("x"); y = act.get("y")
                clicks = int(act.get("clicks", 1))
                interval = float(act.get("interval", 0.0))
                
                if self.dry_run:
                    print(f"[dry] mouse {action} {btn} to ({x},{y}) clicks={clicks}")
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
                            await asyncio.sleep(random.uniform(0.01, 0.03))  # click hold time
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
                        dur = float(act.get("duration", 0))
                        dur_random = dur * random.uniform(0.9, 1.1)
                        self.ms.press(btn)
                        await asyncio.sleep(dur_random)
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
                    print(f"[dry] unknown action type: {atype}")
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
                await self._run_actions_once(actions)
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
    #         {"type":"key","action":"press","key":"2"}
    #       ]
    #     },
    #     "press_r_every_10min": {
    #       "every": 600,
    #       "actions": [
    #         {"type":"key","action":"press","key":"r"}
    #       ]
    #     },
    #     "wasd_example": [
    #       {"type":"key","action":"press","key":"w"},
    #       {"type":"wait","seconds":0.1},
    #       {"type":"key","action":"press","key":"a"},
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