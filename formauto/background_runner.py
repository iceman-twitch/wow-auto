"""Background runner for executing sequences in a separate thread."""
import asyncio
import threading
from pathlib import Path
from typing import List, Optional

from wowauto import SequenceRunner


class BackgroundRunner:
    """Run SequenceRunner in a dedicated thread + asyncio loop so the UI never blocks."""
    
    def __init__(self, json_path: str, selected_sequences: List[str], dry_run: bool = False):
        """
        Initialize background runner.
        
        Args:
            json_path: Path to JSON sequence file
            selected_sequences: List of sequence names to run
            dry_run: If True, print actions instead of executing them
        """
        self.json_path = json_path
        self.selected_sequences = list(selected_sequences)
        self.dry_run = dry_run

        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._stop_event = threading.Event()
        self._exc: Optional[BaseException] = None

    def start(self):
        """Start the background runner thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._thread_main, daemon=True, name="wautopy-runner")
        self._thread.start()

    def _thread_main(self):
        """Main thread function."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._main())
        except BaseException as e:
            self._exc = e
        finally:
            try:
                if self._loop and not self._loop.is_closed():
                    self._loop.close()
            except Exception:
                pass

    async def _main(self):
        """Main async function for running sequences."""
        runner = SequenceRunner(dry_run=self.dry_run)
        runner.load_file(self.json_path)

        # Start repeating sequences; run one-shots once.
        for name in self.selected_sequences:
            seq = runner.data.get(name)
            if isinstance(seq, dict) and float(seq.get("every", 0)) > 0:
                runner.start_repeating(name)
            else:
                asyncio.create_task(runner.run_once(name))

        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(0.5)
        finally:
            try:
                runner.stop_all()
            except Exception:
                pass

    def stop(self, timeout: float = 2.0):
        """
        Stop the background runner.
        
        Args:
            timeout: Maximum time to wait for thread to stop
            
        Returns:
            Exception if runner failed, None otherwise
        """
        self._stop_event.set()
        if self._loop:
            try:
                self._loop.call_soon_threadsafe(lambda: None)
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout)
        return self._exc
