import os
import base64
from abc import ABC, abstractmethod
from typing import Optional

import google.generativeai as genai
from PIL import Image
from openai import OpenAI

class VisionAdapter(ABC):
    @abstractmethod
    def process(self, image_path: str, prompt: str) -> str:
        pass

class GoogleAdapter(VisionAdapter):
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model_name = os.getenv("VISION_MODEL", "gemini-1.5-flash")
        
    def process(self, image_path: str, prompt: str) -> str:
        try:
            model = genai.GenerativeModel(self.model_name)
            image = Image.open(image_path)
            response = model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            return f"[Gemini Error: {e}]"

class OpenAIAdapter(VisionAdapter):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model_name = os.getenv("VISION_MODEL", "gpt-4o")

    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def process(self, image_path: str, prompt: str) -> str:
        if not self.client: return "[Error: OPENAI_API_KEY not set]"
        try:
            base64_image = self._encode_image(image_path)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Error: {e}]"

def get_vision_adapter() -> VisionAdapter:
    provider = os.getenv("VISION_PROVIDER", "google").lower()
    if provider == "openai":
        return OpenAIAdapter()
    return GoogleAdapter()

def process_image(path: str, prompt: str = "Extract all text and describe any diagrams in this image.") -> str:
    adapter = get_vision_adapter()
    return adapter.process(path, prompt)
