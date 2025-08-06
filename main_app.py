"""
Main Application Module
Contains the main application window and orchestrates all components
"""

import tkinter as tk
import logging
from tkinter import ttk, messagebox, Scale
import threading
import uuid
from datetime import datetime
from typing import Optional, List
import os
from gemini_client import GeminiClient, GeminiClientAsync
from openrouter_client import OpenRouterClient, OpenRouterClientAsync
from config_manager import ConfigManager, SettingsDialog
from file_manager import FileManager, FileListWidget
from ui_components import (
    ModernButton, StatusBar, ProgressDialog, ImageViewer, 
    AudioPlayer, ResponseDisplay, LoadingSpinner
)
from keyboard_shortcuts import KeyboardShortcuts
from notification_system import NotificationManager, StatusBarNotification


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

        # Initialize Openrouter client
        self.openrouter_client = None
        self.openrouter_client_async = None
        self.current_client_type = "gemini"

        # Current session
        self.current_session_id = str(uuid.uuid4())
        self.current_request_thread = None
        self.request_cancelled = False
        self.last_user_message = ""  # Store last message for error recovery

        # Create main window
        try:
            import tkinterdnd2 as tkdnd
            self.root = tkdnd.Tk()
        except ImportError:
            self.root = tk.Tk()

        self.root.title("Ask Hole App")
        self.root.iconbitmap("icon.ico")
        self.root.geometry(self.config_manager.get("window_geometry", "1920x1080"))
        
        # Apply theme
        self.apply_theme()
        
        # Setup UI
        self.create_menu()
        self.create_toolbar()
        self.create_main_content()
        self.create_status_bar()
        
        # Initialize notification system
        self.notification_manager = NotificationManager(self.root)
        self.status_notification = StatusBarNotification(self.status_bar)
        
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
        
        # Fix TCombobox styling for dark theme
        style.configure('TCombobox', 
                        fieldbackground=colors['entry_bg'], 
                        foreground=colors['entry_fg'],
                        background=colors['button_bg'],
                        bordercolor=colors['button_bg'],
                        arrowcolor=colors['entry_fg'],
                        font=('Segoe UI', 9))
        
        # Configure combobox dropdown styling
        style.map('TCombobox',
                  fieldbackground=[('readonly', colors['entry_bg'])],
                  selectbackground=[('readonly', colors['select_bg'])],
                  selectforeground=[('readonly', colors['select_fg'])],
                  foreground=[('readonly', colors['entry_fg'])])
        
        style.configure('TNotebook', background=colors['notebook_bg'])
        style.configure('TNotebook.Tab', background=colors['button_bg'], foreground=colors['button_fg'],
                        font=('Segoe UI', 9))
        
        # Map states for notebook tabs
        style.map('TNotebook.Tab',
                  background=[('selected', colors['select_bg']), ('active', colors['button_bg'])],
                  foreground=[('selected', colors['select_fg']), ('active', colors['button_fg'])])

        # Configure scrollbar styles
        style.configure('Vertical.TScrollbar', background=colors['scrollbar_bg'],
                        troughcolor=colors['scrollbar_fg'], borderwidth=1,
                        arrowcolor=colors['entry_fg'])
        style.configure('Horizontal.TScrollbar', background=colors['scrollbar_bg'],
                        troughcolor=colors['scrollbar_fg'], borderwidth=1,
                        arrowcolor=colors['entry_fg'])

        # Configure paned window
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
                                 font=('Segoe UI', 9), relief='flat',
                                 activebackground=colors['select_bg'],
                                 activeforeground=colors['select_fg'])
            elif widget_class == 'Entry':
                widget.configure(bg=colors['entry_bg'], fg=colors['entry_fg'],
                                 font=('Segoe UI', 10), insertbackground=colors['entry_fg'])
            elif widget_class == 'Text':
                widget.configure(bg=colors['text_bg'], fg=colors['text_fg'],
                                 font=('Segoe UI', 10), insertbackground=colors['text_fg'],
                                 selectbackground=colors['select_bg'],
                                 selectforeground=colors['select_fg'])
            elif widget_class == 'Listbox':
                widget.configure(bg=colors['listbox_bg'], fg=colors['listbox_fg'],
                                 font=('Segoe UI', 9),
                                 selectbackground=colors['select_bg'],
                                 selectforeground=colors['select_fg'])
            elif widget_class == 'Menu':
                widget.configure(bg=colors['menu_bg'], fg=colors['menu_fg'],
                                 font=('Segoe UI', 9),
                                 activebackground=colors['select_bg'],
                                 activeforeground=colors['select_fg'])
            elif widget_class == 'PanedWindow':
                widget.configure(bg=colors['frame_bg'])
            elif widget_class == 'Scrollbar':
                widget.configure(bg=colors['scrollbar_bg'],
                                 troughcolor=colors['scrollbar_fg'],
                                 activebackground=colors['button_bg'])
            elif widget_class == 'Scale':
                widget.configure(bg=colors['frame_bg'], fg=colors['fg'],
                                 troughcolor=colors['entry_bg'],
                                 activebackground=colors['select_bg'])
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
        file_menu.add_command(label="Save Chat", command=self.save_current_response)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Clear Chat", command=self.clear_chat)
        edit_menu.add_command(label="Copy Chat", command=self.copy_response)

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

        # Temperature control
        temp_frame = ttk.Frame(self.toolbar)
        temp_frame.pack(side=tk.RIGHT, padx=(0, 10))

        ttk.Label(temp_frame, text="Temperature:").pack(side=tk.LEFT, padx=(0, 5))

        self.temperature_var = tk.DoubleVar(value=1.0)
        self.temperature_scale = tk.Scale(
            temp_frame,
            from_=0.0,
            to=2.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.temperature_var,
            length=100,
            showvalue=0,
            command=self.on_temperature_changed
        )
        self.temperature_scale.pack(side=tk.RIGHT, padx=(0, 5))

        self.temperature_label = ttk.Label(temp_frame, text="1.0")
        self.temperature_label.pack(side=tk.LEFT)
    
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

        # Input text with scrollbar and enhanced features
        input_text_frame = ttk.Frame(input_frame)
        input_text_frame.pack(fill=tk.X, pady=(5, 10))

        self.input_text = tk.Text(input_text_frame, height=4, wrap=tk.WORD, 
                                  font=('Inter', 11), relief=tk.FLAT, bd=2, undo=True, maxundo=20)
        input_scrollbar = ttk.Scrollbar(input_text_frame, orient=tk.VERTICAL,
                                        command=self.input_text.yview)
        self.input_text.configure(yscrollcommand=input_scrollbar.set)

        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        input_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Setup keyboard shortcuts
        self.input_shortcuts = KeyboardShortcuts(self.input_text)
        # Set send message callback
        self.input_shortcuts.set_send_callback(self.send_message)

        # Create context menu for input text
        self.input_context_menu = tk.Menu(self.input_text, tearoff=0, font=('Segoe UI', 9))
        self.input_context_menu.add_command(label="Cut", command=self.input_shortcuts.cut)
        self.input_context_menu.add_command(label="Copy", command=self.input_shortcuts.copy)
        self.input_context_menu.add_command(label="Paste", command=self.input_shortcuts.paste)
        self.input_context_menu.add_separator()
        self.input_context_menu.add_command(label="Select All", command=self.input_shortcuts.select_all)
        self.input_context_menu.add_separator()
        self.input_context_menu.add_command(label="Clear", command=self._clear_input_text)

        # Enhanced context menu for input text
        self.input_text.bind("<Button-3>", self.show_input_context_menu)
        
        # Auto-resize functionality
        self.input_text.bind("<KeyRelease>", self.auto_resize_input)
        self.input_text.bind("<Button-1>", self.auto_resize_input)

        # Character count display
        self.char_count_frame = ttk.Frame(input_frame)
        self.char_count_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.char_count_var = tk.StringVar()
        self.char_count_label = ttk.Label(self.char_count_frame, textvariable=self.char_count_var, 
                                          font=('Inter', 9), foreground='#666666')
        self.char_count_label.pack(side=tk.RIGHT)
        
        # Update character count initially
        self.update_char_count()

        # Send button with loading indicator
        send_frame = ttk.Frame(input_frame)
        send_frame.pack(fill=tk.X)

        self.send_button = ttk.Button(send_frame, text="Send (Ctrl+Enter)",
                                      command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)
        self.send_button.configure(state=tk.DISABLED)

        # ADD stop button next to send button:
        self.stop_button = ttk.Button(send_frame, text="Stop",
                                      command=self.stop_request,
                                      state=tk.DISABLED)
        self.stop_button.pack(side=tk.RIGHT, padx=(0, 5))

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
                    self.notification_manager.show_error(f"{os.path.basename(file_path)}: {message}")

        if added_files:
            self.response_display.add_message(f"Files added: {', '.join(added_files)}", "system")
            if self.file_list.callbacks['on_file_select']:
                self.file_list.callbacks['on_file_select'](self.file_list.get_selected_files())
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def initialize_client(self):
        """
        Initialize AI clients if API keys are available
        """
        gemini_key = self.config_manager.get_api_key()
        openrouter_key = self.config_manager.get_openrouter_api_key()

        initialized_any = False

        # Initialize Gemini client
        if gemini_key:
            try:
                self.gemini_client = GeminiClient(gemini_key)
                self.gemini_async = GeminiClientAsync(self.gemini_client)
                initialized_any = True
                logging.info("Gemini client initialized")
            except Exception as e:
                self.notification_manager.show_error(f"Failed to initialize Gemini client: {e}")

        # Initialize openrouter client with validation
        if openrouter_key:
            try:
                self.openrouter_client = OpenRouterClient(openrouter_key)
                self.openrouter_async = OpenRouterClientAsync(self.openrouter_client)

                # Test the connection to validate the API key
                success, message = self.openrouter_client.test_connection()
                if success:
                    initialized_any = True
                    logging.info("OpenRouter client initialized and tested successfully")
                    self.notification_manager.show_success("OpenRouter client initialized and tested successfully")
                else:
                    logging.error(f"OpenRouter client failed connection test: {message}")
                    self.notification_manager.show_error(f"OpenRouter API key validation failed: {message}")
                    # Don't set the client to None, but warn the user

            except Exception as e:
                self.notification_manager.show_error(f"Failed to initialize OpenRouter client: {e}")

        if initialized_any:
            self.status_bar.set_status("Ready")
            return True
        else:
            self.status_bar.set_status("No valid API keys configured")
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
        selected_model = self.model_var.get()

        # Determine which client to use based on model
        if any(provider in selected_model.lower() for provider in
               ["deepseek", "openai", "meta-llama", "qwen", "z-ai", "tngtech", "microsoft", "mistralai", "moonshotai", "agentica"]):
            self.current_client_type = "openrouter"
            if self.openrouter_client:
                self.openrouter_client.clear_chat_session(self.current_session_id)

            # Check if OpenRouter client is available
            if not self.openrouter_client:
                self.notification_manager.show_warning(
                    "OpenRouter API key not configured. Please add it in Settings.",
                    action_text="Open Settings",
                    action_callback=self.show_settings
                )
                return

            # Show model-specific guidance
            if "deepseek" in selected_model.lower():
                self.response_display.add_message(
                    f"DeepSeek model selected: {selected_model}. This model excels at reasoning and mathematical problems. "
                    "Note: Image and audio generation are not supported.",
                    "system"
                )
            else:
                self.response_display.add_message(
                    f"OpenRouter model selected: {selected_model}. "
                    "Note: Image and audio generation may not be supported.",
                    "system"
                )
        else:
            # Gemini model
            self.current_client_type = "gemini"
            if self.gemini_client:
                self.gemini_client.clear_chat_session(self.current_session_id)
                self.response_display.add_message(
                    f"Google Gemini model selected: {selected_model}. "
                    "Note: Image and audio generation are supported.",
                    "system"
                )

            # Check if Gemini client is available
            if not self.gemini_client:
                self.notification_manager.show_warning(
                    "Gemini API key not configured. Please add it in Settings.",
                    action_text="Open Settings",
                    action_callback=self.show_settings
                )
                return

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

    def on_temperature_changed(self, value):
        """Handle temperature slider change"""
        temp_value = float(value)
        self.temperature_label.configure(text=f"{temp_value:.1f}")

    def new_session(self):
        """Start a new session"""
        self.current_session_id = str(uuid.uuid4())

        # Clear session for both clients
        if self.gemini_client:
            self.gemini_client.clear_chat_session(self.current_session_id)
        if self.openrouter_client:
            self.openrouter_client.clear_chat_session(self.current_session_id)

        self.response_display.clear_all()
        self.clear_files()
        self.response_display.add_message("New session started.", "system")

    def stop_request(self):
        """Stop current request processing"""
        self.request_cancelled = True

        # Wait for current thread to finish gracefully
        if self.current_request_thread and self.current_request_thread.is_alive():
            # Give thread a moment to see the cancellation flag
            self.root.after(100, self._complete_stop_request)
        else:
            self._complete_stop_request()

    def _complete_stop_request(self):
        """Complete the stop request after thread cleanup"""
        # Reset UI state
        self.stop_button.configure(state=tk.DISABLED)
        self.send_button.configure(state=tk.NORMAL)

        # Hide loading indicator
        self.loading_spinner.stop()
        self.loading_frame.pack_forget()

        # Update send button state properly
        self.update_send_button_state()

        # Restore the last user message
        if self.last_user_message:
            self.input_text.delete(1.0, tk.END)
            self.input_text.insert(1.0, self.last_user_message)
            self.update_char_count()
            self.auto_resize_input()

        # Update status
        self.status_bar.set_status("Ready")
        self.response_display.add_message("Request was cancelled by user.", "system")

        # Clear the cancellation flag for next request
        self.request_cancelled = False
        self.current_request_thread = None

    def send_message(self):
        """Send message to AI service"""
        # Check if any client is available
        if self.current_client_type == "openrouter":
            if not self.openrouter_client:
                if not self.initialize_client():
                    self.notification_manager.show_warning("Please configure your OpenRouter API key in Settings.",
                                                           action_text="Open Settings",
                                                           action_callback=self.show_settings)
                    return
        elif self.current_client_type == "gemini":
            if not self.gemini_client:
                if not self.initialize_client():
                    self.notification_manager.show_warning("Please configure your Gemini API key in Settings.",
                                                           action_text="Open Settings",
                                                           action_callback=self.show_settings)
                    return

        message = self.input_text.get(1.0, tk.END).strip()
        if not message and self.file_list.get_file_count() == 0:
            self.notification_manager.show_warning("Please enter a message or attach files.")
            return

        # Store the message for potential error recovery
        self.last_user_message = message
        self.request_cancelled = False

        # Show loading indicator and update button states
        self._show_loading()

        # Add user message to display
        if message:
            self.response_display.add_message(message, "user")

        # Clear input
        self.input_text.delete(1.0, tk.END)
        self.update_char_count()
        self.auto_resize_input()

        # Get current mode
        display_mode = self.mode_var.get()
        mode_key = None
        modes = self.config_manager.get_available_modes()
        for key, value in modes.items():
            if value == display_mode:
                mode_key = key
                break

        # Reset cancellation flag before starting new request
        self.request_cancelled = False

        # Send message in separate thread
        self.current_request_thread = threading.Thread(
            target=self._send_message_thread,
            args=(message, mode_key),
            daemon=True
        )
        self.current_request_thread.start()

    def _send_message_thread(self, message: str, mode: str):
        """Send message in separate thread"""
        try:
            # Check if request was cancelled before starting
            if self.request_cancelled:
                return

            logging.info(f"Sending message in {mode} mode with model {self.model_var.get()}")

            model = self.model_var.get()
            files = self.file_list.get_selected_files()
            temperature = self.temperature_var.get()

            # Check for cancellation again
            if self.request_cancelled:
                return

            # Route to appropriate client
            if self.current_client_type == "openrouter":
                # DeepSeek doesn't support image/audio generation
                if mode in ["image", "edit", "audio"]:
                    error_message = f"{mode.title()} generation is not supported by DeepSeek R1. Please switch to a Gemini model for this feature."
                    self.root.after(0, lambda: self._show_error_with_recovery(error_message))
                    return

                # Use openrouter for text/chat
                if mode == "chat":
                    response = self.openrouter_client.chat_message(
                        self.current_session_id, message, model, files, temperature
                    )
                else:  # text mode or fallback
                    response = self.openrouter_client.generate_text(message, model, files, temperature)

            else:  # Gemini client
                if mode == "chat":
                    response = self.gemini_client.chat_message(
                        self.current_session_id, message, model, files, temperature
                    )
                elif mode == "text":
                    response = self.gemini_client.generate_text(message, model, files, temperature)
                elif mode == "image":
                    images, description = self.gemini_client.generate_image(message)
                    if not self.request_cancelled:
                        self._handle_image_response(images, description)
                    return
                elif mode == "edit":
                    if not files:
                        error_message = "Please attach an image file for editing."
                        self.root.after(0, lambda: self._show_error_with_recovery(error_message))
                        return
                    images, description = self.gemini_client.edit_image(files[0], message)
                    if not self.request_cancelled:
                        self._handle_image_response(images, description)
                    return
                elif mode == "audio":
                    if not self.request_cancelled:
                        self._handle_audio_generation(message)
                    return
                else:
                    response = self.gemini_client.generate_text(message, model, files, temperature)

            # Check if request was cancelled before displaying response
            if self.request_cancelled:
                return

            # Display response
            self.root.after(0, lambda: self._display_response(response))

            # Auto-clear files if option is enabled
            if self.config_manager.get("auto_clear_files", False) and not self.request_cancelled:
                self.root.after(0, self.clear_files)
                logging.info("Auto-cleared files after response")

            # Clear the stored message only on success
            self.root.after(0, lambda: setattr(self, 'last_user_message', ""))
            logging.info("Message sent and response received successfully")

        except Exception as e:
            if not self.request_cancelled:
                error_message = str(e)
                logging.error(f"Error in _send_message_thread: {error_message}")

                # Parse API errors for better user messages
                parsed_error = self._parse_api_error(error_message)
                self.root.after(0, lambda: self._show_error_with_recovery(parsed_error))

        finally:
            if not self.request_cancelled:
                self.root.after(0, self._reset_send_button)

    def _parse_api_error(self, error_message: str) -> str:
        """Parse API error messages to provide user-friendly descriptions"""

        # Common API error patterns and their user-friendly messages
        error_patterns = {
            "503 UNAVAILABLE": {
                "title": "Service Temporarily Unavailable",
                "message": "The Gemini API is currently overloaded. Please try again in a few moments.",
                "suggestion": "• Wait 30-60 seconds and try again\n• Try using a different model if available"
            },
            "400 FAILED_PRECONDITION": {
                "title": "Request Not Supported",
                "message": "Your request cannot be processed due to API restrictions.",
                "suggestion": "• Check if your location supports this API\n• Verify your API key has proper permissions\n• Try a different model or request type"
            },
            "401 UNAUTHENTICATED": {
                "title": "Authentication Error",
                "message": "Your API key is invalid or has expired.",
                "suggestion": "• Check your API key in Settings\n• Verify the key is correctly copied\n• Generate a new API key if needed"
            },
            "403 PERMISSION_DENIED": {
                "title": "Permission Denied",
                "message": "Your API key doesn't have permission for this operation.",
                "suggestion": "• Check your API key permissions\n• Verify your account has access to this model\n• Contact support if the issue persists"
            },
            "429 RESOURCE_EXHAUSTED": {
                "title": "Rate Limit Exceeded",
                "message": "You've exceeded the API rate limits.",
                "suggestion": "• Wait before making another request\n• Consider upgrading your API plan\n• Reduce request frequency"
            },
            "404 NOT_FOUND": {
                "title": "Model Not Found",
                "message": "The requested model is not available.",
                "suggestion": "• Try a different model\n• Check if the model name is correct\n• Verify your API access level"
            }
        }

        # Extract error details from the message
        original_error = error_message

        # Check for common error patterns
        for pattern, details in error_patterns.items():
            if pattern in error_message:
                formatted_error = f"🚫 {details['title']}\n\n"
                formatted_error += f"Problem: {details['message']}\n\n"
                formatted_error += f"Solutions:\n{details['suggestion']}\n\n"
                formatted_error += f"Technical Details: {original_error}"
                return formatted_error

        # Handle network-related errors
        if "connection" in error_message.lower() or "network" in error_message.lower():
            return (f"🌐 Network Connection Error\n\n"
                    f"Problem: Unable to connect to the Gemini API.\n\n"
                    f"Solutions:\n"
                    f"• Check your internet connection\n"
                    f"• Verify firewall settings aren't blocking the connection\n"
                    f"• Try again in a few moments\n\n"
                    f"Technical Details: {original_error}")

        # Handle timeout errors
        if "timeout" in error_message.lower():
            return (f"⏱️ Request Timeout\n\n"
                    f"Problem: The request took too long to complete.\n\n"
                    f"Solutions:\n"
                    f"• Try with a shorter message or fewer files\n"
                    f"• Check your internet connection\n"
                    f"• Retry the request\n\n"
                    f"Technical Details: {original_error}")

        # Handle file-related errors
        if "file" in error_message.lower() and ("size" in error_message.lower() or "format" in error_message.lower()):
            return (f"📁 File Error\n\n"
                    f"Problem: There's an issue with the uploaded file.\n\n"
                    f"Solutions:\n"
                    f"• Check file size (must be under API limits)\n"
                    f"• Verify file format is supported\n"
                    f"• Try with a different file\n\n"
                    f"Technical Details: {original_error}")

        # Default error message for unknown errors
        return (f"❌ Unexpected Error\n\n"
                f"Problem: An unexpected error occurred while processing your request.\n\n"
                f"Solutions:\n"
                f"• Try your request again\n"
                f"• Check your internet connection\n"
                f"• Verify your API key in Settings\n"
                f"• Contact support if the issue persists\n\n"
                f"Technical Details: {original_error}")

    def _handle_image_response(self, images: List, description: str):
        """Handle image generation/editing response"""
        self.root.after(0, lambda desc=description: self._display_response(desc))

        for i, image in enumerate(images):
            # Save image
            try:
                filename = f"generated_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i + 1}.png"
                saved_path = self.file_manager.save_image(image, filename)

                # Show image viewer
                self.root.after(0, lambda img=image: ImageViewer(self.root, img))

                # Add system message about saved image with click-to-open notification
                self.root.after(0, lambda path=saved_path:
                self.notification_manager.show_file_saved_notification(
                    f"Image saved: {os.path.basename(path)}",
                    path
                ))

            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda err=error_msg:
                self.response_display.add_message(f"Error saving image: {err}", "error"))

    def _handle_audio_generation(self, message: str):
        """Handle audio generation"""

        def audio_callback(audio_data, error):
            if error:
                error_msg = f"Audio generation failed: {error}"
                self.root.after(0, lambda msg=error_msg: self._show_error_with_recovery(msg))
            else:
                try:
                    # Save audio
                    filename = f"generated_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                    saved_path = self.file_manager.save_audio(audio_data, filename)

                    # Show audio player
                    self.root.after(0, lambda path=saved_path: self._show_audio_player_with_file(path))

                    # Add system message and notification with click-to-open
                    self.root.after(0, lambda path=saved_path:
                    self.notification_manager.show_file_saved_notification(
                        f"Audio generated: {os.path.basename(path)}",
                        path
                    ))

                except Exception as e:
                    error_msg = f"Error saving audio: {str(e)}"
                    self.root.after(0, lambda msg=error_msg:
                    self.response_display.add_message(msg, "error"))

            self.root.after(0, self._reset_send_button)

        self.gemini_async.generate_audio_sync(message, audio_callback)

    def _display_response(self, response: str):
        """Display response in the UI and clear stored message"""
        markdown_enabled = self.config_manager.get("markdown_rendering", True)
        self.response_display.add_message(response, "assistant", markdown_enabled=markdown_enabled)

        # Clear the stored message since response was successful
        self.last_user_message = ""

        # Reset UI state
        self._reset_send_button()

        logging.info("Response displayed to user")

    def _show_error_with_recovery(self, error_message: str):
        """Show error message with UI recovery and message restoration"""
        # Add error to response display
        self.response_display.add_message(error_message, "error")

        # Reset UI state
        self._reset_send_button()

        # Restore the user's message to input field
        if self.last_user_message:
            self.input_text.delete(1.0, tk.END)
            self.input_text.insert(1.0, self.last_user_message)
            self.update_char_count()
            self.auto_resize_input()

        # Show appropriate notifications based on error type
        try:
            if any(keyword in error_message.lower() for keyword in
                   ["authentication", "api key", "permission", "unauthenticated", "401"]):
                self.notification_manager.show_error(
                    "API Authentication Issue - Check your settings!",
                    action_text="Open Settings",
                    action_callback=self.show_settings,
                    duration=0  # Keep visible until dismissed
                )
            elif any(keyword in error_message.lower() for keyword in
                     ["503", "overloaded", "unavailable", "service"]):
                self.notification_manager.show_warning(
                    "Gemini API is temporarily overloaded. Please try again in a moment.",
                    duration=8000
                )
            elif any(keyword in error_message.lower() for keyword in
                     ["network", "connection", "timeout"]):
                self.notification_manager.show_warning(
                    "Network connection issue. Please check your internet connection.",
                    duration=6000
                )
            elif any(keyword in error_message.lower() for keyword in
                     ["rate limit", "429", "quota", "exceeded"]):
                self.notification_manager.show_warning(
                    "Rate limit exceeded. Please wait before making another request.",
                    duration=8000
                )
            else:
                # Generic error notification
                self.notification_manager.show_error(
                    "Request failed. Your message has been restored to the input field.",
                    duration=6000
                )
        except Exception as e:
            logging.error(f"Error showing notification: {e}")

        # Update status bar
        self.status_bar.set_status("Ready - Error occurred")
        logging.error(f"Error shown to user: {error_message}")

    def _reset_send_button(self):
        """Reset send button state"""
        self.send_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.loading_spinner.stop()
        self.loading_frame.pack_forget()
        self.update_send_button_state()  # Restore proper state based on content
        self.current_request_thread = None

        # Update status bar
        self.status_bar.set_status("Ready")

    def _show_loading(self):
        """Show loading indicator"""
        self.send_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.loading_frame.pack(side=tk.LEFT, padx=10)
        self.loading_spinner.pack(side=tk.LEFT, padx=(0, 5))
        self.thinking_label.pack(side=tk.LEFT)
        self.loading_spinner.start()

        # Update thinking label color for theme
        colors = self.config_manager.get_theme_colors()
        self.thinking_label.configure(fg=colors['fg'], bg=colors['frame_bg'])

    def update_send_button_state(self):
        """Update send button state based on input content"""
        message = self.input_text.get(1.0, tk.END).strip()
        has_files = self.file_list.get_file_count() > 0

        # Enable button if there's text or files attached
        if message or has_files:
            self.send_button.configure(state=tk.NORMAL)
        else:
            self.send_button.configure(state=tk.DISABLED)
    
    def add_files(self):
        """Add files through file list widget"""
        self.file_list.add_files()

    def clear_files(self):
        """Clear all files"""
        self.file_list.clear_files()
        # Update send button state when files are cleared
        self.update_send_button_state()

    def on_files_selected(self, files: List[str]):
        """Handle file selection"""
        count = len(files)
        self.status_bar.set_status(f"Ready - {count} file(s) attached")
        # Update send button state when files change
        self.update_send_button_state()
    
    def preview_file(self, file_info: dict):
        """Preview selected file"""
        file_path = file_info['path']
        
        if file_info['is_image']:
            try:
                from PIL import Image
                image = Image.open(file_path)
                ImageViewer(self.root, image, f"Preview: {file_info['name']}")
            except Exception as e:
                self.notification_manager.show_error(f"Cannot preview image: {e}")
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

    def _clear_input_text(self):
        """Clear all text in input field"""
        self.input_text.delete(1.0, tk.END)
        self.update_char_count()
        self.auto_resize_input()
    
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
            self.notification_manager.show_error(f"Failed to copy: {e}")

    def save_current_response(self):
        """Save current conversation to file"""
        content = self.response_display.get(1.0, tk.END)
        if content.strip():
            try:
                filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                saved_path = self.file_manager.save_text(content, filename)
                self.notification_manager.show_file_saved_notification(
                    f"Conversation saved to: {os.path.basename(saved_path)}",
                    saved_path
                )
            except Exception as e:
                self.notification_manager.show_error(f"Failed to save: {e}")
        else:
            self.notification_manager.show_warning("No conversation to save.")

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
                self.notification_manager.show_file_saved_notification(
                    f"Last response saved to: {os.path.basename(saved_path)}",
                    saved_path
                )
            except Exception as e:
                self.notification_manager.show_error(f"Failed to save: {e}")
        else:
            self.notification_manager.show_warning("No assistant response found to save.")

    def show_input_context_menu(self, event):
        """Show context menu for input text"""
        try:
            # Update menu item states based on current selection and clipboard
            has_selection = bool(self.input_text.tag_ranges(tk.SEL))

            # Enable/disable menu items
            self.input_context_menu.entryconfig("Cut", state=tk.NORMAL if has_selection else tk.DISABLED)
            self.input_context_menu.entryconfig("Copy", state=tk.NORMAL if has_selection else tk.DISABLED)

            # Check if clipboard has content
            try:
                self.root.clipboard_get()
                self.input_context_menu.entryconfig("Paste", state=tk.NORMAL)
            except tk.TclError:
                self.input_context_menu.entryconfig("Paste", state=tk.DISABLED)

            # Show menu
            self.input_context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing context menu: {e}")
        finally:
            self.input_context_menu.grab_release()


    def auto_resize_input(self, event=None):
        """Auto-resize input text widget based on content"""
        content = self.input_text.get(1.0, tk.END)
        lines = content.count('\n') + 1

        # Limit height between 4 and 12 lines
        new_height = max(4, min(12, lines))
        current_height = int(self.input_text.cget('height'))

        if new_height != current_height:
            self.input_text.configure(height=new_height)

        # Update character count
        self.update_char_count()

        # Update send button state
        self.update_send_button_state()

    def update_char_count(self):
        """Update character count display"""
        content = self.input_text.get(1.0, tk.END)
        char_count = len(content) - 1  # Subtract 1 for the trailing newline
        word_count = len(content.split()) if content.strip() else 0
        
        self.char_count_var.set(f"{char_count} chars, {word_count} words")

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.root, self.config_manager)
        if dialog.show():
            # Reinitialize client if API key changed
            self.initialize_client()
            self.apply_theme()
            self.update_fonts_after_theme_change()
            self.update_status()

            # Update toolbar values
            self.model_var.set(self.config_manager.get("default_model"))
            current_mode = self.config_manager.get("default_mode")
            modes = self.config_manager.get_available_modes()
            if current_mode in modes:
                self.mode_var.set(modes[current_mode])

            # Update markdown rendering setting for response display
            markdown_enabled = self.config_manager.get("markdown_rendering", True)
            self.response_display.toggle_markdown_rendering(markdown_enabled)
    
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
        self.notification_manager.show_info("File management is available through the left panel.")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Ask Hole App (Gemini & OpenRouter Desktop Client)

A cross-platform desktop application for interacting with Google's Gemini & OpenRouter's AI models.

Features:
• Text generation and chat with context
• Image generation and editing
• Audio generation and processing
• File upload support
• Multiple model selection
• Customizable themes

Version: 1.0.1
For all questions please contact: one_point_0@icloud.com
Built with Python and Tkinter"""
        
        # Keep about dialog as messagebox since it's a detailed informational dialog
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
        if (not self.config_manager.is_api_key_configured()) and not (self.config_manager.is_openrouter_api_key_configured()):
            self.notification_manager.show_warning(
                "Please configure your Gemini API key in Settings to use this application.",
                action_text="Open Settings",
                action_callback=self.show_settings,
                duration=0  # Permanent until dismissed
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