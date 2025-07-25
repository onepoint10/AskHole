"""
Main Application Module
Contains the main application window and orchestrates all components
"""

import tkinter as tk
import logging
from tkinter import ttk, messagebox
import threading
import uuid
from datetime import datetime
from typing import Optional, List

from gemini_client import GeminiClient, GeminiClientAsync
from config_manager import ConfigManager, SettingsDialog
from file_manager import FileManager, FileListWidget
from ui_components import (
    ModernButton, StatusBar, ProgressDialog, ImageViewer, 
    AudioPlayer, ResponseDisplay, LoadingSpinner
)


class MainApplication:
    """Main application class"""
    
    def __init__(self):
        """Initialize the main application"""
        # Initialize managers
        self.config_manager = ConfigManager()
        self.file_manager = FileManager(self.config_manager)
        
        # Initialize Gemini client (will be set up after API key validation)
        self.gemini_client = None
        self.gemini_async = None
        
        # Current session
        self.current_session_id = str(uuid.uuid4())
        
        # Create main window
        try:
            import tkinterdnd2 as tkdnd
            self.root = tkdnd.Tk()
        except ImportError:
            self.root = tk.Tk()

        self.root.title("Gemini Desktop Client")
        self.root.iconbitmap("icon.ico")
        self.root.geometry(self.config_manager.get("window_geometry", "1920x1080"))
        
        # Apply theme
        self.apply_theme()
        
        # Setup UI
        self.create_menu()
        self.create_toolbar()
        self.create_main_content()
        self.create_status_bar()
        
        # Bind window events
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind('<Configure>', self.on_window_configure)
        
        # Initialize client if API key is available
        self.initialize_client()
        
        # Update status
        self.update_status()

    def apply_theme(self):
        """Apply color theme to the application"""
        colors = self.config_manager.get_theme_colors()

        # Configure root window
        self.root.configure(bg=colors['bg'])

        # Try to set dark title bar on Windows
        try:
            if colors['bg'] == '#2b2b2b':  # Dark theme
                self.root.wm_attributes('-alpha', 0.99)  # Small transparency trick
                # For Windows 10/11 dark title bar
                import ctypes
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    ctypes.windll.user32.GetParent(self.root.winfo_id()),
                    20, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
                )
        except:
            pass  # Not on Windows or method not available

        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')

        # Configure ttk widget styles with comprehensive theming
        style.configure('TFrame', background=colors['frame_bg'])
        style.configure('TLabel', background=colors['frame_bg'], foreground=colors['fg'],
                        font=('Segoe UI', 10))
        style.configure('TButton', background=colors['button_bg'], foreground=colors['button_fg'],
                        font=('Segoe UI', 9))
        style.configure('TCombobox', fieldbackground=colors['entry_bg'], foreground=colors['entry_fg'],
                        font=('Segoe UI', 9))
        style.configure('TNotebook', background=colors['notebook_bg'])
        style.configure('TNotebook.Tab', background=colors['button_bg'], foreground=colors['button_fg'],
                        font=('Segoe UI', 9))

        # NEW: Configure scrollbar styles
        style.configure('Vertical.TScrollbar', background=colors['scrollbar_bg'],
                        troughcolor=colors['scrollbar_fg'], borderwidth=1)
        style.configure('Horizontal.TScrollbar', background=colors['scrollbar_bg'],
                        troughcolor=colors['scrollbar_fg'], borderwidth=1)

        # NEW: Configure paned window
        style.configure('TPanedwindow', background=colors['frame_bg'])

        # Apply theme to existing widgets
        self.apply_theme_to_widgets(self.root, colors)

        # Update response display theme
        if hasattr(self, 'response_display'):
            self.response_display.update_theme_colors(colors)

        # Update spinner theme
        if hasattr(self, 'loading_spinner'):
            self.loading_spinner.set_theme(colors['bg'] == '#2b2b2b')

        # NEW: Update main paned window theme
        if hasattr(self, 'main_paned'):
            self.main_paned.configure(bg=colors['frame_bg'])

    def apply_theme_to_widgets(self, widget, colors):
        """Recursively apply theme to all widgets"""
        try:
            widget_class = widget.winfo_class()

            if widget_class in ['Frame', 'Toplevel']:
                widget.configure(bg=colors['frame_bg'])
            elif widget_class == 'Label':
                widget.configure(bg=colors['frame_bg'], fg=colors['fg'], font=('Segoe UI', 10))
            elif widget_class == 'Button':
                widget.configure(bg=colors['button_bg'], fg=colors['button_fg'],
                                 font=('Segoe UI', 9), relief='flat')
            elif widget_class == 'Entry':
                widget.configure(bg=colors['entry_bg'], fg=colors['entry_fg'],
                                 font=('Segoe UI', 10))
            elif widget_class == 'Text':
                widget.configure(bg=colors['text_bg'], fg=colors['text_fg'],
                                 font=('Segoe UI', 10))
            elif widget_class == 'Listbox':
                widget.configure(bg=colors['listbox_bg'], fg=colors['listbox_fg'],
                                 font=('Segoe UI', 9))
            elif widget_class == 'Menu':
                widget.configure(bg=colors['menu_bg'], fg=colors['menu_fg'],
                                 font=('Segoe UI', 9))
            elif widget_class == 'PanedWindow':
                widget.configure(bg=colors['frame_bg'])
        except tk.TclError:
            pass

        # Recursively apply to children
        for child in widget.winfo_children():
            self.apply_theme_to_widgets(child, colors)

    def update_fonts_after_theme_change(self):
        """Update fonts after theme change"""
        # Update input text font
        if hasattr(self, 'input_text'):
            self.input_text.configure(font=('Inter', 11))

        # Update response display
        if hasattr(self, 'response_display'):
            self.response_display.configure(font=('JetBrains Mono', 10))
    
    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session", command=self.new_session)
        file_menu.add_command(label="Save Response", command=self.save_current_response)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Clear Chat", command=self.clear_chat)
        edit_menu.add_command(label="Copy Response", command=self.copy_response)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Audio Player", command=self.show_audio_player)
        tools_menu.add_command(label="File Manager", command=self.show_file_manager)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_toolbar(self):
        """Create toolbar with common actions"""
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Model selection
        ttk.Label(self.toolbar, text="Model:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            self.toolbar, 
            textvariable=self.model_var,
            values=self.config_manager.get_available_models(),
            state="readonly",
            width=25
        )
        self.model_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.model_combo.bind('<<ComboboxSelected>>', self.on_model_changed)
        self.model_var.set(self.config_manager.get("default_model"))
        
        # Mode selection
        ttk.Label(self.toolbar, text="Mode:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.mode_var = tk.StringVar()
        mode_values = list(self.config_manager.get_available_modes().values())
        self.mode_combo = ttk.Combobox(
            self.toolbar,
            textvariable=self.mode_var,
            values=mode_values,
            state="readonly",
            width=20
        )
        self.mode_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.mode_combo.bind('<<ComboboxSelected>>', self.on_mode_changed)
        
        # Set default mode
        current_mode = self.config_manager.get("default_mode")
        modes = self.config_manager.get_available_modes()
        if current_mode in modes:
            self.mode_var.set(modes[current_mode])
        
        # Action buttons
        ttk.Button(self.toolbar, text="New Session", 
                  command=self.new_session).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.toolbar, text="Clear", 
                  command=self.clear_chat).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.toolbar, text="Settings", 
                  command=self.show_settings).pack(side=tk.RIGHT, padx=5)
    
    def create_main_content(self):
        """Create main content area"""
        # Main paned window
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel (files and controls)
        self.left_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_panel, weight=1)
        
        # Right panel (chat and response)
        self.right_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_panel, weight=3)
        
        self.create_left_panel()
        self.create_right_panel()
        # Setup drag and drop for chat
        self.setup_chat_drag_drop()
    
    def create_left_panel(self):
        """Create left panel with file management"""
        # File list
        ttk.Label(self.left_panel, text="Attached Files:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        self.file_list = FileListWidget(self.left_panel, self.file_manager)
        self.file_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Set file list callbacks
        self.file_list.set_callback('on_file_select', self.on_files_selected)
        self.file_list.set_callback('on_file_preview', self.preview_file)
        
        # Quick actions
        actions_frame = ttk.Frame(self.left_panel)
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(actions_frame, text="Add Files", 
                  command=self.add_files).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="Clear Files", 
                  command=self.clear_files).pack(fill=tk.X, pady=2)

    def create_right_panel(self):
        """Create right panel with chat interface"""
        # Response display
        response_frame = ttk.Frame(self.right_panel)
        response_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(response_frame, text="Conversation:").pack(anchor=tk.W)

        self.response_display = ResponseDisplay(response_frame, height=20)
        self.response_display.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # Input area
        input_frame = ttk.Frame(self.right_panel)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="Your message:").pack(anchor=tk.W)

        # Input text with scrollbar
        input_text_frame = ttk.Frame(input_frame)
        input_text_frame.pack(fill=tk.X, pady=(5, 10))

        self.input_text = tk.Text(input_text_frame, height=4, wrap=tk.WORD)
        input_scrollbar = ttk.Scrollbar(input_text_frame, orient=tk.VERTICAL,
                                        command=self.input_text.yview)
        self.input_text.configure(yscrollcommand=input_scrollbar.set)

        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        input_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # NEW: Add context menu for input text
        self.input_context_menu = tk.Menu(self.input_text, tearoff=0)
        self.input_context_menu.add_command(label="Cut", command=self.cut_text)
        self.input_context_menu.add_command(label="Copy", command=self.copy_text)
        self.input_context_menu.add_command(label="Paste", command=self.paste_text)
        self.input_context_menu.add_separator()
        self.input_context_menu.add_command(label="Select All", command=self.select_all_text)
        self.input_text.bind("<Button-3>", self.show_input_context_menu)

        # NEW: Bind universal keyboard shortcuts
        self.input_text.bind("<Control-c>", lambda e: self.copy_text())
        self.input_text.bind("<Control-v>", lambda e: self.paste_text())
        self.input_text.bind("<Control-x>", lambda e: self.cut_text())
        self.input_text.bind("<Control-a>", lambda e: self.select_all_text())

        # Bind Enter key
        self.input_text.bind('<Control-Return>', lambda e: self.send_message())

        # Send button with loading indicator
        send_frame = ttk.Frame(input_frame)
        send_frame.pack(fill=tk.X)

        self.send_button = ttk.Button(send_frame, text="Send (Ctrl+Enter)",
                                      command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        # Loading frame with spinner and text
        self.loading_frame = tk.Frame(send_frame)
        is_dark = self.config_manager.get("theme") == "dark"
        self.loading_spinner = LoadingSpinner(self.loading_frame, dark_theme=is_dark)
        self.thinking_label = tk.Label(self.loading_frame, text="Thinking...",
                                       font=('Inter', 10), fg="#666666")
        # Don't pack initially - will be shown when loading

        self.save_response_button = ttk.Button(send_frame, text="Save Last Answer",
                                               command=self.save_last_response)
        self.save_response_button.pack(side=tk.RIGHT, padx=(0, 5))

    def setup_chat_drag_drop(self):
        """Setup drag and drop for chat window"""
        try:
            import tkinterdnd2 as tkdnd
            # Make the response display accept drops
            self.response_display.drop_target_register(tkdnd.DND_FILES)
            self.response_display.dnd_bind('<<Drop>>', self.on_chat_drop)

            # Also make input text accept drops
            self.input_text.drop_target_register(tkdnd.DND_FILES)
            self.input_text.dnd_bind('<<Drop>>', self.on_chat_drop)
        except:
            # tkinterdnd2 not available, skip drag and drop
            pass

    def on_chat_drop(self, event):
        """Handle files dropped into chat"""
        files = event.widget.tk.splitlist(event.data)
        added_files = []

        for file_path in files:
            if file_path not in [f['path'] for f in self.file_list.files]:
                valid, message = self.file_manager.validate_file(file_path)
                if valid:
                    file_info = self.file_manager.get_file_info(file_path)
                    self.file_list.files.append(file_info)
                    self.file_list.file_listbox.insert(tk.END, f"{file_info['name']} ({file_info['size_str']})")
                    added_files.append(file_info['name'])
                else:
                    messagebox.showerror("Invalid File", f"{os.path.basename(file_path)}: {message}")

        if added_files:
            self.response_display.add_message(f"Files added: {', '.join(added_files)}", "system")
            if self.file_list.callbacks['on_file_select']:
                self.file_list.callbacks['on_file_select'](self.file_list.get_selected_files())
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def initialize_client(self):
        """Initialize Gemini client if API key is available"""
        api_key = self.config_manager.get_api_key()
        if api_key:
            try:
                self.gemini_client = GeminiClient(api_key)
                self.gemini_async = GeminiClientAsync(self.gemini_client)
                self.status_bar.set_status("Ready")
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize Gemini client: {e}")
                return False
        else:
            self.status_bar.set_status("API key not configured")
            return False
    
    def update_status(self):
        """Update status bar information"""
        if self.gemini_client:
            self.status_bar.set_model(self.model_var.get())
            
            # Convert display mode back to key
            display_mode = self.mode_var.get()
            modes = self.config_manager.get_available_modes()
            for key, value in modes.items():
                if value == display_mode:
                    self.status_bar.set_mode(key)
                    break
    
    def on_model_changed(self, event=None):
        """Handle model selection change"""
        if self.gemini_client:
            # Clear current session when model changes
            self.gemini_client.clear_chat_session(self.current_session_id)
        self.update_status()
    
    def on_mode_changed(self, event=None):
        """Handle mode selection change"""
        self.update_status()
        
        # Show mode-specific guidance
        display_mode = self.mode_var.get()
        if "Image Generation" in display_mode:
            self.response_display.add_message(
                "Image generation mode active. Describe the image you want to create.",
                "system"
            )
        elif "Image Editing" in display_mode:
            self.response_display.add_message(
                "Image editing mode active. Upload an image and describe the changes you want.",
                "system"
            )
        elif "Audio Generation" in display_mode:
            self.response_display.add_message(
                "Audio generation mode active. Enter text to convert to speech.",
                "system"
            )
    
    def new_session(self):
        """Start a new session"""
        self.current_session_id = str(uuid.uuid4())
        if self.gemini_client:
            self.gemini_client.clear_chat_session(self.current_session_id)
        self.response_display.clear_all()
        self.clear_files()
        self.response_display.add_message("New session started.", "system")
    
    def send_message(self):
        """Send message to Gemini"""
        if not self.gemini_client:
            if not self.initialize_client():
                messagebox.showerror("Error", "Please configure your API key in Settings.")
                return
        
        message = self.input_text.get(1.0, tk.END).strip()
        if not message and self.file_list.get_file_count() == 0:
            messagebox.showwarning("Warning", "Please enter a message or attach files.")
            return

        # Show loading indicator
        self._show_loading()
        
        # Add user message to display
        if message:
            self.response_display.add_message(message, "user")
        
        # Clear input
        self.input_text.delete(1.0, tk.END)
        
        # Get current mode
        display_mode = self.mode_var.get()
        mode_key = None
        modes = self.config_manager.get_available_modes()
        for key, value in modes.items():
            if value == display_mode:
                mode_key = key
                break
        
        # Send message in separate thread
        threading.Thread(
            target=self._send_message_thread,
            args=(message, mode_key),
            daemon=True
        ).start()

    def _send_message_thread(self, message: str, mode: str):
        """Send message in separate thread"""
        try:
            logging.info(f"Sending message in {mode} mode with model {self.model_var.get()}")

            model = self.model_var.get()
            files = self.file_list.get_selected_files()

            if mode == "chat":
                response = self.gemini_client.chat_message(
                    self.current_session_id, message, model, files
                )
            elif mode == "text":
                response = self.gemini_client.generate_text(message, model, files)
            elif mode == "image":
                images, description = self.gemini_client.generate_image(message)
                self._handle_image_response(images, description)
                return
            elif mode == "edit":
                if not files:
                    self._show_error("Please attach an image file for editing.")
                    return
                images, description = self.gemini_client.edit_image(files[0], message)
                self._handle_image_response(images, description)
                return
            elif mode == "audio":
                self._handle_audio_generation(message)
                return
            else:
                response = self.gemini_client.generate_text(message, model, files)

            # Display response
            self.root.after(0, lambda: self._display_response(response))

            # NEW: Auto-clear files if option is enabled
            if self.config_manager.get("auto_clear_files", False):
                self.root.after(0, self.clear_files)
                logging.info("Auto-cleared files after response")

            logging.info("Message sent and response received successfully")

        except Exception as e:
            logging.error(f"Error in _send_message_thread: {e}")
            self.root.after(0, lambda: self._show_error(str(e)))
        finally:
            self.root.after(0, self._reset_send_button)
    
    def _handle_image_response(self, images: List, description: str):
        """Handle image generation/editing response"""
        self.root.after(0, lambda: self._display_response(description))
        
        for i, image in enumerate(images):
            # Save image
            try:
                filename = f"generated_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}.png"
                saved_path = self.file_manager.save_image(image, filename)
                
                # Show image viewer
                self.root.after(0, lambda img=image: ImageViewer(self.root, img))
                
                # Add system message about saved image
                self.root.after(0, lambda path=saved_path: 
                    self.response_display.add_message(f"Image saved to: {path}", "system"))
                
            except Exception as e:
                self.root.after(0, lambda err=str(e): 
                    self.response_display.add_message(f"Error saving image: {err}", "error"))
    
    def _handle_audio_generation(self, message: str):
        """Handle audio generation"""
        def audio_callback(audio_data, error):
            if error:
                self.root.after(0, lambda: self._show_error(f"Audio generation failed: {error}"))
            else:
                try:
                    # Save audio
                    filename = f"generated_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                    saved_path = self.file_manager.save_audio(audio_data, filename)
                    
                    # Show audio player
                    self.root.after(0, lambda: self._show_audio_player_with_file(saved_path))
                    
                    # Add system message
                    self.root.after(0, lambda: 
                        self.response_display.add_message(f"Audio generated and saved to: {saved_path}", "system"))
                    
                except Exception as e:
                    self.root.after(0, lambda: 
                        self.response_display.add_message(f"Error saving audio: {str(e)}", "error"))
            
            self.root.after(0, self._reset_send_button)
        
        self.gemini_async.generate_audio_sync(message, audio_callback)

    def _display_response(self, response: str):
        """Display response in the UI"""
        self.response_display.add_message(response, "assistant")
        logging.info("Response displayed to user")

    def _show_error(self, error_message: str):
        """Show error message"""
        self.response_display.add_message(error_message, "error")
        logging.error(f"Error shown to user: {error_message}")

    def _reset_send_button(self):
        """Reset send button state"""
        self.send_button.configure(state=tk.NORMAL)
        self.loading_spinner.stop()
        self.loading_frame.pack_forget()

    def _show_loading(self):
        """Show loading indicator"""
        self.send_button.configure(state=tk.DISABLED)
        self.loading_frame.pack(side=tk.LEFT, padx=10)
        self.loading_spinner.pack(side=tk.LEFT, padx=(0, 5))
        self.thinking_label.pack(side=tk.LEFT)
        self.loading_spinner.start()

        # Update thinking label color for theme
        colors = self.config_manager.get_theme_colors()
        self.thinking_label.configure(fg=colors['fg'], bg=colors['frame_bg'])
    
    def add_files(self):
        """Add files through file list widget"""
        self.file_list.add_files()
    
    def clear_files(self):
        """Clear all files"""
        self.file_list.clear_files()
    
    def on_files_selected(self, files: List[str]):
        """Handle file selection"""
        count = len(files)
        self.status_bar.set_status(f"Ready - {count} file(s) attached")
    
    def preview_file(self, file_info: dict):
        """Preview selected file"""
        file_path = file_info['path']
        
        if file_info['is_image']:
            try:
                from PIL import Image
                image = Image.open(file_path)
                ImageViewer(self.root, image, f"Preview: {file_info['name']}")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot preview image: {e}")
        else:
            # Show text preview dialog
            preview_text = self.file_manager.get_file_preview(file_path)
            self._show_text_preview(file_info['name'], preview_text)
    
    def _show_text_preview(self, filename: str, content: str):
        """Show text preview dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Preview: {filename}")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        
        text_widget = tk.Text(dialog, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, content)
        text_widget.configure(state=tk.DISABLED)
        
        tk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def clear_chat(self):
        """Clear chat history"""
        if messagebox.askyesno("Confirm", "Clear conversation history?"):
            self.response_display.clear_all()
            if self.gemini_client:
                self.gemini_client.clear_chat_session(self.current_session_id)
    
    def copy_response(self):
        """Copy last response to clipboard"""
        try:
            # Get all text from response display
            content = self.response_display.get(1.0, tk.END)
            if content.strip():
                self.root.clipboard_clear()
                self.root.clipboard_append(content)
                self.status_bar.set_status("Response copied to clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {e}")
    
    def save_current_response(self):
        """Save current conversation to file"""
        content = self.response_display.get(1.0, tk.END)
        if content.strip():
            try:
                filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                saved_path = self.file_manager.save_text(content, filename)
                messagebox.showinfo("Saved", f"Conversation saved to: {saved_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
        else:
            messagebox.showwarning("Warning", "No conversation to save.")

    def save_last_response(self):
        """Save only the last assistant response"""
        # Get all content and find the last assistant message
        content = self.response_display.get(1.0, tk.END)
        lines = content.split('\n')

        last_response = ""
        for i in range(len(lines) - 1, -1, -1):
            if "Assistant:" in lines[i]:
                # Found the last assistant message, collect it and following lines
                response_lines = []
                for j in range(i, len(lines)):
                    if j > i and ("You:" in lines[j] or "System:" in lines[j] or "Error:" in lines[j]):
                        break
                    response_lines.append(lines[j])
                last_response = '\n'.join(response_lines).replace("Assistant:", "").strip()
                break

        if last_response:
            try:
                filename = f"last_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                saved_path = self.file_manager.save_text(last_response, filename)
                messagebox.showinfo("Saved", f"Last response saved to: {saved_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
        else:
            messagebox.showwarning("Warning", "No assistant response found to save.")

    def send_message(self):
        """Send message to Gemini"""
        if not self.gemini_client:
            if not self.initialize_client():
                messagebox.showerror("Error", "Please configure your API key in Settings.")
                logging.error("Failed to send message: API key not configured")
                return

        message = self.input_text.get(1.0, tk.END).strip()
        if not message and self.file_list.get_file_count() == 0:
            messagebox.showwarning("Warning", "Please enter a message or attach files.")
            return

        logging.info(f"User sending message: {message[:50]}{'...' if len(message) > 50 else ''}")

        # Show loading indicator
        self._show_loading()

        # Add user message to display
        if message:
            self.response_display.add_message(message, "user")

        # Clear input
        self.input_text.delete(1.0, tk.END)

        # Get current mode
        display_mode = self.mode_var.get()
        mode_key = None
        modes = self.config_manager.get_available_modes()
        for key, value in modes.items():
            if value == display_mode:
                mode_key = key
                break

        # Send message in separate thread
        threading.Thread(
            target=self._send_message_thread,
            args=(message, mode_key),
            daemon=True
        ).start()

    def show_input_context_menu(self, event):
        """Show context menu for input text"""
        self.input_context_menu.post(event.x_root, event.y_root)

    def cut_text(self):
        """Cut selected text"""
        try:
            self.input_text.event_generate("<<Cut>>")
        except tk.TclError:
            pass

    def copy_text(self):
        """Copy selected text"""
        try:
            self.input_text.event_generate("<<Copy>>")
        except tk.TclError:
            pass

    def paste_text(self):
        """Paste text from clipboard"""
        try:
            self.input_text.event_generate("<<Paste>>")
        except tk.TclError:
            pass

    def select_all_text(self):
        """Select all text in input"""
        self.input_text.tag_add(tk.SEL, "1.0", tk.END)
        self.input_text.mark_set(tk.INSERT, "1.0")
        self.input_text.see(tk.INSERT)

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.root, self.config_manager)
        if dialog.show():
            # Reinitialize client if API key changed
            self.initialize_client()
            self.apply_theme()
            self.update_fonts_after_theme_change()  # Add this line
            self.update_status()

            # Update toolbar values
            self.model_var.set(self.config_manager.get("default_model"))
            current_mode = self.config_manager.get("default_mode")
            modes = self.config_manager.get_available_modes()
            if current_mode in modes:
                self.mode_var.set(modes[current_mode])
    
    def show_audio_player(self):
        """Show audio player window"""
        player_window = tk.Toplevel(self.root)
        player_window.title("Audio Player")
        player_window.geometry("400x100")
        player_window.transient(self.root)
        
        player = AudioPlayer(player_window, self.file_manager)
        player.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add file selection button
        tk.Button(player_window, text="Load Audio File", 
                 command=lambda: self._load_audio_file(player)).pack(pady=5)
    
    def _show_audio_player_with_file(self, file_path: str):
        """Show audio player with loaded file"""
        player_window = tk.Toplevel(self.root)
        player_window.title("Audio Player")
        player_window.geometry("400x100")
        player_window.transient(self.root)
        
        player = AudioPlayer(player_window, self.file_manager)
        player.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        player.load_audio(file_path)
    
    def _load_audio_file(self, player: AudioPlayer):
        """Load audio file into player"""
        files = self.file_manager.select_files(
            multiple=False,
            file_types=[("Audio files", "*.mp3;*.wav;*.ogg"), ("All files", "*.*")]
        )
        if files:
            player.load_audio(files[0])
    
    def show_file_manager(self):
        """Show file manager window"""
        # This could be expanded to show a full file manager
        messagebox.showinfo("File Manager", "File management is available through the left panel.")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Gemini Desktop Client

A cross-platform desktop application for interacting with Google's Gemini AI models.

Features:
• Text generation and chat with context
• Image generation and editing
• Audio generation and processing
• File upload support
• Multiple model selection
• Customizable themes

Version: 1.0.0
Built with Python and Tkinter"""
        
        messagebox.showinfo("About", about_text)
    
    def on_window_configure(self, event):
        """Handle window resize"""
        if event.widget == self.root:
            # Save window geometry
            geometry = self.root.geometry()
            self.config_manager.set("window_geometry", geometry)
    
    def on_closing(self):
        """Handle application closing"""
        # Save current session if needed
        if self.config_manager.get("auto_save_responses"):
            content = self.response_display.get(1.0, tk.END)
            if content.strip():
                try:
                    session_data = {
                        "content": content,
                        "timestamp": datetime.now().isoformat(),
                        "model": self.model_var.get(),
                        "mode": self.mode_var.get()
                    }
                    self.config_manager.save_session(self.current_session_id, session_data)
                except Exception as e:
                    print(f"Error saving session: {e}")
        
        # Cleanup
        self.file_manager.cleanup_temp_files()
        
        # Close application
        self.root.destroy()
    
    def run(self):
        """Run the application"""
        # Check for API key on startup
        if not self.config_manager.is_api_key_configured():
            messagebox.showwarning(
                "API Key Required",
                "Please configure your Gemini API key in Settings to use this application."
            )
        
        # Start main loop
        self.root.mainloop()


def main():
    """Main entry point"""
    try:
        app = MainApplication()
        app.run()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application failed to start: {e}")


if __name__ == "__main__":
    main()