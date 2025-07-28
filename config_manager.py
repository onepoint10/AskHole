"""
Configuration Manager Module
Handles application settings, user preferences, and API key management
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import tkinter as tk
from tkinter import messagebox


class ConfigManager:
    """Manages application configuration and user settings"""
    
    def __init__(self):
        """Initialize configuration manager"""
        self.app_name = "GeminiDesktopClient"
        self.config_dir = self._get_config_directory()
        self.config_file = self.config_dir / "config.json"
        self.sessions_file = self.config_dir / "sessions.json"
        self.log_file = self.config_dir / "app.log"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Default configuration
        self.default_config = {
            "api_key": "",
            "default_model": "gemini-2.5-pro",
            "default_mode": "chat",
            "theme": "light",
            "window_geometry": "1200x800",
            "font_size": 10,
            "auto_save_responses": True,
            "max_response_length": 4096,
            "audio_enabled": True,
            "image_generation_enabled": True,
            "search_enabled": True,
            "last_used_directory": str(Path.home()),
            "chat_history_limit": 100,
            "auto_clear_files": False  # NEW OPTION
        }
        
        self.config = self._load_config()
        self.sessions = self._load_sessions()
        
        # Log initialization
        logging.info("ConfigManager initialized")
    
    def _setup_logging(self):
        """Setup application logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()  # Also log to console
            ]
        )
    
    def _get_config_directory(self) -> Path:
        """Get platform-specific configuration directory"""
        if os.name == 'nt':  # Windows
            config_dir = Path.home() / "AppData" / "Local" / self.app_name
        elif os.name == 'posix':  # Linux/macOS
            if os.uname().sysname == 'Darwin':  # macOS
                config_dir = Path.home() / "Library" / "Application Support" / self.app_name
            else:  # Linux
                config_dir = Path.home() / ".config" / self.app_name
        else:
            config_dir = Path.home() / f".{self.app_name.lower()}"
        
        return config_dir
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                merged_config = self.default_config.copy()
                merged_config.update(config)
                logging.info("Configuration loaded successfully")
                return merged_config
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Error loading config: {e}")
                return self.default_config.copy()
        else:
            logging.info("No existing config file, using defaults")
            return self.default_config.copy()
    
    def _load_sessions(self) -> Dict[str, Any]:
        """Load saved chat sessions"""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    sessions = json.load(f)
                logging.info("Sessions loaded successfully")
                return sessions
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Error loading sessions: {e}")
                return {}
        else:
            return {}
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logging.info("Configuration saved successfully")
        except IOError as e:
            logging.error(f"Error saving config: {e}")
    
    def save_sessions(self):
        """Save chat sessions to file"""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
            logging.info("Sessions saved successfully")
        except IOError as e:
            logging.error(f"Error saving sessions: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
        logging.info(f"Configuration updated: {key} = {value}")
    
    def get_api_key(self) -> str:
        """Get API key"""
        return self.config.get("api_key", "")
    
    def set_api_key(self, api_key: str):
        """Set API key"""
        self.config["api_key"] = api_key
        self.save_config()
        logging.info("API key updated")
    
    def is_api_key_configured(self) -> bool:
        """Check if API key is configured"""
        return bool(self.get_api_key().strip())
    
    def get_available_models(self) -> list:
        """Get list of available models"""
        return [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.5-flash-lite-preview-06-17"
        ]
    
    def get_available_modes(self) -> Dict[str, str]:
        """Get available generation modes"""
        return {
            "text": "📝 Text Generation",
            "chat": "💬 Chat with Context",
            "image": "🎨 Image Generation",
            "edit": "✏️ Image Editing",
            "audio": "🎵 Audio Generation"
        }

    def get_theme_colors(self) -> Dict[str, str]:
        """Get theme colors based on current theme"""
        if self.config.get("theme") == "dark":
            return {
                "bg": "#2b2b2b",
                "fg": "#ffffff",
                "select_bg": "#0078d4",
                "select_fg": "#ffffff",
                "entry_bg": "#404040",
                "entry_fg": "#ffffff",
                "button_bg": "#505050",
                "button_fg": "#ffffff",
                "text_bg": "#353535",
                "text_fg": "#ffffff",
                "scrollbar_bg": "#404040",
                "scrollbar_fg": "#606060",
                "frame_bg": "#2b2b2b",
                "notebook_bg": "#2b2b2b",
                "listbox_bg": "#353535",
                "listbox_fg": "#ffffff",
                "menu_bg": "#404040",
                "menu_fg": "#ffffff"
            }
        else:  # light theme
            return {
                "bg": "#ffffff",
                "fg": "#000000",
                "select_bg": "#0078d4",
                "select_fg": "#ffffff",
                "entry_bg": "#ffffff",
                "entry_fg": "#000000",
                "button_bg": "#f0f0f0",
                "button_fg": "#000000",
                "text_bg": "#ffffff",
                "text_fg": "#000000",
                "scrollbar_bg": "#f0f0f0",
                "scrollbar_fg": "#c0c0c0",
                "frame_bg": "#ffffff",
                "notebook_bg": "#ffffff",
                "listbox_bg": "#ffffff",
                "listbox_fg": "#000000",
                "menu_bg": "#f0f0f0",
                "menu_fg": "#000000"
            }
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]):
        """Save a chat session"""
        self.sessions[session_id] = session_data
        self.save_sessions()
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a chat session"""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str):
        """Delete a chat session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.save_sessions()
    
    def get_all_sessions(self) -> Dict[str, Any]:
        """Get all saved sessions"""
        return self.sessions.copy()
    
    def clear_all_sessions(self):
        """Clear all saved sessions"""
        self.sessions.clear()
        self.save_sessions()
    
    def export_config(self, file_path: str) -> bool:
        """Export configuration to file"""
        try:
            export_data = {
                "config": self.config,
                "sessions": self.sessions
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Configuration exported to {file_path}")
            return True
        except Exception as e:
            logging.error(f"Error exporting config: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if "config" in import_data:
                # Merge with defaults
                merged_config = self.default_config.copy()
                merged_config.update(import_data["config"])
                self.config = merged_config
                self.save_config()
            
            if "sessions" in import_data:
                self.sessions.update(import_data["sessions"])
                self.save_sessions()
            
            logging.info(f"Configuration imported from {file_path}")
            return True
        except Exception as e:
            logging.error(f"Error importing config: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        api_key = self.config.get("api_key", "")  # Preserve API key
        self.config = self.default_config.copy()
        self.config["api_key"] = api_key
        self.save_config()
        logging.info("Configuration reset to defaults")
    
    def validate_config(self) -> list:
        """Validate configuration and return list of issues"""
        issues = []
        
        if not self.is_api_key_configured():
            issues.append("API key is not configured")
        
        if self.config.get("default_model") not in self.get_available_models():
            issues.append("Invalid default model selected")
        
        if self.config.get("default_mode") not in self.get_available_modes():
            issues.append("Invalid default mode selected")
        
        if not isinstance(self.config.get("font_size"), int) or self.config.get("font_size") < 8:
            issues.append("Invalid font size")
        
        if not isinstance(self.config.get("chat_history_limit"), int) or self.config.get("chat_history_limit") < 1:
            issues.append("Invalid chat history limit")
        
        return issues


class SettingsDialog:
    """Settings dialog for configuration management"""
    
    def __init__(self, parent, config_manager: ConfigManager):
        self.parent = parent
        self.config_manager = config_manager
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("500x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"500x600+{x}+{y}")
        
        self.create_widgets()
        self.load_current_settings()
    
    def create_widgets(self):
        """Create settings dialog widgets"""
        # Create notebook for tabs
        from tkinter import ttk
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # General tab
        self.general_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.general_frame, text="General")
        self.create_general_tab()
        
        # API tab
        self.api_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.api_frame, text="API")
        self.create_api_tab()
        
        # Appearance tab
        self.appearance_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.appearance_frame, text="Appearance")
        self.create_appearance_tab()
        
        # Advanced tab
        self.advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.advanced_frame, text="Advanced")
        self.create_advanced_tab()
        
        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(button_frame, text="Reset to Defaults", 
                 command=self.reset_defaults).pack(side=tk.LEFT)
        
        tk.Button(button_frame, text="Cancel", 
                 command=self.cancel).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(button_frame, text="OK", 
                 command=self.ok).pack(side=tk.RIGHT)
    
    def create_general_tab(self):
        """Create general settings tab"""
        # Default model
        tk.Label(self.general_frame, text="Default Model:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.model_var = tk.StringVar()
        model_combo = tk.ttk.Combobox(self.general_frame, textvariable=self.model_var,
                                     values=self.config_manager.get_available_models(),
                                     state="readonly")
        model_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Default mode
        tk.Label(self.general_frame, text="Default Mode:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.mode_var = tk.StringVar()
        mode_values = list(self.config_manager.get_available_modes().values())
        mode_combo = tk.ttk.Combobox(self.general_frame, textvariable=self.mode_var,
                                    values=mode_values, state="readonly")
        mode_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Auto-save responses
        self.auto_save_var = tk.BooleanVar()
        tk.Checkbutton(self.general_frame, text="Auto-save responses",
                      variable=self.auto_save_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # NEW: Auto-clear files option
        self.auto_clear_files_var = tk.BooleanVar()
        tk.Checkbutton(self.general_frame, text="Auto-clear files after response",
                      variable=self.auto_clear_files_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Chat history limit
        tk.Label(self.general_frame, text="Chat History Limit:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.history_limit_var = tk.StringVar()
        tk.Entry(self.general_frame, textvariable=self.history_limit_var).grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        
        self.general_frame.columnconfigure(1, weight=1)
    
    def create_api_tab(self):
        """Create API settings tab"""
        tk.Label(self.api_frame, text="Gemini API Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.api_key_var = tk.StringVar()
        api_entry = tk.Entry(self.api_frame, textvariable=self.api_key_var, show="*")
        api_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Features
        self.search_enabled_var = tk.BooleanVar()
        tk.Checkbutton(self.api_frame, text="Enable Google Search",
                      variable=self.search_enabled_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        self.audio_enabled_var = tk.BooleanVar()
        tk.Checkbutton(self.api_frame, text="Enable Audio Generation",
                      variable=self.audio_enabled_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        self.image_enabled_var = tk.BooleanVar()
        tk.Checkbutton(self.api_frame, text="Enable Image Generation",
                      variable=self.image_enabled_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        self.api_frame.columnconfigure(1, weight=1)
    
    def create_appearance_tab(self):
        """Create appearance settings tab"""
        # Theme
        tk.Label(self.appearance_frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.theme_var = tk.StringVar()
        theme_combo = tk.ttk.Combobox(self.appearance_frame, textvariable=self.theme_var,
                                     values=["light", "dark"], state="readonly")
        theme_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Font size
        tk.Label(self.appearance_frame, text="Font Size:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.font_size_var = tk.StringVar()
        tk.Entry(self.appearance_frame, textvariable=self.font_size_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Window geometry
        tk.Label(self.appearance_frame, text="Default Window Size:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.geometry_var = tk.StringVar()
        tk.Entry(self.appearance_frame, textvariable=self.geometry_var).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        self.appearance_frame.columnconfigure(1, weight=1)
    
    def create_advanced_tab(self):
        """Create advanced settings tab"""
        # Max response length
        tk.Label(self.advanced_frame, text="Max Response Length:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_length_var = tk.StringVar()
        tk.Entry(self.advanced_frame, textvariable=self.max_length_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Last used directory
        tk.Label(self.advanced_frame, text="Default Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.directory_var = tk.StringVar()
        dir_frame = tk.Frame(self.advanced_frame)
        dir_frame.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        tk.Entry(dir_frame, textvariable=self.directory_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(dir_frame, text="Browse", command=self.browse_directory).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Export/Import buttons
        export_frame = tk.Frame(self.advanced_frame)
        export_frame.grid(row=2, column=0, columnspan=2, pady=20)
        tk.Button(export_frame, text="Export Settings", command=self.export_settings).pack(side=tk.LEFT, padx=5)
        tk.Button(export_frame, text="Import Settings", command=self.import_settings).pack(side=tk.LEFT, padx=5)
        
        self.advanced_frame.columnconfigure(1, weight=1)
    
    def load_current_settings(self):
        """Load current settings into dialog"""
        self.model_var.set(self.config_manager.get("default_model"))
        
        # Convert mode key to display value
        current_mode = self.config_manager.get("default_mode")
        modes = self.config_manager.get_available_modes()
        if current_mode in modes:
            self.mode_var.set(modes[current_mode])
        
        self.auto_save_var.set(self.config_manager.get("auto_save_responses"))
        self.auto_clear_files_var.set(self.config_manager.get("auto_clear_files"))  # NEW
        self.history_limit_var.set(str(self.config_manager.get("chat_history_limit")))
        
        self.api_key_var.set(self.config_manager.get("api_key"))
        self.search_enabled_var.set(self.config_manager.get("search_enabled"))
        self.audio_enabled_var.set(self.config_manager.get("audio_enabled"))
        self.image_enabled_var.set(self.config_manager.get("image_generation_enabled"))
        
        self.theme_var.set(self.config_manager.get("theme"))
        self.font_size_var.set(str(self.config_manager.get("font_size")))
        self.geometry_var.set(self.config_manager.get("window_geometry"))
        
        self.max_length_var.set(str(self.config_manager.get("max_response_length")))
        self.directory_var.set(self.config_manager.get("last_used_directory"))
    
    def browse_directory(self):
        """Browse for directory"""
        from tkinter import filedialog
        directory = filedialog.askdirectory(initialdir=self.directory_var.get())
        if directory:
            self.directory_var.set(directory)
    
    def export_settings(self):
        """Export settings to file"""
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            if self.config_manager.export_config(file_path):
                messagebox.showinfo("Success", "Settings exported successfully!")
            else:
                messagebox.showerror("Error", "Failed to export settings.")
    
    def import_settings(self):
        """Import settings from file"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            if self.config_manager.import_config(file_path):
                messagebox.showinfo("Success", "Settings imported successfully!")
                self.load_current_settings()
            else:
                messagebox.showerror("Error", "Failed to import settings.")
    
    def reset_defaults(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Confirm", "Reset all settings to defaults?"):
            self.config_manager.reset_to_defaults()
            self.load_current_settings()
    
    def ok(self):
        """Save settings and close dialog"""
        try:
            # Validate and save settings
            self.config_manager.set("default_model", self.model_var.get())
            
            # Convert display mode back to key
            display_mode = self.mode_var.get()
            modes = self.config_manager.get_available_modes()
            for key, value in modes.items():
                if value == display_mode:
                    self.config_manager.set("default_mode", key)
                    break
            
            self.config_manager.set("auto_save_responses", self.auto_save_var.get())
            self.config_manager.set("auto_clear_files", self.auto_clear_files_var.get())  # NEW
            self.config_manager.set("chat_history_limit", int(self.history_limit_var.get()))
            
            self.config_manager.set("api_key", self.api_key_var.get())
            self.config_manager.set("search_enabled", self.search_enabled_var.get())
            self.config_manager.set("audio_enabled", self.audio_enabled_var.get())
            self.config_manager.set("image_generation_enabled", self.image_enabled_var.get())
            
            self.config_manager.set("theme", self.theme_var.get())
            self.config_manager.set("font_size", int(self.font_size_var.get()))
            self.config_manager.set("window_geometry", self.geometry_var.get())
            
            self.config_manager.set("max_response_length", int(self.max_length_var.get()))
            self.config_manager.set("last_used_directory", self.directory_var.get())
            
            self.result = True
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid value: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def cancel(self):
        """Cancel and close dialog"""
        self.result = False
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and return result"""
        self.dialog.wait_window()
        return self.result