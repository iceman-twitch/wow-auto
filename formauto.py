import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import threading
import asyncio
import time
from typing import List, Optional

from wowauto import SequenceRunner  # requires wowauto.py in same folder/project

# default settings folder -> %USERPROFILE%\Documents\wowautopy\settings.json
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
        self._started_event = threading.Event()
        self._exc: Optional[BaseException] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._started_event.clear()
        self._thread = threading.Thread(target=self._thread_main, daemon=True, name="wautopy-runner")
        self._thread.start()
        # wait briefly for startup confirmation (non-blocking callers can poll started)
        self._started_event.wait(2.0)

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
        # instantiate SequenceRunner inside this loop/thread
        runner = SequenceRunner(dry_run=self.dry_run)
        # load file
        runner.load_file(self.json_path)

        # schedule work: start repeating sequences, and one-shots run once
        for name in self.selected_sequences:
            seq = runner.data.get(name)
            if isinstance(seq, dict) and float(seq.get("every", 0)) > 0:
                # start repeating in the runner's loop
                runner.start_repeating(name)
            else:
                # run once (non-blocking)
                asyncio.create_task(runner.run_once(name))

        self._started_event.set()

        # keep running until stop requested
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(0.5)
        finally:
            # request runner to stop repeating tasks and cancel
            try:
                runner.stop_all()
            except Exception:
                pass

    def stop(self, timeout: float = 2.0):
        # signal stop and wait for thread to end
        self._stop_event.set()
        if self._loop:
            try:
                self._loop.call_soon_threadsafe(lambda: None)
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout)
        return self._exc


