"""Main GUI form for formauto settings and control."""
import json
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from .background_runner import BackgroundRunner
from .key_listener import GlobalKeyListener
from .settings_manager import SettingsManager
from .stop_window import StopWindow


# WoW-inspired color scheme - Brown/Gold theme
COLORS = {
    'bg_dark': '#2b1f14',        # Dark brown background
    'bg_medium': '#3d2a1f',      # Medium brown
    'bg_light': '#4d3a2a',       # Light brown
    'gold': '#d4af37',           # Gold accent
    'gold_light': '#f0d98c',     # Light gold
    'gold_dark': '#b8942c',      # Dark gold
    'text': '#f0e6d2',           # Light beige text
    'text_dim': '#c0b49e',       # Dimmed text
    'success': '#4ade80',        # Green for success
    'error': '#ef4444',          # Red for error
    'warning': '#fb923c',        # Orange for warning
}


class RoundedButton(tk.Canvas):
    """A custom button with rounded corners and hover effects."""
    
    def __init__(self, parent, text, command, width=120, height=35, 
                 bg=COLORS['gold_dark'], hover_bg=COLORS['gold'], 
                 text_color=COLORS['bg_dark'], font=("Segoe UI", 10, "bold"), **kwargs):
        super().__init__(parent, width=width, height=height, 
                        bg=COLORS['bg_medium'], highlightthickness=0, **kwargs)
        
        self.command = command
        self.text = text
        self.bg_color = bg
        self.hover_bg = hover_bg
        self.text_color = text_color
        self.font = font
        self.is_hovered = False
        
        # Draw rounded rectangle
        self._draw_button()
        
        # Bind events
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
    def _draw_button(self):
        """Draw the rounded button."""
        self.delete("all")
        
        # Choose color based on hover state
        color = self.hover_bg if self.is_hovered else self.bg_color
        
        # Draw rounded rectangle
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        radius = 8
        
        self.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, fill=color, outline="")
        self.create_arc(w-radius*2, 0, w, radius*2, start=0, extent=90, fill=color, outline="")
        self.create_arc(0, h-radius*2, radius*2, h, start=180, extent=90, fill=color, outline="")
        self.create_arc(w-radius*2, h-radius*2, w, h, start=270, extent=90, fill=color, outline="")
        
        self.create_rectangle(radius, 0, w-radius, h, fill=color, outline="")
        self.create_rectangle(0, radius, w, h-radius, fill=color, outline="")
        
        # Draw text
        self.create_text(w/2, h/2, text=self.text, fill=self.text_color, font=self.font)
        
    def _on_click(self, event):
        """Handle button click."""
        if self.command:
            self.command()
            
    def _on_enter(self, event):
        """Handle mouse enter."""
        self.is_hovered = True
        self._draw_button()
        self.config(cursor="hand2")
        
    def _on_leave(self, event):
        """Handle mouse leave."""
        self.is_hovered = False
        self._draw_button()
        self.config(cursor="")


