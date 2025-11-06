"""Control panel widget - always-on-top overlay with START/STOP buttons."""
import tkinter as tk


# WoW-inspired colors
COLORS = {
    'success': '#22c55e',
    'success_hover': '#16a34a',
    'error': '#ef4444',
    'error_hover': '#dc2626',
    'bg_dark': '#2b1f14',
    'bg_panel': '#3d2a1f',
}


class StopWindow:
    """Transparent overlay control panel with START and STOP buttons."""
    
    def __init__(self, stop_callback, start_callback=None):
        """
        Initialize control panel as transparent overlay.
        
        Args:
            stop_callback: Function to call when STOP button is clicked
            start_callback: Function to call when START button is clicked
        """
        self.stop_callback = stop_callback
        self.start_callback = start_callback
        self.is_running = False
        self.selected_sequences = []  # Store selected sequences
        
        try:
            self.window = tk.Toplevel()
            self.window.title("")  # No title
            self.window.geometry("280x120")  # Increased height for sequences
            self.window.resizable(False, False)
            
            # Make it always on top of ALL windows
            self.window.attributes("-topmost", True)
            
            # Remove window decorations (no border, title bar)
            self.window.overrideredirect(True)
            
            # Make background transparent/see-through
            self.window.attributes("-transparentcolor", COLORS['bg_dark'])
            
            # Set window transparency (0.0 = fully transparent, 1.0 = opaque)
            self.window.attributes("-alpha", 0.95)
            
            # Force window to appear
            self.window.update_idletasks()
            self.window.update()
            
            # Position in top-right corner with safe bounds
            try:
                screen_width = self.window.winfo_screenwidth()
                screen_height = self.window.winfo_screenheight()
            except:
                # Fallback if screen info not available
                screen_width = 1920
                screen_height = 1080
            
            x = max(0, screen_width - 300)  # 280 width + 20 margin
            y = 20  # 20 pixels from top
            self.window.geometry(f"280x120+{x}+{y}")
            
            # Dark background (will be transparent)
            self.window.configure(bg=COLORS['bg_dark'])
        
            # Create main panel with rounded background
            self.main_canvas = tk.Canvas(
                self.window,
                width=270,
                height=110,
                bg=COLORS['bg_dark'],
                highlightthickness=0
            )
            self.main_canvas.pack(expand=True, padx=5, pady=5)
        
            # Draw panel background (rounded rectangle)
            self._draw_rounded_rect(self.main_canvas, 0, 0, 270, 110, 15, COLORS['bg_panel'])
        
            # Add title text
            self.main_canvas.create_text(
                135, 15,
                text="⚔️ WoW Auto Control",
                fill="#f0d98c",
                font=("Segoe UI", 11, "bold")
            )
            
            # Add sequences display area
            self.sequences_text = self.main_canvas.create_text(
                135, 35,
                text="No sequences selected",
                fill="#c0b49e",
                font=("Segoe UI", 8),
                width=250
            )
        
            # Create START button canvas
            self.start_canvas = tk.Canvas(
                self.main_canvas,
                width=120,
                height=35,
                bg=COLORS['bg_panel'],
                highlightthickness=0
            )
            self.main_canvas.create_window(60, 75, window=self.start_canvas)
        
            # Draw START button
            self._draw_rounded_rect(self.start_canvas, 0, 0, 120, 35, 8, COLORS['success'])
            self.start_canvas.create_text(
                60, 17,
                text="▶️ START",
                fill="white",
                font=("Segoe UI", 11, "bold")
            )
        
            # Create STOP button canvas
            self.stop_canvas = tk.Canvas(
                self.main_canvas,
                width=120,
                height=35,
                bg=COLORS['bg_panel'],
                highlightthickness=0
            )
            self.main_canvas.create_window(210, 75, window=self.stop_canvas)
        
            # Draw STOP button (initially disabled appearance)
            self._draw_rounded_rect(self.stop_canvas, 0, 0, 120, 35, 8, "#666666")
            self.stop_canvas.create_text(
                60, 17,
                text="⏹️ STOP",
                fill="#999999",
                font=("Segoe UI", 11, "bold")
            )
        
            # Bind START button events
            self.start_canvas.bind("<Button-1>", self._on_start_click)
            self.start_canvas.bind("<Enter>", lambda e: self._on_button_hover(self.start_canvas, True, "start"))
            self.start_canvas.bind("<Leave>", lambda e: self._on_button_hover(self.start_canvas, False, "start"))
        
            # Bind STOP button events (initially disabled)
            self.stop_canvas.bind("<Button-1>", self._on_stop_click)
        
            # Make window draggable - bind to window itself to prevent losing drag
            self.window.bind("<Button-1>", self._start_drag)
            self.window.bind("<B1-Motion>", self._do_drag)
            self.window.bind("<ButtonRelease-1>", self._stop_drag)
            
            # Also bind to canvas for title area
            self.main_canvas.bind("<Button-1>", self._start_drag)
            self.main_canvas.bind("<B1-Motion>", self._do_drag)
            self.main_canvas.bind("<ButtonRelease-1>", self._stop_drag)
        
            self.drag_start_x = 0
            self.drag_start_y = 0
            self.is_dragging = False
        
            # Handle resolution changes gracefully
            self.window.bind("<Configure>", self._on_configure)
        
            # Store original position
            self.saved_x = x
            self.saved_y = y
        
        except Exception as e:
            # If control panel creation fails, log but don't crash
            print(f"Warning: Control panel creation failed: {e}")
            # Create a minimal fallback window
            self.window = tk.Toplevel()
            self.window.withdraw()  # Hide if creation fails
    
    def _on_start_click(self, event):
        """Handle START button click."""
        if not self.is_running and self.start_callback:
            self.is_running = True
            self._update_buttons()
            self.start_callback()
    
    def _on_stop_click(self, event):
        """Handle STOP button click."""
        if self.is_running:
            self.is_running = False
            self._update_buttons()
            self.stop_callback()
    
    def _update_buttons(self):
        """Update button states based on running status."""
        # Clear and redraw START button
        self.start_canvas.delete("all")
        if self.is_running:
            # Disabled state
            self._draw_rounded_rect(self.start_canvas, 0, 0, 120, 35, 8, "#666666")
            self.start_canvas.create_text(
                60, 17,
                text="▶️ START",
                fill="#999999",
                font=("Segoe UI", 11, "bold")
            )
            self.start_canvas.config(cursor="")
        else:
            # Enabled state
            self._draw_rounded_rect(self.start_canvas, 0, 0, 120, 35, 8, COLORS['success'])
            self.start_canvas.create_text(
                60, 17,
                text="▶️ START",
                fill="white",
                font=("Segoe UI", 11, "bold")
            )
            self.start_canvas.config(cursor="hand2")
        
        # Clear and redraw STOP button
        self.stop_canvas.delete("all")
        if self.is_running:
            # Enabled state
            self._draw_rounded_rect(self.stop_canvas, 0, 0, 120, 35, 8, COLORS['error'])
            self.stop_canvas.create_text(
                60, 17,
                text="⏹️ STOP",
                fill="white",
                font=("Segoe UI", 11, "bold")
            )
            self.stop_canvas.config(cursor="hand2")
            # Bind hover events for STOP when enabled
            self.stop_canvas.bind("<Enter>", lambda e: self._on_button_hover(self.stop_canvas, True, "stop"))
            self.stop_canvas.bind("<Leave>", lambda e: self._on_button_hover(self.stop_canvas, False, "stop"))
        else:
            # Disabled state
            self._draw_rounded_rect(self.stop_canvas, 0, 0, 120, 35, 8, "#666666")
            self.stop_canvas.create_text(
                60, 17,
                text="⏹️ STOP",
                fill="#999999",
                font=("Segoe UI", 11, "bold")
            )
            self.stop_canvas.config(cursor="")
            # Unbind hover events when disabled
            self.stop_canvas.unbind("<Enter>")
            self.stop_canvas.unbind("<Leave>")
    
    def _on_button_hover(self, canvas, entering, button_type):
        """Handle button hover effects."""
        if button_type == "start" and not self.is_running:
            canvas.delete("all")
            color = COLORS['success_hover'] if entering else COLORS['success']
            self._draw_rounded_rect(canvas, 0, 0, 120, 35, 8, color)
            canvas.create_text(
                60, 17,
                text="▶️ START",
                fill="white",
                font=("Segoe UI", 11, "bold")
            )
            canvas.config(cursor="hand2" if entering else "")
        elif button_type == "stop" and self.is_running:
            canvas.delete("all")
            color = COLORS['error_hover'] if entering else COLORS['error']
            self._draw_rounded_rect(canvas, 0, 0, 120, 35, 8, color)
            canvas.create_text(
                60, 17,
                text="⏹️ STOP",
                fill="white",
                font=("Segoe UI", 11, "bold")
            )
            canvas.config(cursor="hand2" if entering else "")
        
    def _start_drag(self, event):
        """Start dragging the window."""
        # Check if click is on a button canvas - don't drag if so
        if event.widget in (self.start_canvas, self.stop_canvas):
            return
            
        # Only allow drag from title/sequence area (top 60 pixels)
        if hasattr(event, 'y') and event.y < 60:
            self.is_dragging = True
            self.drag_start_x = event.x_root - self.window.winfo_x()
            self.drag_start_y = event.y_root - self.window.winfo_y()
            self.main_canvas.config(cursor="fleur")
            # Prevent event propagation
            return "break"
    
    def _do_drag(self, event):
        """Handle window dragging - smoother version with global tracking."""
        if self.is_dragging:
            try:
                x = event.x_root - self.drag_start_x
                y = event.y_root - self.drag_start_y
                
                # Keep window on screen bounds
                screen_width = self.window.winfo_screenwidth()
                screen_height = self.window.winfo_screenheight()
                
                # Constrain to screen
                x = max(0, min(x, screen_width - 280))
                y = max(0, min(y, screen_height - 120))
                
                self.window.geometry(f"+{x}+{y}")
                self.saved_x = x
                self.saved_y = y
                # Prevent event propagation
                return "break"
            except Exception:
                pass
    
    def _stop_drag(self, event):
        """Stop dragging the window."""
        if self.is_dragging:
            self.is_dragging = False
            self.main_canvas.config(cursor="")
            return "break"
    
    def _on_configure(self, event):
        """Handle resolution changes - reposition if off screen."""
        try:
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            current_x = self.window.winfo_x()
            current_y = self.window.winfo_y()
            
            # If window is off screen, reposition to top-right
            if current_x + 280 > screen_width or current_y + 120 > screen_height or current_x < 0 or current_y < 0:
                new_x = screen_width - 300
                new_y = 20
                self.window.geometry(f"+{new_x}+{new_y}")
                self.saved_x = new_x
                self.saved_y = new_y
        except Exception:
            pass
    
    def update_sequences(self, sequences):
        """Update the displayed sequences."""
        self.selected_sequences = sequences
        if not sequences:
            text = "No sequences selected"
        elif len(sequences) == 1:
            text = f"📋 {sequences[0]}"
        elif len(sequences) <= 3:
            text = "📋 " + ", ".join(sequences)
        else:
            text = f"📋 {len(sequences)} sequences"
        
        try:
            self.main_canvas.itemconfig(self.sequences_text, text=text)
        except Exception:
            pass
    
    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius, fill):
        """Draw a rounded rectangle on canvas."""
        points = [
            x1+radius, y1,
            x1+radius, y1,
            x2-radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1+radius,
            x1, y1
        ]
        return canvas.create_polygon(points, fill=fill, outline="", smooth=True)
        
    def destroy(self):
        """Close the control panel window."""
        try:
            self.window.destroy()
        except Exception:
            pass
