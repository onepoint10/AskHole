"""
OpenRouter API Client Module
Handles communication with OpenRouter R1 API using OpenAI-compatible interface
"""

import logging
from typing import List, Tuple
from openai import OpenAI


class OpenRouterClient:
    """OpenRouter API client"""

    def __init__(self, api_key: str):
        """Initialize OpenRouter client"""
        self.api_key = api_key
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.chat_sessions = {}  # Store conversation history
        logging.info("OpenRouter client initialized")

    def chat_message(self, session_id: str, message: str, model: str = "deepseek/deepseek-r1:free",
                    files: List[str] = None, temperature: float = 1.0) -> str:
        """Send a chat message with conversation context"""
        try:
            # Get or create session history
            if session_id not in self.chat_sessions:
                self.chat_sessions[session_id] = []

            messages = self.chat_sessions[session_id].copy()

            # Add user message
            user_message = {"role": "user", "content": message}

            # Handle file attachments for vision models (if supported in future)
            if files:
                logging.info(f"Files attached: {len(files)} (Note: File support varies by model)")
                # For text-only models, just mention files in the message
                if len(files) > 0:
                    file_info = f"\n\n[Note: {len(files)} file(s) were attached but may not be processed by this model]"
                    user_message["content"] += file_info

            messages.append(user_message)

            # Make API call with extra headers for OpenRouter
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                extra_headers={
                    "HTTP-Referer": "https://github.com/your-app",  # Optional
                    "X-Title": "Gemini Desktop Client",  # Optional
                }
            )

            # Extract response content
            assistant_message = response.choices[0].message
            content = assistant_message.content

            # Check if reasoning content is available (R1 specific feature)
            reasoning_content = getattr(assistant_message, 'reasoning_content', None)

            # Format response with reasoning if available
            if reasoning_content:
                formatted_response = f"**Reasoning Process:**\n{reasoning_content}\n\n**Answer:**\n{content}"
            else:
                formatted_response = content

            # Update session history
            messages.append({"role": "assistant", "content": content})
            self.chat_sessions[session_id] = messages

            logging.info(f"OpenRouter chat response generated for session {session_id}")
            return formatted_response

        except Exception as e:
            error_msg = f"OpenRouter API error: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)

    def generate_text(self, prompt: str, model: str = "deepseek/deepseek-r1:free",
                     files: List[str] = None, temperature: float = 1.0) -> str:
        """Generate text without conversation context"""
        try:
            messages = [{"role": "user", "content": prompt}]

            # Handle file attachments
            if files:
                logging.info(f"Files attached: {len(files)} (Note: File support varies by model)")
                if len(files) > 0:
                    file_info = f"\n\n[Note: {len(files)} file(s) were attached but may not be processed by this model]"
                    messages[0]["content"] += file_info

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=4000,
                extra_headers={
                    "HTTP-Referer": "https://github.com/your-app",
                    "X-Title": "Gemini Desktop Client",
                }
            )

            # Extract response content
            assistant_message = response.choices[0].message
            content = assistant_message.content

            # Check if reasoning content is available
            reasoning_content = getattr(assistant_message, 'reasoning_content', None)

            # Format response with reasoning if available
            if reasoning_content:
                formatted_response = f"**Reasoning Process:**\n{reasoning_content}\n\n**Answer:**\n{content}"
            else:
                formatted_response = content

            logging.info("OpenRouter text generation completed")
            return formatted_response

        except Exception as e:
            error_msg = f"OpenRouter API error: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)

    def clear_chat_session(self, session_id: str):
        """Clear chat session history"""
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
            logging.info(f"Cleared OpenRouter chat session: {session_id}")

    def get_available_models(self) -> List[str]:
        """Get list of available OpenRouter models"""
        return [
            "deepseek/deepseek-r1:free",
            "deepseek/deepseek-r1-0528:free",
            "tngtech/deepseek-r1t2-chimera:free",
            "tngtech/deepseek-r1t-chimera:free",
            "z-ai/glm-4.5-air:free",
            "openai/gpt-4o-mini:free",
            "openai/gpt-3.5-turbo:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "meta-llama/llama-3.2-1b-instruct:free",
            "qwen/qwen-2-7b-instruct:free"
        ]

    def test_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                extra_headers={
                    "HTTP-Referer": "https://github.com/your-app",
                    "X-Title": "Gemini Desktop Client",
                }
            )
            return True, "OpenRouter connection successful"
        except Exception as e:
            return False, f"OpenRouter connection failed: {str(e)}"


class OpenRouterClientAsync:
    """Asynchronous wrapper for OpenRouter operations"""

    def __init__(self, openrouter_client: OpenRouterClient):
        self.client = openrouter_client

    def generate_audio_sync(self, text: str, callback):
        """Audio generation not supported by OpenRouter - return error"""
        callback(None, "Audio generation is not supported by OpenRouter. Please use Gemini for audio features.")

    def generate_image_sync(self, prompt: str, callback):
        """Image generation not supported by most OpenRouter models - return error"""
        callback(None, None, "Image generation is not supported by most OpenRouter models. Please use Gemini for image features.")

    def edit_image_sync(self, image_path: str, prompt: str, callback):
        """Image editing not supported by most OpenRouter models - return error"""
        callback(None, None, "Image editing is not supported by most OpenRouter models. Please use Gemini for image features.")
#
#
# client = OpenAI(
#   base_url="https://openrouter.ai/api/v1",
#   api_key="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",
# )
# completion = client.chat.completions.create(
#   # extra_headers={
#   #   "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
#   #   "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
#   # },
#   model="tngtech/OpenRouter-r1t2-chimera:free",
#   messages=[
#     {
#       "role": "user",
#       "content": "What is the meaning of life?"
#     }
#   ]
# )
# print(completion.choices[0].message.content)