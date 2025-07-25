"""
UI Components Module
Contains reusable UI components and widgets
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Callable, Optional, Dict, Any, List
import threading
from datetime import datetime
from PIL import Image, ImageTk
import io


class ModernButton(tk.Button):
    """Modern styled button with hover effects"""
    
    def __init__(self, parent, text="", command=None, style="primary", **kwargs):
        self.style = style
        self.default_bg = kwargs.get('bg', '#0078d4' if style == 'primary' else '#f0f0f0')
        self.hover_bg = self._get_hover_color(self.default_bg)
        
        super().__init__(parent, text=text, command=command, 
                        relief=tk.FLAT, bd=0, cursor='hand2', **kwargs)
        
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
    
    def _get_hover_color(self, color):
        """Generate hover color"""
        if color == '#0078d4':  # Primary blue
            return '#106ebe'
        elif color == '#f0f0f0':  # Light gray
            return '#e0e0e0'
        return color
    
    def on_enter(self, event):
        """Handle mouse enter"""
        self.configure(bg=self.hover_bg)
    
    def on_leave(self, event):
        """Handle mouse leave"""
        self.configure(bg=self.default_bg)


class StatusBar(tk.Frame):
    """Status bar with multiple sections"""
    
    def __init__(self, parent):
        super().__init__(parent, relief=tk.SUNKEN, bd=1)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        self.model_var = tk.StringVar()
        self.mode_var = tk.StringVar()
        
        # Left section - main status
        self.status_label = tk.Label(self, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Right section - model and mode info
        self.model_label = tk.Label(self, textvariable=self.model_var, anchor=tk.E)
        self.model_label.pack(side=tk.RIGHT, padx=5)
        
        self.mode_label = tk.Label(self, textvariable=self.mode_var, anchor=tk.E)
        self.mode_label.pack(side=tk.RIGHT, padx=5)
    
    def set_status(self, text: str):
        """Set main status text"""
        self.status_var.set(text)
    
    def set_model(self, model: str):
        """Set current model"""
        self.model_var.set(f"Model: {model}")
    
    def set_mode(self, mode: str):
        """Set current mode"""
        self.mode_var.set(f"Mode: {mode}")


class ProgressDialog:
    """Progress dialog for long-running operations"""
    
    def __init__(self, parent, title="Processing", message="Please wait..."):
        self.parent = parent
        self.cancelled = False
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"400x150+{x}+{y}")
        
        # Message
        self.message_var = tk.StringVar(value=message)
        tk.Label(self.dialog, textvariable=self.message_var, 
                wraplength=350).pack(pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate')
        self.progress.pack(pady=10, padx=20, fill=tk.X)
        self.progress.start()
        
        # Cancel button
        tk.Button(self.dialog, text="Cancel", 
                 command=self.cancel).pack(pady=10)
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def update_message(self, message: str):
        """Update progress message"""
        self.message_var.set(message)
        self.dialog.update()
    
    def cancel(self):
        """Cancel operation"""
        self.cancelled = True
        self.close()
    
    def close(self):
        """Close dialog"""
        self.progress.stop()
        self.dialog.destroy()
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled"""
        return self.cancelled


class ChatBubble(tk.Frame):
    """Chat bubble widget for displaying messages"""
    
    def __init__(self, parent, message: str, is_user: bool = False, timestamp: str = None):
        super().__init__(parent)
        
        self.is_user = is_user
        self.message = message
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")
        
        # Configure colors based on sender
        if is_user:
            self.bg_color = "#0078d4"
            self.fg_color = "white"
            self.anchor = tk.E
        else:
            self.bg_color = "#f0f0f0"
            self.fg_color = "black"
            self.anchor = tk.W
        
        self.create_widgets()

    def create_widgets(self):
        """Create chat bubble widgets"""
        # Bubble frame
        bubble_frame = tk.Frame(self, bg=self.bg_color, relief=tk.RAISED, bd=1)
        bubble_frame.pack(anchor=self.anchor, padx=10, pady=5, fill=tk.X if not self.is_user else tk.NONE)

        # Message text
        message_label = tk.Label(bubble_frame, text=self.message,
                                 bg=self.bg_color, fg=self.fg_color,
                                 wraplength=400, justify=tk.LEFT,
                                 padx=10, pady=8, font=('Inter', 11))
        message_label.pack(anchor=self.anchor)

        # Timestamp
        time_label = tk.Label(bubble_frame, text=self.timestamp,
                              bg=self.bg_color, fg=self.fg_color,
                              font=('Inter', 8), padx=10, pady=2)
        time_label.pack(anchor=tk.SE)


