"""Stop window widget - always-on-top overlay STOP button."""
import tkinter as tk


# WoW-inspired colors
COLORS = {
    'error': '#ef4444',
    'error_hover': '#dc2626',
    'bg_dark': '#2b1f14',
}


class StopWindow:
    """Transparent overlay with a STOP button in the top-right corner."""
    
    def __init__(self, stop_callback):
        """
        Initialize stop window as transparent overlay.
        
        Args:
            stop_callback: Function to call when STOP button is clicked
        """
        self.stop_callback = stop_callback
        self.window = tk.Toplevel()
        self.window.title("")  # No title
        self.window.geometry("140x60")
        self.window.resizable(False, False)
        
        # Make it always on top
        self.window.attributes("-topmost", True)
        
        # Remove window decorations (no border, title bar)
        self.window.overrideredirect(True)
        
        # Make background transparent/see-through
        self.window.attributes("-transparentcolor", COLORS['bg_dark'])
        
        # Set window transparency (0.0 = fully transparent, 1.0 = opaque)
        self.window.attributes("-alpha", 0.95)
        
        # Position in top-right corner
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        x = screen_width - 160  # 140 width + 20 margin
        y = 20  # 20 pixels from top
        self.window.geometry(f"140x60+{x}+{y}")
        
        # Dark background (will be transparent)
        self.window.configure(bg=COLORS['bg_dark'])
        
        # Create rounded button effect with canvas
        canvas = tk.Canvas(
            self.window,
            width=130,
            height=50,
            bg=COLORS['bg_dark'],
            highlightthickness=0
        )
        canvas.pack(expand=True, padx=5, pady=5)
        
        # Draw rounded rectangle button
        self._draw_rounded_rect(canvas, 0, 0, 130, 50, 10, COLORS['error'])
        
        # Add text
        canvas.create_text(
            65, 25,
            text="⏹️ STOP",
            fill="white",
            font=("Segoe UI", 14, "bold")
        )
        
        # Store canvas for hover effects
        self.canvas = canvas
        self.is_hovered = False
        
        # Bind events
        canvas.bind("<Button-1>", lambda e: self.stop_callback())
        canvas.bind("<Enter>", self._on_enter)
        canvas.bind("<Leave>", self._on_leave)
        
        # Make window draggable (optional - allows repositioning)
        canvas.bind("<ButtonPress-1>", self._start_drag)
        canvas.bind("<B1-Motion>", self._on_drag)
        
        self.drag_start_x = 0
        self.drag_start_y = 0
        
    def _start_drag(self, event):
        """Start dragging the window."""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
    def _on_drag(self, event):
        """Handle window dragging."""
        x = self.window.winfo_x() + event.x - self.drag_start_x
        y = self.window.winfo_y() + event.y - self.drag_start_y
        self.window.geometry(f"+{x}+{y}")
    
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
    
    def _on_enter(self, event):
        """Handle mouse enter for hover effect."""
        self.is_hovered = True
        self.canvas.delete("all")
        self._draw_rounded_rect(self.canvas, 0, 0, 130, 50, 10, COLORS['error_hover'])
        self.canvas.create_text(
            65, 25,
            text="⏹️ STOP",
            fill="white",
            font=("Segoe UI", 14, "bold")
        )
        self.canvas.config(cursor="hand2")
    
    def _on_leave(self, event):
        """Handle mouse leave to remove hover effect."""
        self.is_hovered = False
        self.canvas.delete("all")
        self._draw_rounded_rect(self.canvas, 0, 0, 130, 50, 10, COLORS['error'])
        self.canvas.create_text(
            65, 25,
            text="⏹️ STOP",
            fill="white",
            font=("Segoe UI", 14, "bold")
        )
        self.canvas.config(cursor="")
    
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
    
    def _on_enter(self, event):
        """Handle mouse enter for hover effect."""
        self.is_hovered = True
        self.canvas.delete("all")
        self._draw_rounded_rect(self.canvas, 0, 0, 130, 50, 10, COLORS['error_hover'])
        self.canvas.create_text(
            65, 25,
            text="⏹️ STOP",
            fill="white",
            font=("Segoe UI", 14, "bold")
        )
        self.canvas.config(cursor="hand2")
    
    def _on_leave(self, event):
        """Handle mouse leave to remove hover effect."""
        self.is_hovered = False
        self.canvas.delete("all")
        self._draw_rounded_rect(self.canvas, 0, 0, 130, 50, 10, COLORS['error'])
        self.canvas.create_text(
            65, 25,
            text="⏹️ STOP",
            fill="white",
            font=("Segoe UI", 14, "bold")
        )
        self.canvas.config(cursor="")
        
    def destroy(self):
        """Close the stop window."""
        try:
            self.window.destroy()
        except Exception:
            pass