class SettingsForm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WoW Auto - Settings")
        # slightly larger default size and allow resizing so widgets never get clipped
        self.geometry("760x520")
        self.resizable(True, True)

        # ensure default settings folder/file exist (attempt to create)
        try:
            DEFAULT_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
            if not DEFAULT_SETTINGS_FILE.exists():
                default_settings = {
                    "json_path": "",
                    "selected_sequences": [],
                    "toggle_key": "",
                    "is_running": False,
                }
                DEFAULT_SETTINGS_FILE.write_text(json.dumps(default_settings, indent=2), encoding="utf-8")
        except Exception as e:
            # can't create folder/file -> inform user and fall back to home folder
            try:
                messagebox.showwarning(
                    "Warning",
                    f"Could not create settings folder '{DEFAULT_SETTINGS_DIR}': {e}\n"
                    "Falling back to home folder for settings."
                )
            except Exception:
                pass
            # fallback
            fallback = Path.home() / "wautopy"
            try:
                fallback.mkdir(parents=True, exist_ok=True)
                fb_file = fallback / "settings.json"
                if not fb_file.exists():
                    fb_file.write_text(json.dumps({
                        "json_path": "",
                        "selected_sequences": [],
                        "toggle_key": "",
                        "is_running": False,
                    }, indent=2), encoding="utf-8")
                # update defaults to fallback
                global DEFAULT_SETTINGS_DIR, DEFAULT_SETTINGS_FILE
                DEFAULT_SETTINGS_DIR = fallback
                DEFAULT_SETTINGS_FILE = fb_file
            except Exception:
                # last resort: ignore and continue; saving will fail later with message
                pass

        # state
        self.json_path_var = tk.StringVar()
        self.save_dir_var = tk.StringVar(value=str(DEFAULT_SETTINGS_DIR))
        self.sequence_names: list[str] = []

        # toggle key and running status
        self.toggle_key_var = tk.StringVar(value="")  # key used to toggle auto mode (e.g. "F8" or "r")
        self.is_running = False
        self.run_status_var = tk.StringVar(value="Not running")

        # background runner
        self._bg_runner: Optional[BackgroundRunner] = None
        self._bg_exc: Optional[BaseException] = None

        # Widgets
        row = 0
        tk.Label(self, text="Select sequence JSON:").grid(column=0, row=row, sticky="w", padx=8, pady=6)
        tk.Entry(self, textvariable=self.json_path_var, width=64).grid(column=0, row=row + 1, columnspan=2, padx=8, sticky="we")
        tk.Button(self, text="Browse...", command=self.browse_json).grid(column=2, row=row + 1, padx=8, sticky="w")

        row += 2
        tk.Button(self, text="Load sequences from file", command=self.load_sequences).grid(column=0, row=row, padx=8, pady=6, sticky="w")

        row += 1
        tk.Label(self, text="Sequences (select one or more):").grid(column=0, row=row, sticky="w", padx=8)
        self.listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, width=80, height=10)
        self.listbox.grid(column=0, row=row + 1, columnspan=3, padx=8, sticky="we")

        row += 2
        tk.Label(self, text="Settings save folder:").grid(column=0, row=row, sticky="w", padx=8, pady=6)
        tk.Entry(self, textvariable=self.save_dir_var, width=64).grid(column=0, row=row + 1, columnspan=2, padx=8, sticky="we")
        tk.Button(self, text="Open...", command=self.open_save_dir).grid(column=2, row=row + 1, padx=8, sticky="w")

        row += 2
        # Toggle key UI
        tk.Label(self, text="Toggle key (press while app has focus):").grid(column=0, row=row, sticky="w", padx=8)
        tk.Entry(self, textvariable=self.toggle_key_var, width=20).grid(column=1, row=row, sticky="w", padx=8)
        tk.Button(self, text="Set to last key press", command=self._set_last_key).grid(column=2, row=row, sticky="w", padx=8)

        row += 1
        # Running status and toggle button
        tk.Label(self, text="Auto mode status:").grid(column=0, row=row, sticky="w", padx=8, pady=6)
        self.run_status_label = tk.Label(self, textvariable=self.run_status_var, width=20, anchor="w", fg="red")
        self.run_status_label.grid(column=1, row=row, sticky="w")
        tk.Button(self, text="Toggle Run", command=self.toggle_running, width=12).grid(column=2, row=row, sticky="e", padx=8)

        row += 1
        # Added a label to show background thread state / errors
        tk.Label(self, text="Runner thread:").grid(column=0, row=row, sticky="w", padx=8, pady=6)
        self.thread_status_var = tk.StringVar(value="stopped")
        self.thread_status_label = tk.Label(self, textvariable=self.thread_status_var, width=40, anchor="w")
        self.thread_status_label.grid(column=1, row=row, columnspan=2, sticky="w")

        row += 1
        tk.Button(self, text="Save settings", command=self.save_settings, width=20).grid(column=0, row=row, padx=8, pady=12, sticky="w")
        tk.Button(self, text="Save & Close", command=self.save_and_close, width=20).grid(column=1, row=row, padx=8, sticky="w")
        tk.Button(self, text="Quit", command=self._on_close, width=12).grid(column=2, row=row, padx=8, sticky="e")

        self.status = tk.Label(self, text="", anchor="w")
        self.status.grid(column=0, row=row + 1, columnspan=3, padx=8, pady=6, sticky="we")

        # track last key pressed for easy set
        self._last_key_pressed = ""
        # bind key events while app has focus
        self.bind_all("<Key>", self._on_keypress)

        # try to preload existing settings
        self.load_existing_settings()

        # start polling UI to reflect thread state
        self.after(500, self._poll_status)

    def browse_json(self):
        p = filedialog.askopenfilename(title="Select JSON file", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if p:
            self.json_path_var.set(p)
            # auto-load sequences
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

        # determine sequences
        seqs = []
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
        folder = Path(self.save_dir_var.get())
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
        # gather selected sequences
        selected = [self.sequence_names[i] for i in self.listbox.curselection()] if self.sequence_names else []
        settings = {
            "json_path": self.json_path_var.get().strip(),
            "selected_sequences": selected,
            "toggle_key": self.toggle_key_var.get().strip(),
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
        # try default settings locations
        candidates = [DEFAULT_SETTINGS_FILE, DEFAULT_SETTINGS_DIR / "settings.json"]
        for c in candidates:
            if c.exists():
                try:
                    data = json.loads(c.read_text(encoding="utf-8"))
                    json_path = data.get("json_path", "")
                    sel = data.get("selected_sequences", [])
                    toggle = data.get("toggle_key", "")
                    is_running = data.get("is_running", False)
                    if json_path:
                        self.json_path_var.set(json_path)
                        self.load_sequences()
                        # select sequences if present
                        for i, name in enumerate(self.sequence_names):
                            if name in sel:
                                self.listbox.selection_set(i)
                    # set toggle key and running status
                    self.toggle_key_var.set(str(toggle))
                    self.is_running = bool(is_running)
                    self._update_run_status()
                    # set save dir to parent of loaded settings
                    self.save_dir_var.set(str(c.parent))
                    self.status.config(text=f"Loaded settings from {c}")
                except Exception:
                    pass
                break

    # new: toggle running state
    def toggle_running(self):
        if not self.is_running:
            # start background runner
            json_path = self.json_path_var.get().strip()
            if not json_path:
                messagebox.showinfo("Info", "Please select a JSON file first.")
                return
            selected = [self.sequence_names[i] for i in self.listbox.curselection()] if self.sequence_names else []
            if not selected:
                messagebox.showinfo("Info", "Please select at least one sequence to run.")
                return
            # save settings before starting
            self.save_settings()
            try:
                self._bg_runner = BackgroundRunner(json_path=json_path, selected_sequences=selected, dry_run=False)
                self._bg_runner.start()
                self.is_running = True
                self._update_run_status()
                self.thread_status_var.set("running")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start runner: {e}")
        else:
            # stop background runner
            try:
                exc = None
                if self._bg_runner:
                    exc = self._bg_runner.stop()
                    self._bg_runner = None
                self.is_running = False
                self._update_run_status()
                self.thread_status_var.set("stopped")
                if exc:
                    messagebox.showerror("Runner error", f"Background runner raised: {exc}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to stop runner: {e}")

    def _update_run_status(self):
        if self.is_running:
            self.run_status_var.set("Running")
            self.run_status_label.config(fg="green")
        else:
            self.run_status_var.set("Not running")
            self.run_status_label.config(fg="red")

    # record last key pressed and use it for quick set
    def _on_keypress(self, event: tk.Event):
        # event.keysym is e.g. 'F8', 'r', 'Return'
        ks = getattr(event, "keysym", "")
        if not ks:
            return
        self._last_key_pressed = ks
        # if the pressed key matches configured toggle key -> toggle running
        cfg = self.toggle_key_var.get().strip()
        if cfg and ks.lower() == cfg.lower():
            # avoid toggling while typing in entries: check focus widget class
            fw = self.focus_get()
            if isinstance(fw, tk.Entry):
                return
            self.toggle_running()

    def _set_last_key(self):
        if self._last_key_pressed:
            self.toggle_key_var.set(self._last_key_pressed)
            self.status.config(text=f"Toggle key set to: {self._last_key_pressed}")
        else:
            self.status.config(text="No key press recorded yet. Click inside the window and press a key to record it.")

    def _poll_status(self):
        # update thread status and detect background exceptions
        if self._bg_runner and self._bg_runner._thread:
            t = self._bg_runner._thread
            if t.is_alive():
                self.thread_status_var.set("running")
            else:
                self.thread_status_var.set("stopped")
                # check for exception
                if self._bg_runner._exc:
                    self.thread_status_var.set("error")
                    messagebox.showerror("Runner error", f"Background runner failed: {self._bg_runner._exc}")
                    self._bg_runner = None
                    self.is_running = False
                    self._update_run_status()
        else:
            self.thread_status_var.set("stopped")
        # schedule next poll
        self.after(500, self._poll_status)

    def _on_close(self):
        # ensure background runner stopped before exiting
        if self._bg_runner:
            try:
                self._bg_runner.stop(timeout=1.0)
            except Exception:
                pass
            self._bg_runner = None
        # save settings on close
        try:
            self.save_settings()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = SettingsForm()
    app.mainloop()