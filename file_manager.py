"""
File Manager Module
Handles file operations, uploads, downloads, and media processing
"""

import os
import shutil
import tempfile
import mimetypes
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import json
import wave
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import pygame
import io
import tkinterdnd2 as tkdnd


class FileManager:
    """Manages file operations for the application"""
    
    def __init__(self, config_manager):
        """Initialize file manager"""
        self.config_manager = config_manager
        self.temp_files = []  # Track temporary files for cleanup
        self.downloads_dir = self._get_downloads_directory()
        
        # Initialize pygame mixer for audio playback
        try:
            pygame.mixer.init()
            self.audio_enabled = True
        except:
            self.audio_enabled = False
            print("Warning: Audio playback not available")
    
    def _get_downloads_directory(self) -> Path:
        """Get default downloads directory"""
        downloads_dir = Path.home() / "Downloads" / "GeminiClient"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        return downloads_dir
    
    def select_files(self, multiple=True, file_types=None) -> List[str]:
        """Open file dialog to select files"""
        if file_types is None:
            file_types = [
                ("All supported", "*.pdf;*.txt;*.docx;*.xlsx;*.pptx;*.jpg;*.jpeg;*.png;*.gif;*.webp;*.mp3;*.wav;*.ogg"),
                ("Documents", "*.pdf;*.txt;*.docx;*.xlsx;*.pptx;*.csv;*.rtf"),
                ("Images", "*.jpg;*.jpeg;*.png;*.gif;*.webp;*.heic;*.heif"),
                ("Audio", "*.mp3;*.wav;*.ogg;*.m4a"),
                ("All files", "*.*")
            ]
        
        initial_dir = self.config_manager.get("last_used_directory", str(Path.home()))
        
        if multiple:
            files = filedialog.askopenfilenames(
                title="Select files",
                initialdir=initial_dir,
                filetypes=file_types
            )
        else:
            file = filedialog.askopenfilename(
                title="Select file",
                initialdir=initial_dir,
                filetypes=file_types
            )
            files = [file] if file else []
        
        if files:
            # Update last used directory
            self.config_manager.set("last_used_directory", os.path.dirname(files[0]))
        
        return list(files)
    
    def select_save_location(self, default_name="", file_types=None) -> str:
        """Open save dialog to select save location"""
        if file_types is None:
            file_types = [("Text files", "*.txt"), ("All files", "*.*")]
        
        initial_dir = self.config_manager.get("last_used_directory", str(Path.home()))
        
        file_path = filedialog.asksaveasfilename(
            title="Save as",
            initialdir=initial_dir,
            initialfile=default_name,
            filetypes=file_types
        )
        
        if file_path:
            self.config_manager.set("last_used_directory", os.path.dirname(file_path))
        
        return file_path
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information"""
        if not os.path.exists(file_path):
            return {}
        
        stat = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": stat.st_size,
            "size_str": self._format_file_size(stat.st_size),
            "mime_type": mime_type or "unknown",
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "is_image": self._is_image_file(file_path),
            "is_audio": self._is_audio_file(file_path),
            "is_document": self._is_document_file(file_path)
        }
    
    def _format_file_size(self, size: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def _is_image_file(self, file_path: str) -> bool:
        """Check if file is an image"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type and mime_type.startswith('image/')
    
    def _is_audio_file(self, file_path: str) -> bool:
        """Check if file is an audio file"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type and mime_type.startswith('audio/')
    
    def _is_document_file(self, file_path: str) -> bool:
        """Check if file is a document"""
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            return False
        
        document_types = [
            'application/pdf',
            'text/plain',
            'application/vnd.openxmlformats-officedocument',
            'application/msword',
            'application/vnd.ms-excel',
            'application/vnd.ms-powerpoint',
            'text/csv',
            'application/rtf'
        ]
        
        return any(mime_type.startswith(doc_type) for doc_type in document_types)
    
    def create_thumbnail(self, image_path: str, size=(150, 150)) -> Optional[ImageTk.PhotoImage]:
        """Create thumbnail for image file"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None
    
    def save_image(self, image: Image.Image, filename: str = None) -> str:
        """Save PIL Image to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_image_{timestamp}.png"
        
        file_path = self.downloads_dir / filename
        
        try:
            image.save(file_path, 'PNG')
            return str(file_path)
        except Exception as e:
            raise Exception(f"Failed to save image: {e}")
    
    def save_audio(self, audio_data: io.BytesIO, filename: str = None) -> str:
        """Save audio data to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_audio_{timestamp}.wav"
        
        file_path = self.downloads_dir / filename
        
        try:
            with open(file_path, 'wb') as f:
                f.write(audio_data.getvalue())
            return str(file_path)
        except Exception as e:
            raise Exception(f"Failed to save audio: {e}")
    
    def save_text(self, text: str, filename: str = None) -> str:
        """Save text to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"response_{timestamp}.txt"
        
        file_path = self.downloads_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return str(file_path)
        except Exception as e:
            raise Exception(f"Failed to save text: {e}")
    
    def play_audio(self, audio_path: str, callback=None):
        """Play audio file"""
        if not self.audio_enabled:
            if callback:
                callback("Audio playback not available")
            return
        
        def play_thread():
            try:
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    threading.Event().wait(0.1)
                
                if callback:
                    callback(None)
            except Exception as e:
                if callback:
                    callback(str(e))
        
        thread = threading.Thread(target=play_thread)
        thread.daemon = True
        thread.start()
    
    def stop_audio(self):
        """Stop audio playback"""
        if self.audio_enabled:
            pygame.mixer.music.stop()
    
    def create_temp_file(self, suffix="", prefix="gemini_", content=None) -> str:
        """Create temporary file"""
        temp_file = tempfile.NamedTemporaryFile(
            suffix=suffix, 
            prefix=prefix, 
            delete=False
        )
        
        if content:
            if isinstance(content, str):
                temp_file.write(content.encode('utf-8'))
            else:
                temp_file.write(content)
        
        temp_file.close()
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
        self.temp_files.clear()
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate file for upload"""
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        file_size = os.path.getsize(file_path)
        if file_size > 20 * 1024 * 1024:  # 20MB limit
            return False, "File size exceeds 20MB limit"
        
        if file_size == 0:
            return False, "File is empty"
        
        # Check if file type is supported
        mime_type, _ = mimetypes.guess_type(file_path)
        supported_types = [
            'application/pdf',
            'text/plain',
            'text/csv',
            'text/html',
            'text/css',
            'text/javascript',
            'application/x-javascript',
            'text/x-typescript',
            'application/json',
            'text/xml',
            'application/rtf',
            'text/rtf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/msword',
            'application/vnd.ms-excel',
            'application/vnd.ms-powerpoint',
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
            'image/heic',
            'image/heif',
            'audio/mpeg',
            'audio/wav',
            'audio/ogg'
        ]
        
        if mime_type not in supported_types:
            return False, f"Unsupported file type: {mime_type}"
        
        return True, "File is valid"
    
    def get_file_preview(self, file_path: str, max_chars=500) -> str:
        """Get file preview text"""
        try:
            if self._is_image_file(file_path):
                return f"[Image file: {os.path.basename(file_path)}]"
            elif self._is_audio_file(file_path):
                return f"[Audio file: {os.path.basename(file_path)}]"
            elif file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(max_chars)
                    if len(content) == max_chars:
                        content += "..."
                    return content
            else:
                return f"[Document: {os.path.basename(file_path)}]"
        except Exception as e:
            return f"[Error reading file: {e}]"