class ImageViewer(tk.Toplevel):
    """Image viewer window"""
    
    def __init__(self, parent, image: Image.Image, title="Image Viewer"):
        super().__init__(parent)
        
        self.title(title)
        self.image = image
        self.zoom_factor = 1.0
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculate initial size (80% of screen, max image size)
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)
        
        img_width, img_height = image.size
        if img_width > max_width or img_height > max_height:
            ratio = min(max_width / img_width, max_height / img_height)
            self.zoom_factor = ratio
        
        self.setup_ui()
        self.update_image()
        
        # Center window
        self.update_idletasks()
        x = (screen_width // 2) - (self.winfo_width() // 2)
        y = (screen_height // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup image viewer UI"""
        # Toolbar
        toolbar = tk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(toolbar, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Reset", command=self.reset_zoom).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Save", command=self.save_image).pack(side=tk.LEFT, padx=2)
        
        # Image canvas with scrollbars
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg='white')
        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind mouse events for panning
        self.canvas.bind("<Button-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan_image)
        self.canvas.bind("<MouseWheel>", self.mouse_zoom)
    
    def update_image(self):
        """Update displayed image"""
        # Calculate new size
        orig_width, orig_height = self.image.size
        new_width = int(orig_width * self.zoom_factor)
        new_height = int(orig_height * self.zoom_factor)
        
        # Resize image
        resized_image = self.image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(resized_image)
        
        # Update canvas
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def zoom_in(self):
        """Zoom in"""
        self.zoom_factor *= 1.2
        self.update_image()
    
    def zoom_out(self):
        """Zoom out"""
        self.zoom_factor /= 1.2
        self.update_image()
    
    def reset_zoom(self):
        """Reset zoom to fit"""
        self.zoom_factor = 1.0
        self.update_image()
    
    def mouse_zoom(self, event):
        """Handle mouse wheel zoom"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def start_pan(self, event):
        """Start panning"""
        self.canvas.scan_mark(event.x, event.y)
    
    def pan_image(self, event):
        """Pan image"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    
    def save_image(self):
        """Save image to file"""
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.image.save(file_path)
                messagebox.showinfo("Saved", f"Image saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {e}")


class AudioPlayer(tk.Frame):
    """Audio player widget"""
    
    def __init__(self, parent, file_manager):
        super().__init__(parent)
        
        self.file_manager = file_manager
        self.current_file = None
        self.is_playing = False
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create audio player widgets"""
        # Control buttons
        controls = tk.Frame(self)
        controls.pack(fill=tk.X, padx=5, pady=5)
        
        self.play_button = tk.Button(controls, text="▶", width=3, 
                                   command=self.toggle_play)
        self.play_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = tk.Button(controls, text="⏹", width=3, 
                                   command=self.stop)
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # File info
        self.info_var = tk.StringVar()
        self.info_label = tk.Label(controls, textvariable=self.info_var, 
                                  anchor=tk.W)
        self.info_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
    
    def load_audio(self, file_path: str):
        """Load audio file"""
        self.current_file = file_path
        filename = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
        self.info_var.set(f"Loaded: {filename}")
        self.is_playing = False
        self.play_button.configure(text="▶")
    
    def toggle_play(self):
        """Toggle play/pause"""
        if not self.current_file:
            return
        
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def play(self):
        """Play audio"""
        if self.current_file:
            self.file_manager.play_audio(self.current_file, self.on_playback_finished)
            self.is_playing = True
            self.play_button.configure(text="⏸")
            self.info_var.set("Playing...")
    
    def pause(self):
        """Pause audio"""
        self.file_manager.stop_audio()
        self.is_playing = False
        self.play_button.configure(text="▶")
        self.info_var.set("Paused")
    
    def stop(self):
        """Stop audio"""
        self.file_manager.stop_audio()
        self.is_playing = False
        self.play_button.configure(text="▶")
        if self.current_file:
            filename = self.current_file.split('/')[-1] if '/' in self.current_file else self.current_file.split('\\')[-1]
            self.info_var.set(f"Loaded: {filename}")
    
    def on_playback_finished(self, error):
        """Called when playback finishes"""
        self.is_playing = False
        self.play_button.configure(text="▶")
        if error:
            self.info_var.set(f"Error: {error}")
        else:
            self.info_var.set("Finished")


class ResponseDisplay(scrolledtext.ScrolledText):
    """Enhanced text display for AI responses"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.configure(state=tk.DISABLED, wrap=tk.WORD, font=('JetBrains Mono', 10))

        # Configure text tags for styling
        self.tag_configure("user", foreground="#0078d4", font=("Inter", 11, "bold"))
        self.tag_configure("assistant", foreground="#000000", font=("Inter", 11))
        self.tag_configure("timestamp", foreground="#666666", font=("SF Pro Display", 9))
        self.tag_configure("error", foreground="#ff0000", font=("Inter", 11))
        self.tag_configure("system", foreground="#008000", font=("Inter", 11, "italic"))

        # Context menu
        self.context_menu = tk.Menu(self, tearoff=0, font=('Segoe UI', 9))
        self.context_menu.add_command(label="Copy", command=self.copy_selection)
        self.context_menu.add_command(label="Select All", command=self.select_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Clear", command=self.clear_all)
        self.context_menu.add_command(label="Save", command=self.save_content)

        self.bind("<Button-3>", self.show_context_menu)

    def update_theme_colors(self, colors):
        """Update colors for theme changes"""
        self.configure(bg=colors['text_bg'], fg=colors['text_fg'])

        # Update tag colors for dark theme
        if colors.get('bg') == '#2b2b2b':  # Dark theme
            self.tag_configure("user", foreground="#4da6ff", font=("Inter", 11, "normal"))
            self.tag_configure("assistant", foreground="#ffffff", font=("Inter", 11, "normal"))
            self.tag_configure("timestamp", foreground="#999999", font=("SF Pro Display", 9))
            self.tag_configure("error", foreground="#ff6b6b", font=("Inter", 11, "normal"))
            self.tag_configure("system", foreground="#66bb6a", font=("Inter", 11, "italic"))
        else:  # Light theme
            self.tag_configure("user", foreground="#0078d4", font=("Inter", 11, "bold"))
            self.tag_configure("assistant", foreground="#000000", font=("Inter", 11))
            self.tag_configure("timestamp", foreground="#666666", font=("SF Pro Display", 9))
            self.tag_configure("error", foreground="#ff0000", font=("Inter", 11))
            self.tag_configure("system", foreground="#008000", font=("Inter", 11, "italic"))
    
    def add_message(self, message: str, sender: str = "assistant", timestamp: str = None):
        """Add a message to the display"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.configure(state=tk.NORMAL)
        
        # Add timestamp
        self.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Add sender and message
        if sender == "user":
            self.insert(tk.END, "You: ", "user")
        elif sender == "assistant":
            self.insert(tk.END, "Assistant: ", "assistant")
        elif sender == "system":
            self.insert(tk.END, "System: ", "system")
        elif sender == "error":
            self.insert(tk.END, "Error: ", "error")
        
        self.insert(tk.END, f"{message}\n\n", sender)
        
        # Scroll to bottom
        self.see(tk.END)
        self.configure(state=tk.DISABLED)
    
    def clear_all(self):
        """Clear all content"""
        self.configure(state=tk.NORMAL)
        self.delete(1.0, tk.END)
        self.configure(state=tk.DISABLED)
    
    def copy_selection(self):
        """Copy selected text"""
        try:
            selected_text = self.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(selected_text)
        except tk.TclError:
            pass  # No selection
    
    def select_all(self):
        """Select all text"""
        self.tag_add(tk.SEL, "1.0", tk.END)
        self.mark_set(tk.INSERT, "1.0")
        self.see(tk.INSERT)
    
    def save_content(self):
        """Save content to file"""
        from tkinter import filedialog
        content = self.get(1.0, tk.END)
        if content.strip():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    messagebox.showinfo("Saved", f"Content saved to {file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save: {e}")
    
    def show_context_menu(self, event):
        """Show context menu"""
        self.context_menu.post(event.x_root, event.y_root)


class LoadingSpinner:
    """Loading spinner widget"""

    def __init__(self, parent, size=20, dark_theme=False):
        self.parent = parent
        self.size = size
        self.is_spinning = False
        self.angle = 0
        self.dark_theme = dark_theme

        # Get parent background color safely
        try:
            parent_bg = parent.cget('bg')
        except tk.TclError:
            # If parent doesn't have bg attribute (like ttk widgets), use default
            parent_bg = '#2b2b2b' if dark_theme else '#f0f0f0'

        self.canvas = tk.Canvas(parent, width=size, height=size,
                                highlightthickness=0, bg=parent_bg)

    def set_theme(self, dark_theme):
        """Update theme"""
        self.dark_theme = dark_theme

    def start(self):
        """Start spinning"""
        self.is_spinning = True
        self.spin()

    def stop(self):
        """Stop spinning"""
        self.is_spinning = False
        self.canvas.delete("all")

    def spin(self):
        """Animate spinner"""
        if not self.is_spinning:
            return

        self.canvas.delete("all")

        # Draw spinning circle
        center = self.size // 2
        radius = center - 2

        # Draw segments with varying opacity
        import math
        for i in range(8):
            start_angle = (self.angle + i * 45) % 360
            opacity = 1.0 - (i * 0.12)

            # Use appropriate colors for theme
            if self.dark_theme:
                color = f"#{int(opacity * 255):02x}{int(opacity * 255):02x}{int(opacity * 255):02x}"
            else:
                gray_value = int(opacity * 100)
                color = f"#{gray_value:02x}{gray_value:02x}{gray_value:02x}"

            x1 = center + radius * 0.6 * math.cos(math.radians(start_angle))
            y1 = center + radius * 0.6 * math.sin(math.radians(start_angle))
            x2 = center + radius * math.cos(math.radians(start_angle))
            y2 = center + radius * math.sin(math.radians(start_angle))

            self.canvas.create_line(x1, y1, x2, y2, width=2, fill=color, capstyle=tk.ROUND)

        self.angle = (self.angle + 45) % 360
        self.parent.after(100, self.spin)

    def pack(self, **kwargs):
        """Pack the spinner"""
        self.canvas.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the spinner"""
        self.canvas.grid(**kwargs)

    def pack_forget(self):
        """Hide the spinner"""
        self.canvas.pack_forget()