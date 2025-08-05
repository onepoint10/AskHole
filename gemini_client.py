"""
Gemini API Client Module
Handles all interactions with Google's Gemini AI models
"""

from google import genai
from google.genai import types
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    Tool,
)
import io
import tempfile
import os
import asyncio
import wave
import soundfile as sf
import librosa
from PIL import Image
import mimetypes
from datetime import datetime
import threading


class GeminiClient:
    """Main client for interacting with Gemini AI models"""
    
    def __init__(self, api_key: str):
        """Initialize the Gemini client with API key"""
        self.client = genai.Client(api_key=api_key)
        self.chat_sessions = {}  # Store chat sessions by session_id
        
    def get_available_models(self):
        """Get list of available Gemini models"""
        return [
            "gemini-2.5-flash",
            "gemini-2.5-pro", 
            "gemini-2.5-flash-lite-preview-06-17"
        ]
    
    def create_chat_session(self, session_id: str, model: str):
        """Create a new chat session"""
        chat = self.client.chats.create(model=model)
        self.chat_sessions[session_id] = {
            'chat': chat,
            'model': model,
            'message_count': 0
        }
        return chat
    
    def get_chat_session(self, session_id: str, model: str):
        """Get existing chat session or create new one"""
        if (session_id not in self.chat_sessions or 
            self.chat_sessions[session_id]['model'] != model):
            return self.create_chat_session(session_id, model)
        return self.chat_sessions[session_id]['chat']
    
    def clear_chat_session(self, session_id: str):
        """Clear chat session"""
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
    
    def get_chat_history(self, session_id: str):
        """Get chat history for session"""
        if session_id not in self.chat_sessions:
            return []
        
        try:
            chat = self.chat_sessions[session_id]['chat']
            return chat.get_history()
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []

    def generate_text(self, prompt: str, model: str, files=None, temperature: float = 1.0):
        """Generate text response"""
        content_parts = [prompt]

        if files:
            for file_path in files:
                uploaded_file = self._upload_file(file_path)
                if uploaded_file:
                    content_parts.append(uploaded_file)

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=content_parts,
                config=GenerateContentConfig(
                    tools=[Tool(google_search=GoogleSearch())],
                    temperature=temperature,
                )
            )
            return response.text
        except Exception as e:
            raise Exception(f"Text generation error: {str(e)}")

    def chat_message(self, session_id: str, message: str, model: str, files=None, temperature: float = 1.0):
        """Send message in chat mode"""
        chat = self.get_chat_session(session_id, model)

        content_parts = [message]

        if files:
            for file_path in files:
                uploaded_file = self._upload_file(file_path)
                if uploaded_file:
                    content_parts.append(uploaded_file)

        try:
            response = chat.send_message(
                content_parts,
                config=GenerateContentConfig(
                    tools=[Tool(google_search=GoogleSearch())],
                    temperature=temperature,
                )
            )

            # Update message count
            if session_id in self.chat_sessions:
                self.chat_sessions[session_id]['message_count'] += 1

            return response.text
        except Exception as e:
            raise Exception(f"Chat message error: {str(e)}")
    
    def generate_image(self, prompt: str):
        """Generate image from text prompt"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )
            
            images = []
            description = ""
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    description = part.text
                elif part.inline_data is not None:
                    # Convert to PIL Image
                    image = Image.open(io.BytesIO(part.inline_data.data))
                    images.append(image)
            
            return images, description
        except Exception as e:
            raise Exception(f"Image generation error: {str(e)}")
    
    def edit_image(self, image_path: str, instruction: str):
        """Edit image based on instruction"""
        try:
            uploaded_file = self._upload_file(image_path)
            if not uploaded_file:
                raise Exception("Failed to upload image")
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents=[instruction, uploaded_file],
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )
            
            images = []
            description = ""
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    description = part.text
                elif part.inline_data is not None:
                    image = Image.open(io.BytesIO(part.inline_data.data))
                    images.append(image)
            
            return images, description
        except Exception as e:
            raise Exception(f"Image editing error: {str(e)}")
    
    async def generate_audio(self, prompt: str):
        """Generate audio from text prompt"""
        try:
            config = {
                "response_modalities": ["AUDIO"],
                "system_instruction": "You are a helpful assistant and answer in a friendly tone.",
            }
            
            audio_data = io.BytesIO()
            
            async with self.client.aio.live.connect(
                model="gemini-2.5-flash-preview-native-audio-dialog",
                config=config
            ) as session:
                await session.send_realtime_input(text=prompt)
                
                wf = wave.open(audio_data, "wb")
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                
                async for response in session.receive():
                    if response.data is not None:
                        wf.writeframes(response.data)
                
                wf.close()
                audio_data.seek(0)
            
            return audio_data
        except Exception as e:
            raise Exception(f"Audio generation error: {str(e)}")
    
    async def process_audio_input(self, audio_path: str):
        """Process audio input and return audio response"""
        try:
            # Convert audio to required format
            y, sr = librosa.load(audio_path, sr=16000)
            
            buffer = io.BytesIO()
            sf.write(buffer, y, sr, format='RAW', subtype='PCM_16')
            buffer.seek(0)
            audio_bytes = buffer.read()
            
            config = {
                "response_modalities": ["AUDIO"],
                "system_instruction": "Listen to the audio input and respond appropriately in a friendly tone.",
            }
            
            output_buffer = io.BytesIO()
            
            async with self.client.aio.live.connect(
                model="gemini-2.5-flash-preview-native-audio-dialog",
                config=config
            ) as session:
                await session.send_realtime_input(
                    audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
                )
                
                wf = wave.open(output_buffer, "wb")
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                
                async for response in session.receive():
                    if response.data is not None:
                        wf.writeframes(response.data)
                
                wf.close()
                output_buffer.seek(0)
            
            return output_buffer
        except Exception as e:
            raise Exception(f"Audio processing error: {str(e)}")
    
    def _upload_file(self, file_path: str):
        """Upload file to Gemini API"""
        if not os.path.exists(file_path):
            return None
        
        try:
            uploaded_file = self.client.files.upload(file=file_path)
            
            # Wait for processing
            max_wait = 60
            wait_time = 0
            check_interval = 2
            
            while wait_time < max_wait:
                try:
                    current_file = self.client.files.get(uploaded_file.name)
                    if current_file.state.name == "ACTIVE":
                        return current_file
                    elif current_file.state.name == "FAILED":
                        return None
                    else:
                        import time
                        time.sleep(check_interval)
                        wait_time += check_interval
                except:
                    import time
                    time.sleep(check_interval)
                    wait_time += check_interval
            
            return uploaded_file
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None
    
    def is_supported_file(self, file_path: str):
        """Check if file type is supported"""
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
            'image/heif'
        ]
        
        return mime_type in supported_types


class GeminiClientAsync:
    """Wrapper for async operations in sync context"""
    
    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client
    
    def generate_audio_sync(self, prompt: str, callback=None):
        """Generate audio synchronously with callback"""
        def run_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.client.generate_audio(prompt))
                if callback:
                    callback(result, None)
            except Exception as e:
                if callback:
                    callback(None, e)
        
        thread = threading.Thread(target=run_async)
        thread.daemon = True
        thread.start()
    
    def process_audio_sync(self, audio_path: str, callback=None):
        """Process audio synchronously with callback"""
        def run_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.client.process_audio_input(audio_path))
                if callback:
                    callback(result, None)
            except Exception as e:
                if callback:
                    callback(None, e)
        
        thread = threading.Thread(target=run_async)
        thread.daemon = True
        thread.start()
