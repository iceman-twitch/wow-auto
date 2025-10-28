# -*- coding: utf-8 -*-
import json
import os
import threading
import asyncio
from pathlib import Path
from typing import List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from pynput import keyboard

from wowauto import SequenceRunner  # requires wowauto.py in same folder/project

# Default settings folder -> %USERPROFILE%\Documents\wowautopy\settings.json
DEFAULT_SETTINGS_DIR = Path.home() / "Documents" / "wowautopy"
DEFAULT_SETTINGS_FILE = DEFAULT_SETTINGS_DIR / "settings.json"


class BackgroundRunner:
    """Run SequenceRunner in a dedicated thread + asyncio loop so the UI never blocks."""
    def __init__(self, json_path: str, selected_sequences: List[str], dry_run: bool = False):
        self.json_path = json_path
        self.selected_sequences = list(selected_sequences)
        self.dry_run = dry_run

        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._stop_event = threading.Event()
        self._exc: Optional[BaseException] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._thread_main, daemon=True, name="wautopy-runner")
        self._thread.start()

    def _thread_main(self):
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
        self._stop_event.set()
        if self._loop:
            try:
                self._loop.call_soon_threadsafe(lambda: None)
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout)
        return self._exc


class GlobalKeyListener:
    """Global keyboard listener using pynput to detect toggle key anywhere."""
    def __init__(self, toggle_callback, toggle_key: str = "á"):
        self.toggle_callback = toggle_callback
        self.toggle_key = toggle_key.lower()
        self._listener: Optional[keyboard.Listener] = None
        
    def start(self):
        if self._listener and self._listener.running:
            return
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()
        
    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None
            
    def _on_press(self, key):
        try:
            # Handle character keys
            if hasattr(key, 'char') and key.char:
                if key.char.lower() == self.toggle_key:
                    self.toggle_callback()
                    return False  # Suppress the key
            # Handle named keys (like Key.f8)
            key_name = str(key).replace("Key.", "").replace("'", "").lower()
            if key_name == self.toggle_key:
                self.toggle_callback()
                return False  # Suppress the key
        except Exception:
            pass
        return True  # Allow other keys to pass through


