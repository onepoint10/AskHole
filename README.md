# AskHole
# Gemini & OpenRouter Desktop Client

A cross-platform desktop application for interacting with Google's Gemini and OpenRouter's AI models. This application provides a modern, user-friendly interface for text generation, image creation, audio synthesis, and file processing using Google's Gemini AI.

## Features

### 🤖 AI Capabilities
- **Text Generation**: Generate text responses and have conversations
- **Chat with Context**: Maintain conversation history with context awareness
- **Image Generation**: Create images from text descriptions
- **Image Editing**: Modify existing images with AI-powered editing
- **Audio Generation**: Convert text to speech with AI voices
- **File Processing**: Upload and analyze documents, images, and audio files

### 🎨 User Interface
- **Modern GUI**: Clean, intuitive interface built with Tkinter
- **Dark/Light Themes**: Customizable appearance
- **File Management**: Drag-and-drop file handling with preview
- **Automatic File Convert**: Support  the most popular file formats
- **Multi-pane Layout**: Organized workspace with resizable panels
- **Real-time Status**: Live updates and progress indicators

### ⚙️ Configuration
- **Multiple Models**: Switch between Gemini Flash, Pro, Lite and free OpenRouter models 
- **Persistent Settings**: Save preferences and session data
- **Export/Import**: Backup and restore configuration
- **Cross-platform**: Works on Windows, macOS, and Linux

## Installation

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- OpenRouter API key ([Get one here](https://openrouter.ai/settings/keys))

### Setup
1. **Clone or download the project files**:
   ```bash
   git clone <repository-url>
   cd gemini-desktop-client
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main_app.py
   ```

4. **Configure API Key**:
   - Go to Settings (File → Settings)
   - Enter your Gemini API key
   - Click OK to save

5. **Create install package**:
    ```bash
   pip install pyinstaller
   pyinstaller --onefile main_app.py
   pyinstaller --onefile --windowed main_app.py
   ```

## Project Structure

The application is organized into several functional modules:

```
gemini-desktop-client/
├── main_app.py           # Main application window and orchestration
├── gemini_client.py      # Core Gemini API client and interactions
├── config_manager.py     # Configuration and settings management
├── file_manager.py       # File operations and media handling
├── ui_components.py      # Reusable UI widgets and components
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Module Overview

#### `main_app.py` (Main Application)
- Main application window and UI layout
- Event handling and user interactions
- Orchestrates all other modules
- Session management and threading

#### `gemini_client.py` (Gemini API Client)
- Direct interface to Google Gemini API
- Handles text, image, and audio generation
- Chat session management
- File upload and processing
- Async operations wrapper

- #### `openrouter_client.py` (OpenRouter API Client)
- Direct interface to OpenRouter API
- Chat session management
- File upload and processing
- Async operations wrapper

#### `config_manager.py` (Configuration Management)
- User settings and preferences
- API key management
- Theme configuration
- Session persistence
- Settings dialog interface

#### `file_manager.py` (File Operations)
- File selection and validation
- Image and audio processing
- Temporary file management
- Media playback and preview
- File list widget component

#### `ui_components.py` (UI Components)
- Reusable widgets (buttons, displays, dialogs)
- Image viewer with zoom and pan
- Audio player controls
- Progress indicators and status bars
- Chat bubble interface

## Usage Guide

### Getting Started
1. **Launch the application** by running `python main_app.py`
2. **Configure your API keys** in Settings if not already done
3. **Select a model** from the toolbar dropdown (Flash for speed, Pro for quality)
4. **Choose a mode** based on what you want to do:
   - **Chat**: Conversational AI with memory
   - **Text**: One-off text generation
   - **Image**: Create images from text
   - **Edit**: Modify existing images
   - **Audio**: Generate speech from text

### Working with Files
- **Add files**: Click "Add Files" in the left panel or use the file list toolbar
- **Preview files**: Double-click any file to preview it
- **Remove files**: Right-click and select "Remove" or use the "Clear All" button
- **Supported formats**: PDF, DOCX, TXT, JPG, PNG, MP3, WAV, and more

### Generation Modes

#### Text Generation
- Enter your prompt in the input area
- Optionally attach reference files
- Click "Send" or press Ctrl+Enter
- View the response in the conversation area

#### Chat Mode
- Have ongoing conversations with context
- Previous messages are remembered
- Use "Clear Chat" to start fresh
- View chat history with timestamps

#### Image Generation
- Describe the image you want to create
- The generated image will appear in a viewer window
- Images are automatically saved to your Downloads folder
- Multiple images may be generated per request

#### Image Editing
- Attach an image file first
- Describe the changes you want to make
- The edited image will open in the image viewer
- Original image is preserved

#### Audio Generation
- Enter text to convert to speech
- Audio will play automatically when ready
- Generated audio files are saved locally
- Use the built-in audio player for playback

### Keyboard Shortcuts
- **Ctrl+Enter**: Send message
- **Ctrl+N**: New session
- **Ctrl+S**: Save conversation
- **Ctrl+,**: Open settings
- **F1**: Show help/about

### Tips for Best Results
- **Be specific** in your prompts for better results
- **Use context** in chat mode to build on previous responses
- **Attach relevant files** to provide additional context
- **Try different models** for varying speed/quality trade-offs
- **Use image mode** for creative visual content
- **Edit mode works best** with clear, specific instructions

## Configuration

### Settings Options
- **API Key**: Your Google Gemini API key
- **OpenRouter API Key**: Your OpenRouter API key
- **Default Model**: Preferred model for new sessions
- **Default Mode**: Starting mode when launching
- **Theme**: Light or dark appearance
- **Font Size**: Text display size
- **Auto-save**: Automatically save conversations
- **File Paths**: Default directories for files

### File Locations
- **Config**: `~/.config/GeminiDesktopClient/` (Linux), `~/Library/Application Support/GeminiDesktopClient/` (macOS), `%LOCALAPPDATA%\GeminiDesktopClient\` (Windows)
- **Downloads**: `~/Downloads/GeminiClient/`
- **Sessions**: Stored in config directory as JSON

## Troubleshooting

### Common Issues

**"API key not configured"**
- Go to Settings and enter a valid Gemini API key
- Ensure the key has appropriate permissions

**"File upload failed"**
- Check file size (max 20MB)
- Verify file format is supported
- Try a different file or contact support

**"Audio not working"**
- Ensure pygame is installed (`pip install pygame`)
- Check system audio settings
- Try different audio formats

**"Application won't start"**
- Verify Python version (3.8+)
- Install all requirements (`pip install -r requirements.txt`)
- Check for error messages in terminal

### Performance Tips
- Use **Gemini Flash** for faster responses
- **Limit file sizes** for better upload performance
- **Clear chat history** periodically for memory efficiency
- **Close unused image viewers** to free resources

## Contributing

This project is structured for easy modification and extension:

1. **UI Changes**: Modify `ui_components.py` for new widgets
2. **API Features**: Extend `gemini_client.py` for new capabilities
3. **Settings**: Add options in `config_manager.py`
4. **File Handling**: Enhance `file_manager.py` for new formats

Each module is designed to be under 800 lines for maintainability.

## License

This project is provided as-is for educational and personal use. Please respect Google's Gemini API terms of service and usage limits.

## Contributing

Please raise PR for any contributions. Any PR raised will be reviewed and merged with the main branch.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Google's Gemini API documentation
3. Verify your API key and permissions
4. Check Python and dependency versions

For all questions please contact: one_point_0@icloud.com
---

**Enjoy using this app!** 🚀

**Cross-platform Gemini & OpenRouter desktop client**