class FileListWidget:
    """Widget for displaying and managing file lists"""

    def __init__(self, parent, file_manager: FileManager):
        self.parent = parent
        self.file_manager = file_manager
        self.files = []
        self.callbacks = {
            'on_file_select': None,
            'on_file_remove': None,
            'on_file_preview': None
        }

        self.create_widgets()
        self.setup_drag_drop()

    def create_widgets(self):
        """Create file list widgets"""
        # Main frame
        self.frame = tk.Frame(self.parent)

        # Toolbar
        toolbar = tk.Frame(self.frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(toolbar, text="Add Files",
                  command=self.add_files).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(toolbar, text="Clear All",
                  command=self.clear_files).pack(side=tk.LEFT)

        # File list
        list_frame = tk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollable listbox
        from tkinter import scrolledtext
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, font=('Segoe UI', 9))
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)

        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.file_listbox.bind('<Double-Button-1>', self.on_double_click)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_select)
        self.file_listbox.bind('<KeyPress-Delete>', self.on_delete_key)  # NEW: Delete key binding

        # Context menu
        self.context_menu = tk.Menu(self.file_listbox, tearoff=0)
        self.context_menu.add_command(label="Preview", command=self.preview_file)
        self.context_menu.add_command(label="Remove", command=self.remove_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Show in Explorer", command=self.show_in_explorer)

        self.file_listbox.bind("<Button-3>", self.show_context_menu)

    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        try:
            # Make the listbox accept drops
            self.file_listbox.drop_target_register(tkdnd.DND_FILES)
            self.file_listbox.dnd_bind('<<Drop>>', self.on_drop)
        except:
            # tkinterdnd2 not available, skip drag and drop
            pass

    def on_drop(self, event):
        """Handle dropped files"""
        files = self.file_listbox.tk.splitlist(event.data)
        for file_path in files:
            if file_path not in [f['path'] for f in self.files]:
                valid, message = self.file_manager.validate_file(file_path)
                if valid:
                    file_info = self.file_manager.get_file_info(file_path)
                    self.files.append(file_info)
                    self.file_listbox.insert(tk.END, f"{file_info['name']} ({file_info['size_str']})")
                else:
                    messagebox.showerror("Invalid File", f"{os.path.basename(file_path)}: {message}")

        if self.callbacks['on_file_select']:
            self.callbacks['on_file_select'](self.get_selected_files())

    def add_files(self):
        """Add files to the list"""
        files = self.file_manager.select_files(multiple=True)
        for file_path in files:
            if file_path not in [f['path'] for f in self.files]:
                valid, message = self.file_manager.validate_file(file_path)
                if valid:
                    file_info = self.file_manager.get_file_info(file_path)
                    self.files.append(file_info)
                    self.file_listbox.insert(tk.END, f"{file_info['name']} ({file_info['size_str']})")
                else:
                    messagebox.showerror("Invalid File", f"{os.path.basename(file_path)}: {message}")

        if self.callbacks['on_file_select']:
            self.callbacks['on_file_select'](self.get_selected_files())

    def clear_files(self):
        """Clear all files from the list"""
        self.files.clear()
        self.file_listbox.delete(0, tk.END)

        if self.callbacks['on_file_select']:
            self.callbacks['on_file_select']([])

    def remove_file(self):
        """Remove selected file"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            self.files.pop(index)
            self.file_listbox.delete(index)

            if self.callbacks['on_file_remove']:
                self.callbacks['on_file_remove'](index)

            if self.callbacks['on_file_select']:
                self.callbacks['on_file_select'](self.get_selected_files())

    def on_delete_key(self, event):
        """Handle Delete key press - NEW METHOD"""
        self.remove_file()

    def preview_file(self):
        """Preview selected file"""
        selection = self.file_listbox.curselection()
        if selection:
            file_info = self.files[selection[0]]
            if self.callbacks['on_file_preview']:
                self.callbacks['on_file_preview'](file_info)

    def show_in_explorer(self):
        """Show file in system explorer"""
        selection = self.file_listbox.curselection()
        if selection:
            file_path = self.files[selection[0]]['path']
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(os.path.dirname(file_path))
                elif os.name == 'posix':  # macOS/Linux
                    os.system(f'open "{os.path.dirname(file_path)}"')
            except:
                messagebox.showerror("Error", "Could not open file location")

    def show_context_menu(self, event):
        """Show context menu"""
        if self.file_listbox.curselection():
            self.context_menu.post(event.x_root, event.y_root)

    def on_double_click(self, event):
        """Handle double-click on file"""
        self.preview_file()

    def on_select(self, event):
        """Handle file selection"""
        if self.callbacks['on_file_select']:
            self.callbacks['on_file_select'](self.get_selected_files())

    def get_selected_files(self) -> List[str]:
        """Get list of selected file paths"""
        return [f['path'] for f in self.files]

    def get_file_count(self) -> int:
        """Get number of files in list"""
        return len(self.files)

    def set_callback(self, event: str, callback):
        """Set callback for events"""
        if event in self.callbacks:
            self.callbacks[event] = callback

    def pack(self, **kwargs):
        """Pack the widget"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the widget"""
        self.frame.grid(**kwargs)