class SettingsForm(tk.Tk):
    """Main settings form for WoW Auto."""
    
    def __init__(self):
        """Initialize the settings form."""
        super().__init__()
        self.title("⚔️ WoW Auto - Settings")
        
        # Window styling - increased height to fit all content
        self.geometry("600x750")
        self.resizable(False, False)
        
        # Apply WoW theme colors
        self.configure(bg=COLORS['bg_dark'])
        
        # Custom title bar styling (Windows 10/11)
        try:
            # This makes the title bar dark on Windows 10/11
            import ctypes
            HWND = ctypes.windll.user32.GetParent(self.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_CAPTION_COLOR = 35
            
            # Set dark mode for title bar
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                HWND, 
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(1)), 
                ctypes.sizeof(ctypes.c_int)
            )
            
            # Set custom title bar color (brown)
            title_color = 0x00142f2b  # BGR format of #2b1f14
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                HWND,
                DWMWA_CAPTION_COLOR,
                ctypes.byref(ctypes.c_int(title_color)),
                ctypes.sizeof(ctypes.c_int)
            )
        except:
            # Fallback if ctypes doesn't work
            pass

        # Settings manager
        self.settings_mgr = SettingsManager()

        # UI state
        self.json_path_var = tk.StringVar()
        self.save_dir_var = tk.StringVar(value=str(self.settings_mgr.settings_dir))
        self.sequence_names: List[str] = []

        # Change default toggle key to something easier to detect
        self.toggle_key_var = tk.StringVar(value="f8")
        self.is_running = False
        self.run_status_var = tk.StringVar(value="Not running")

        # Background runner
        self._bg_runner: Optional[BackgroundRunner] = None
        
        # Global key listener (will be started after UI is built)
        self._key_listener: Optional[GlobalKeyListener] = None
        
        # Stop window (always-on-top red STOP button)
        self._stop_window: Optional[StopWindow] = None

        # Build UI
        self._build_ui()

        # Load existing settings if present
        self.load_existing_settings()

        # NOW start global listener after all UI vars are created
        self._start_global_listener()
        
        # Show the control panel (always visible) - increased delay for stability
        self.after(200, self._show_stop_window)

        # Poll thread state
        self.after(500, self._poll_status)
        
        # Handle window state changes to prevent control panel issues
        self.bind("<Unmap>", self._on_minimize)
        self.bind("<Map>", self._on_restore)

    def _build_ui(self):
        """Build the user interface."""
        # Title header with gradient-like effect
        header = tk.Frame(self, bg=COLORS['bg_medium'], height=60)
        header.grid(column=0, row=0, columnspan=3, sticky="ew", padx=0, pady=0)
        header.grid_propagate(False)
        
        title_label = tk.Label(
            header, 
            text="⚔️ World of Warcraft Automation ⚔️",
            font=("Segoe UI", 16, "bold"),
            fg=COLORS['gold'],
            bg=COLORS['bg_medium']
        )
        title_label.pack(expand=True)
        
        subtitle_label = tk.Label(
            header,
            text="Configure your automation sequences",
            font=("Segoe UI", 9),
            fg=COLORS['text_dim'],
            bg=COLORS['bg_medium']
        )
        subtitle_label.pack()
        
        row = 1
        
        # JSON file selection section
        section_frame = tk.Frame(self, bg=COLORS['bg_medium'], relief="flat", bd=0)
        section_frame.grid(column=0, row=row, columnspan=3, sticky="ew", padx=12, pady=(12, 6))
        
        tk.Label(
            section_frame, 
            text="📁 Sequence File:", 
            font=("Segoe UI", 10, "bold"),
            fg=COLORS['gold_light'],
            bg=COLORS['bg_medium']
        ).grid(column=0, row=0, sticky="w", padx=10, pady=8)
        
        entry_frame = tk.Frame(section_frame, bg=COLORS['bg_light'], relief="flat", bd=1)
        entry_frame.grid(column=0, row=1, columnspan=2, sticky="ew", padx=10, pady=(0, 8))
        
        path_entry = tk.Entry(
            entry_frame,
            textvariable=self.json_path_var,
            font=("Consolas", 9),
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            insertbackground=COLORS['gold'],
            relief="flat",
            bd=5
        )
        path_entry.pack(fill="both", expand=True, padx=2, pady=2)
        
        browse_btn = RoundedButton(section_frame, "Browse...", self.browse_json, width=100, height=30)
        browse_btn.grid(column=2, row=1, padx=(5, 10), pady=(0, 8))

        section_frame.grid_columnconfigure(0, weight=1)
        
        row += 1
        
        load_btn = RoundedButton(self, "📂 Load Sequences", self.load_sequences, width=150, height=32)
        load_btn.grid(column=0, row=row, padx=12, pady=6, sticky="w")
        
        row += 1
        
        # Sequences list section
        seq_frame = tk.Frame(self, bg=COLORS['bg_medium'], relief="flat", bd=0)
        seq_frame.grid(column=0, row=row, columnspan=3, sticky="ew", padx=12, pady=6)
        
        tk.Label(
            seq_frame,
            text="📋 Available Sequences (select one or more):",
            font=("Segoe UI", 10, "bold"),
            fg=COLORS['gold_light'],
            bg=COLORS['bg_medium']
        ).pack(anchor="w", padx=10, pady=(8, 4))
        
        # Create frame for listbox with scrollbar
        listbox_container = tk.Frame(seq_frame, bg=COLORS['bg_light'], relief="flat", bd=1)
        listbox_container.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        
        # Styled listbox
        self.listbox = tk.Listbox(
            listbox_container,
            selectmode=tk.MULTIPLE,
            font=("Consolas", 9),
            bg=COLORS['bg_light'],
            fg=COLORS['text'],
            selectbackground=COLORS['gold_dark'],
            selectforeground=COLORS['bg_dark'],
            relief="flat",
            bd=5,
            height=6,
            highlightthickness=0
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        
        # Bind selection change to update control panel
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._update_control_panel_sequences())
        
        # Scrollbar with custom styling
        scrollbar = tk.Scrollbar(listbox_container, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        row += 1
        
        # Settings section
        settings_frame = tk.Frame(self, bg=COLORS['bg_medium'], relief="flat", bd=0)
        settings_frame.grid(column=0, row=row, columnspan=3, sticky="ew", padx=12, pady=6)
        
        tk.Label(
            settings_frame,
            text="⚙️ Configuration:",
            font=("Segoe UI", 10, "bold"),
            fg=COLORS['gold_light'],
            bg=COLORS['bg_medium']
        ).grid(column=0, row=0, sticky="w", padx=10, pady=(8, 4))
        
        # Hotkey setting
        hotkey_frame = tk.Frame(settings_frame, bg=COLORS['bg_medium'])
        hotkey_frame.grid(column=0, row=1, columnspan=3, sticky="ew", padx=10, pady=4)
        
        tk.Label(
            hotkey_frame,
            text="🎯 Global Toggle Key:",
            font=("Segoe UI", 9),
            fg=COLORS['text'],
            bg=COLORS['bg_medium']
        ).pack(side="left", padx=(0, 10))
        
        key_entry_frame = tk.Frame(hotkey_frame, bg=COLORS['bg_light'], relief="flat", bd=1)
        key_entry_frame.pack(side="left", padx=(0, 10))
        
        key_entry = tk.Entry(
            key_entry_frame,
            textvariable=self.toggle_key_var,
            font=("Consolas", 10, "bold"),
            bg=COLORS['bg_light'],
            fg=COLORS['gold'],
            insertbackground=COLORS['gold'],
            relief="flat",
            bd=3,
            width=12,
            justify="center"
        )
        key_entry.pack(padx=2, pady=2)
        
        update_key_btn = RoundedButton(
            hotkey_frame, 
            "Update", 
            self._restart_global_listener, 
            width=80, 
            height=28,
            bg=COLORS['bg_light'],
            hover_bg=COLORS['gold_dark'],
            text_color=COLORS['text']
        )
        update_key_btn.pack(side="left")

        row += 1

        
        # Status section
        status_frame = tk.Frame(self, bg=COLORS['bg_medium'], relief="flat", bd=0)
        status_frame.grid(column=0, row=row, columnspan=3, sticky="ew", padx=12, pady=6)
        
        tk.Label(
            status_frame,
            text="📊 Status:",
            font=("Segoe UI", 10, "bold"),
            fg=COLORS['gold_light'],
            bg=COLORS['bg_medium']
        ).pack(anchor="w", padx=10, pady=(8, 4))
        
        # Status indicators
        status_inner = tk.Frame(status_frame, bg=COLORS['bg_medium'])
        status_inner.pack(fill="x", padx=10, pady=(0, 8))
        
        # Auto mode status
        auto_status_frame = tk.Frame(status_inner, bg=COLORS['bg_light'], relief="flat", bd=1)
        auto_status_frame.pack(fill="x", pady=2)
        
        tk.Label(
            auto_status_frame,
            text="🤖 Automation:",
            font=("Segoe UI", 9),
            fg=COLORS['text_dim'],
            bg=COLORS['bg_light']
        ).pack(side="left", padx=8, pady=6)
        
        self.run_status_label = tk.Label(
            auto_status_frame,
            textvariable=self.run_status_var,
            font=("Segoe UI", 10, "bold"),
            fg=COLORS['error'],
            bg=COLORS['bg_light']
        )
        self.run_status_label.pack(side="left", padx=8)
        
        # Thread status
        thread_status_frame = tk.Frame(status_inner, bg=COLORS['bg_light'], relief="flat", bd=1)
        thread_status_frame.pack(fill="x", pady=2)
        
        tk.Label(
            thread_status_frame,
            text="⚡ Runner:",
            font=("Segoe UI", 9),
            fg=COLORS['text_dim'],
            bg=COLORS['bg_light']
        ).pack(side="left", padx=8, pady=6)
        
        self.thread_status_var = tk.StringVar(value="stopped")
        self.thread_status_label = tk.Label(
            thread_status_frame,
            textvariable=self.thread_status_var,
            font=("Segoe UI", 9),
            fg=COLORS['text'],
            bg=COLORS['bg_light']
        )
        self.thread_status_label.pack(side="left", padx=8)
        
        # Listener status
        listener_status_frame = tk.Frame(status_inner, bg=COLORS['bg_light'], relief="flat", bd=1)
        listener_status_frame.pack(fill="x", pady=2)
        
        tk.Label(
            listener_status_frame,
            text="🎧 Listener:",
            font=("Segoe UI", 9),
            fg=COLORS['text_dim'],
            bg=COLORS['bg_light']
        ).pack(side="left", padx=8, pady=6)
        
        self.listener_status_var = tk.StringVar(value="starting...")
        tk.Label(
            listener_status_frame,
            textvariable=self.listener_status_var,
            font=("Segoe UI", 9),
            fg=COLORS['warning'],
            bg=COLORS['bg_light']
        ).pack(side="left", padx=8)

        row += 1

        
        # Action buttons
        btn_frame = tk.Frame(self, bg=COLORS['bg_dark'])
        btn_frame.grid(column=0, row=row, columnspan=3, sticky="ew", padx=12, pady=(12, 8))
        
        # Toggle run button (large and prominent)
        toggle_btn = RoundedButton(
            btn_frame,
            "▶️ START AUTOMATION",
            self.toggle_running,
            width=200,
            height=45,
            bg=COLORS['success'],
            hover_bg='#22c55e',
            text_color='#1e293b',
            font=("Segoe UI", 11, "bold")
        )
        toggle_btn.pack(side="top", pady=(0, 8))
        
        # Bottom buttons row
        bottom_btn_frame = tk.Frame(btn_frame, bg=COLORS['bg_dark'])
        bottom_btn_frame.pack(fill="x")
        
        save_btn = RoundedButton(
            bottom_btn_frame,
            "💾 Save",
            self.save_settings,
            width=130,
            height=35,
            bg=COLORS['bg_light'],
            hover_bg=COLORS['gold_dark'],
            text_color=COLORS['text']
        )
        save_btn.pack(side="left", padx=(0, 8))
        
        save_close_btn = RoundedButton(
            bottom_btn_frame,
            "💾 Save & Exit",
            self.save_and_close,
            width=130,
            height=35,
            bg=COLORS['bg_light'],
            hover_bg=COLORS['gold_dark'],
            text_color=COLORS['text']
        )
        save_close_btn.pack(side="left", padx=(0, 8))
        
        quit_btn = RoundedButton(
            bottom_btn_frame,
            "❌ Quit",
            self._on_close,
            width=100,
            height=35,
            bg=COLORS['error'],
            hover_bg='#dc2626',
            text_color='white'
        )
        quit_btn.pack(side="left")
        
        # Store toggle button reference for updating text
        self.toggle_btn_widget = toggle_btn

        row += 1
        
        # Status message bar
        status_bar = tk.Frame(self, bg=COLORS['bg_medium'], relief="flat", bd=0, height=40)
        status_bar.grid(column=0, row=row, columnspan=3, sticky="ew", padx=0, pady=0)
        status_bar.grid_propagate(False)
        
        self.status = tk.Label(
            status_bar,
            text="",
            font=("Segoe UI", 9),
            fg=COLORS['text_dim'],
            bg=COLORS['bg_medium'],
            anchor="w"
        )
        self.status.pack(fill="both", expand=True, padx=15, pady=8)

        # Configure column weights for resizing
        self.grid_columnconfigure(0, weight=1)

    def _start_global_listener(self):
        """Start global keyboard listener."""
        toggle_key = self.toggle_key_var.get().strip() or "f8"
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

    def _show_stop_window(self):
        """Show the always-on-top control panel window."""
        if not self._stop_window:
            self._stop_window = StopWindow(
                stop_callback=self.toggle_running,
                start_callback=self.toggle_running
            )
            # Update the control panel state based on current running status
            if hasattr(self._stop_window, 'is_running'):
                self._stop_window.is_running = self.is_running
                self._stop_window._update_buttons()
            # Update sequences display
            self._update_control_panel_sequences()

    def _hide_stop_window(self):
        """Hide the STOP window."""
        if self._stop_window:
            self._stop_window.destroy()
            self._stop_window = None
    
    def _update_control_panel_sequences(self):
        """Update the control panel with currently selected sequences."""
        if self._stop_window:
            selected = [self.sequence_names[i] for i in self.listbox.curselection()] if self.sequence_names else []
            self._stop_window.update_sequences(selected)
    
    def _on_minimize(self, event):
        """Handle main window minimize - keep control panel visible."""
        if self._stop_window and self._stop_window.window.winfo_exists():
            # Ensure control panel stays on top even when main window is minimized
            self._stop_window.window.lift()
            self._stop_window.window.attributes("-topmost", True)
    
    def _on_restore(self, event):
        """Handle main window restore - ensure control panel is still on top."""
        if self._stop_window and self._stop_window.window.winfo_exists():
            self._stop_window.window.lift()
            self._stop_window.window.attributes("-topmost", True)

    def browse_json(self):
        """Browse for JSON sequence file."""
        p = filedialog.askopenfilename(title="Select JSON file", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if p:
            self.json_path_var.set(p)
            self.load_sequences()

    def load_sequences(self):
        """Load sequences from the selected JSON file."""
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
        
        # Update control panel when sequences are loaded
        self._update_control_panel_sequences()

    def open_save_dir(self):
        """Open the settings save directory."""
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
        """Save current settings to file."""
        selected = [self.sequence_names[i] for i in self.listbox.curselection()] if self.sequence_names else []
        
        try:
            save_file = self.settings_mgr.save(
                json_path=self.json_path_var.get().strip(),
                selected_sequences=selected,
                toggle_key=self.toggle_key_var.get().strip() or "f8",
                is_running=self.is_running
            )
            self.status.config(text=f"Settings saved to: {save_file}")
            return save_file
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None

    def save_and_close(self):
        """Save settings and close the application."""
        saved = self.save_settings()
        if saved:
            self._on_close()

    def load_existing_settings(self):
        """Load existing settings from file."""
        data = self.settings_mgr.load()
        if data:
            json_path = data.get("json_path", "")
            sel = data.get("selected_sequences", [])
            toggle = data.get("toggle_key", "f8")
            
            if json_path:
                self.json_path_var.set(json_path)
                self.load_sequences()
                for i, name in enumerate(self.sequence_names):
                    if name in sel:
                        self.listbox.selection_set(i)
            self.toggle_key_var.set(str(toggle) if str(toggle) else "f8")
            
            # Always start in stopped state to avoid confusion
            self.is_running = False
            self._update_run_status()
            self.save_dir_var.set(str(self.settings_mgr.settings_dir))
            self.status.config(text=f"Loaded settings from {self.settings_mgr.settings_file}")

    def _on_close(self):
        """Handle window close event."""
        self.save_settings()  # Save settings on close
        if self._key_listener:
            self._key_listener.stop()
        if self._stop_window:
            self._stop_window.destroy()
        self.destroy()

    def toggle_running(self):
        """Toggle the automation running state."""
        if not self.is_running:
            # Starting - validate first
            json_path = self.json_path_var.get().strip()
            if not json_path:
                self.status.config(text="Error: Please select a JSON file first.")
                return
            selected = [self.sequence_names[i] for i in self.listbox.curselection()] if self.sequence_names else []
            if not selected:
                self.status.config(text="Error: Please select at least one sequence to run.")
                return
            
            # Save settings before starting
            self.save_settings()
            
            try:
                self._bg_runner = BackgroundRunner(json_path=json_path, selected_sequences=selected, dry_run=False)
                self._bg_runner.start()
                self.is_running = True
                self._update_run_status()
                self.thread_status_var.set("running")
                
                # Update control panel state to show STOP is active
                if self._stop_window:
                    self._stop_window.is_running = True
                    self._stop_window._update_buttons()
                    # Update sequences display with what's running
                    self._stop_window.update_sequences(selected)
                
                # Minimize main window when automation starts
                self.iconify()
                
                self.status.config(text="Auto mode started! Press toggle key to stop.")
            except Exception as e:
                self.status.config(text=f"Failed to start runner: {e}")
        else:
            # Stopping
            try:
                exc = None
                if self._bg_runner:
                    exc = self._bg_runner.stop()
                    self._bg_runner = None
                self.is_running = False
                self._update_run_status()
                self.thread_status_var.set("stopped")
                
                # Update control panel state to show START is active
                if self._stop_window:
                    self._stop_window.is_running = False
                    self._stop_window._update_buttons()
                
                # Don't restore main window - keep it minimized
                # User can manually restore if needed
                
                if exc:
                    self.status.config(text=f"Runner stopped with error: {exc}")
                else:
                    self.status.config(text="Auto mode stopped.")
            except Exception as e:
                self.status.config(text=f"Failed to stop runner: {e}")

    def _update_run_status(self):
        """Update the run status label and background runner state."""
        if self.is_running:
            self.run_status_var.set("✅ Running")
            self.run_status_label.config(fg=COLORS['success'])
            # Update button
            self.toggle_btn_widget.text = "⏸️ STOP AUTOMATION"
            self.toggle_btn_widget.bg_color = COLORS['error']
            self.toggle_btn_widget.hover_bg = '#dc2626'
            self.toggle_btn_widget._draw_button()
        else:
            self.run_status_var.set("⏹️ Not Running")
            self.run_status_label.config(fg=COLORS['error'])
            # Update button
            self.toggle_btn_widget.text = "▶️ START AUTOMATION"
            self.toggle_btn_widget.bg_color = COLORS['success']
            self.toggle_btn_widget.hover_bg = '#22c55e'
            self.toggle_btn_widget._draw_button()

    def _poll_status(self):
        """Poll the background runner status periodically."""
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
                    # Update control panel to show START button if runner crashed
                    if self._stop_window:
                        self._stop_window.is_running = False
                        self._stop_window._update_buttons()
        else:
            self.thread_status_var.set("stopped")
        self.after(500, self._poll_status)
