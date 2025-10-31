"""Main sequence runner orchestrating all components."""
import asyncio
import random
from typing import Any, Dict, List, Optional

from .sequence_loader import SequenceLoader
from .action_executor import ActionExecutor
from .window_detector import WindowDetector


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
    """

    def __init__(self, dry_run: bool = False):
        """
        Initialize sequence runner.
        
        Args:
            dry_run: If True, print actions instead of executing them
        """
        self.dry_run = dry_run
        self.loader = SequenceLoader()
        self.executor = ActionExecutor(dry_run=dry_run)
        self.window_detector = WindowDetector()
        self._tasks: Dict[str, asyncio.Task] = {}

    @property
    def data(self) -> Dict[str, Any]:
        """Get loaded sequence data."""
        return self.loader.data

    def load_file(self, path: str) -> List[str]:
        """
        Load sequences from a JSON file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            List of sequence names loaded
        """
        return self.loader.load_file(path)

    def list_sequences(self) -> List[str]:
        """Get list of all loaded sequence names."""
        return self.loader.list_sequences()

    async def _run_actions_once(self, actions: List[Dict[str, Any]]):
        """Run a list of actions once."""
        for act in actions:
            # Check if WoW is still active before each action
            if not self.dry_run and not self.window_detector.is_target_window_active():
                if self.dry_run:
                    print("[dry] World of Warcraft not active - pausing sequence")
                # Wait for WoW to become active again
                while not self.window_detector.is_target_window_active():
                    await asyncio.sleep(self.window_detector.check_interval)
                if self.dry_run:
                    print("[dry] World of Warcraft active again - resuming sequence")

            await self.executor.execute_action(act)

    async def _periodic_worker(self, name: str, interval: float, actions: List[Dict[str, Any]]):
        """Worker for periodic sequence execution."""
        try:
            while True:
                # Only run if World of Warcraft is active
                if self.dry_run or self.window_detector.is_target_window_active():
                    await self._run_actions_once(actions)
                else:
                    # Wait for WoW to become active
                    while not self.window_detector.is_target_window_active():
                        await asyncio.sleep(self.window_detector.check_interval)
                
                # Add randomness to periodic interval: ±10%
                interval_random = interval * random.uniform(0.9, 1.1)
                await asyncio.sleep(interval_random)
        except asyncio.CancelledError:
            return

    def start_repeating(self, name: str):
        """
        Start a repeating sequence defined with an 'every' field. Non-blocking.
        
        Args:
            name: Sequence name
            
        Returns:
            asyncio.Task object
            
        Raises:
            KeyError: If sequence doesn't exist
            ValueError: If sequence doesn't have valid 'every' field
            RuntimeError: If sequence is already running
        """
        seq = self.loader.get_sequence(name)
        if isinstance(seq, list):
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
        """
        Stop a running sequence.
        
        Args:
            name: Sequence name
        """
        t = self._tasks.pop(name, None)
        if t:
            t.cancel()

    def stop_all(self):
        """Stop all running sequences."""
        for n, t in list(self._tasks.items()):
            t.cancel()
        self._tasks.clear()

    async def run_once(self, name: str):
        """
        Run a sequence once (list or object with actions).
        
        Args:
            name: Sequence name
            
        Raises:
            KeyError: If sequence doesn't exist
        """
        seq = self.loader.get_sequence(name)
        if isinstance(seq, list):
            actions = seq
        else:
            actions = seq.get("actions", [])
        await self._run_actions_once(actions)

    def run_once_sync(self, name: str):
        """
        Run a sequence once synchronously (blocking).
        
        Args:
            name: Sequence name
        """
        asyncio.run(self.run_once(name))

    async def start_all_repeating(self):
        """Start all sequences that define 'every' concurrently."""
        for name, seq in self.data.items():
            if isinstance(seq, dict) and "every" in seq:
                try:
                    self.start_repeating(name)
                except Exception as e:
                    print(f"failed to start {name}: {e}")

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
    # Example usage
    runner = SequenceRunner(dry_run=True)
    try:
        runner.load_file("example_sequences.json")
        print("Sequences:", runner.list_sequences())
        runner.run_forever()
    except FileNotFoundError:
        print("Place example_sequences.json next to this script to test.")