class SettingsForm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WoW Auto - Settings")
        # Smaller default size and resizable
        self.geometry("500x490")
        self.resizable(False, False)

        # Instance-level settings paths
        self.settings_dir: Path = DEFAULT_SETTINGS_DIR
        self.settings_file: Path = DEFAULT_SETTINGS_FILE
        self._ensure_settings_location()

        # UI state
        self.json_path_var = tk.StringVar()
        self.save_dir_var = tk.StringVar(value=str(self.settings_dir))
        self.sequence_names: List[str] = []

        # Default toggle key: 'á'
        self.toggle_key_var = tk.StringVar(value="á")
        self.is_running = False
        self.run_status_var = tk.StringVar(value="Not running")

        # Background runner
        self._bg_runner: Optional[BackgroundRunner] = None
        
        # Global key listener (will be started after UI is built)
        self._key_listener: Optional[GlobalKeyListener] = None

        # Build UI
        row = 0
        tk.Label(self, text="Select sequence JSON:").grid(column=0, row=row, sticky="w", padx=8, pady=6)
        tk.Entry(self, textvariable=self.json_path_var, width=64).grid(column=0, row=row + 1, columnspan=2, padx=8, sticky="we")
        tk.Button(self, text="Browse...", command=self.browse_json).grid(column=2, row=row + 1, padx=8, sticky="w")

        row += 2
        tk.Button(self, text="Load sequences from file", command=self.load_sequences).grid(column=0, row=row, padx=8, pady=6, sticky="w")

        row += 1
        tk.Label(self, text="Sequences (select one or more):").grid(column=0, row=row, sticky="w", padx=8)
        
        # Create frame for listbox with scrollbar
        listbox_frame = tk.Frame(self)
        listbox_frame.grid(column=0, row=row + 1, columnspan=3, padx=8, pady=4, sticky="we")
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)
        
        # Listbox with smaller height
        self.listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, width=80, height=6)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        row += 2
        tk.Label(self, text="Settings save folder:").grid(column=0, row=row, sticky="w", padx=8, pady=6)
        tk.Entry(self, textvariable=self.save_dir_var, width=64).grid(column=0, row=row + 1, columnspan=2, padx=8, sticky="we")
        tk.Button(self, text="Open...", command=self.open_save_dir).grid(column=2, row=row + 1, padx=8, sticky="w")

        row += 2
        tk.Label(self, text="Global toggle key (works anywhere):").grid(column=0, row=row, sticky="w", padx=8)
        tk.Entry(self, textvariable=self.toggle_key_var, width=20).grid(column=1, row=row, sticky="w", padx=8)
        tk.Button(self, text="Update listener", command=self._restart_global_listener).grid(column=2, row=row, sticky="w", padx=8)

        row += 1
        tk.Label(self, text="Auto mode status:").grid(column=0, row=row, sticky="w", padx=8, pady=6)
        self.run_status_label = tk.Label(self, textvariable=self.run_status_var, width=20, anchor="w", fg="red")
        self.run_status_label.grid(column=1, row=row, sticky="w")
        tk.Button(self, text="Toggle Run", command=self.toggle_running, width=12).grid(column=2, row=row, sticky="e", padx=8)

        row += 1
        tk.Label(self, text="Runner thread:").grid(column=0, row=row, sticky="w", padx=8, pady=6)
        self.thread_status_var = tk.StringVar(value="stopped")
        self.thread_status_label = tk.Label(self, textvariable=self.thread_status_var, width=40, anchor="w")
        self.thread_status_label.grid(column=1, row=row, columnspan=2, sticky="w")

        row += 1
        tk.Label(self, text="Global listener:").grid(column=0, row=row, sticky="w", padx=8, pady=6)
        self.listener_status_var = tk.StringVar(value="starting...")
        tk.Label(self, textvariable=self.listener_status_var, width=40, anchor="w", fg="orange").grid(column=1, row=row, columnspan=2, sticky="w")

        row += 1
        tk.Button(self, text="Save settings", command=self.save_settings, width=20).grid(column=0, row=row, padx=8, pady=12, sticky="w")
        tk.Button(self, text="Save & Close", command=self.save_and_close, width=20).grid(column=1, row=row, padx=8, sticky="w")
        tk.Button(self, text="Quit", command=self._on_close, width=12).grid(column=2, row=row, padx=8, sticky="e")

        self.status = tk.Label(self, text="", anchor="w")
        self.status.grid(column=0, row=row + 1, columnspan=3, padx=8, pady=6, sticky="we")

        # Configure column weights for resizing
        self.grid_columnconfigure(0, weight=1)

        # Load existing settings if present
        self.load_existing_settings()

        # NOW start global listener after all UI vars are created
        self._start_global_listener()

        # Poll thread state
        self.after(500, self._poll_status)

    def _ensure_settings_location(self):
        """Ensure settings dir and default file exist; on failure, fall back to home\\wautopy."""
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            if not self.settings_file.exists():
                default_settings = {
                    "json_path": "",
                    "selected_sequences": [],
                    "toggle_key": "á",
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
                        "toggle_key": "á",
                        "is_running": False,
                    }, indent=2), encoding="utf-8")
                self.settings_dir = fallback
                self.settings_file = fb_file
            except Exception:
                pass

    def _start_global_listener(self):
        """Start global keyboard listener."""
        toggle_key = self.toggle_key_var.get().strip() or "á"
        self._key_listener = GlobalKeyListener(self.toggle_running, toggle_key)
        self._key_listener.start()
        self.listener_status_var.set("running")
        self.status.config(text=f"Global hotkey listener active. Press '{toggle_key}' anywhere to toggle.")

    def _restart_global_listener(self):
        """Restart listener with new toggle key."""
        if self._key_listener:
            self._key_listener.stop()
        self._start_global_listener()
        self.status.config(text=f"Global listener restarted. Toggle key: {self.toggle_key_var.get()}")

    def browse_json(self):
        p = filedialog.askopenfilename(title="Select JSON file", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if p:
            self.json_path_var.set(p)
            self.load_sequences()

    def load_sequences(self):
        path = self.json_path_var.get().strip()
        if not path:
            messagebox.showinfo("Info", "Please choose a JSON file first.")
            return
        p = Path(path)
        if not p.exists():
            messagebox.showerror("Error", f"File not found: {path}")
            return
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse JSON: {e}")
            return

        if isinstance(payload, dict) and "sequences" in payload and isinstance(payload["sequences"], dict):
            seqs = list(payload["sequences"].keys())
        elif isinstance(payload, dict):
            seqs = list(payload.keys())
        elif isinstance(payload, list):
            seqs = ["_default"]
        else:
            seqs = []

        self.sequence_names = seqs
        self.listbox.delete(0, tk.END)
        for name in seqs:
            self.listbox.insert(tk.END, name)

        self.status.config(text=f"Loaded {len(seqs)} sequence(s) from file.")

    def open_save_dir(self):
        folder = Path(self.save_dir_var.get()).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create/open folder: {e}")
            return
        try:
            os.startfile(str(folder))
        except Exception:
            messagebox.showinfo("Info", f"Settings folder: {folder}")

    def save_settings(self):
        selected = [self.sequence_names[i] for i in self.listbox.curselection()] if self.sequence_names else []
        settings = {
            "json_path": self.json_path_var.get().strip(),
            "selected_sequences": selected,
            "toggle_key": self.toggle_key_var.get().strip() or "á",
            "is_running": self.is_running,
        }
        save_dir = Path(self.save_dir_var.get()).expanduser()
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create settings folder: {e}")
            return

        save_file = save_dir / "settings.json"
        try:
            save_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write settings: {e}")
            return

        self.status.config(text=f"Settings saved to: {save_file}")
        return save_file

    def save_and_close(self):
        saved = self.save_settings()
        if saved:
            self._on_close()

    def load_existing_settings(self):
        candidates = [self.settings_file, self.settings_dir / "settings.json"]
        for c in candidates:
            if c.exists():
                try:
                    data = json.loads(c.read_text(encoding="utf-8"))
                    json_path = data.get("json_path", "")
                    sel = data.get("selected_sequences", [])
                    toggle = data.get("toggle_key", "á")
                    is_running = data.get("is_running", False)
                    if json_path:
                        self.json_path_var.set(json_path)
                        self.load_sequences()
                        for i, name in enumerate(self.sequence_names):
                            if name in sel:
                                self.listbox.selection_set(i)
                    self.toggle_key_var.set(str(toggle) if str(toggle) else "á")
                    self.is_running = bool(is_running)
                    self._update_run_status()
                    self.save_dir_var.set(str(c.parent))
                    self.status.config(text=f"Loaded settings from {c}")
                except Exception:
                    pass
                break

    def toggle_running(self):
        if not self.is_running:
            json_path = self.json_path_var.get().strip()
            if not json_path:
                self.status.config(text="Error: Please select a JSON file first.")
                return
            selected = [self.sequence_names[i] for i in self.listbox.curselection()] if self.sequence_names else []
            if not selected:
                self.status.config(text="Error: Please select at least one sequence to run.")
                return
            self.save_settings()
            try:
                self._bg_runner = BackgroundRunner(json_path=json_path, selected_sequences=selected, dry_run=False)
                self._bg_runner.start()
                self.is_running = True
                self._update_run_status()
                self.thread_status_var.set("running")
                self.status.config(text="Auto mode started! Press toggle key to stop.")
            except Exception as e:
                self.status.config(text=f"Failed to start runner: {e}")
        else:
            try:
                exc = None
                if self._bg_runner:
                    exc = self._bg_runner.stop()
                    self._bg_runner = None
                self.is_running = False
                self._update_run_status()
                self.thread_status_var.set("stopped")
                if exc:
                    self.status.config(text=f"Runner stopped with error: {exc}")
                else:
                    self.status.config(text="Auto mode stopped.")
            except Exception as e:
                self.status.config(text=f"Failed to stop runner: {e}")

    def _update_run_status(self):
        if self.is_running:
            self.run_status_var.set("Running")
            self.run_status_label.config(fg="green")
        else:
            self.run_status_var.set("Not running")
            self.run_status_label.config(fg="red")

    def _poll_status(self):
        if self._bg_runner and self._bg_runner._thread:
            t = self._bg_runner._thread
            if t.is_alive():
                self.thread_status_var.set("running")
            else:
                self.thread_status_var.set("stopped")
                if self._bg_runner._exc:
                    self.thread_status_var.set("error")
                    self.status.config(text=f"Background runner failed: {self._bg_runner._exc}")
                    self._bg_runner = None
                    self.is_running = False
                    self._update_run_status()
        else:
            self.thread_status_var.set("stopped")
        self.after(500, self._poll_status)

    def _on_close(self):
        if self._key_listener:
            self._key_listener.stop()
        if self._bg_runner:
            try:
                self._bg_runner.stop(timeout=1.0)
            except Exception:
                pass
            self._bg_runner = None
        try:
            self.save_settings()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = SettingsForm()
    app.mainloop()