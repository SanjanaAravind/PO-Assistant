import os
import base64
from typing import Dict, Optional
from PIL import Image
import google.generativeai as genai
from config import config
import time

class ImageProcessor:
    def __init__(self, image_storage_path: str = "data/images"):
        self.image_storage_path = image_storage_path
        self._ensure_storage_exists()
        
        # Configure Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def _ensure_storage_exists(self):
        """Ensure the image storage directory exists"""
        os.makedirs(self.image_storage_path, exist_ok=True)

    def _encode_image(self, image_path: str) -> str:
        """Convert image to base64 string"""
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def save_image(self, image_path: str, project_key: str) -> Dict:
        """
        Save an image and generate its description using Gemini
        Returns a dict with image metadata and description
        """
        # Validate image
        try:
            with Image.open(image_path) as img:
                img.verify()
                # Get the actual format from the image
                img_format = img.format.lower() if img.format else 'png'
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")

        # Generate a filename based on timestamp and project key
        timestamp = int(time.time())
        filename = f"{project_key}_{timestamp}.{img_format}"
        target_path = os.path.join(self.image_storage_path, filename)
        
        # Copy image to storage
        with Image.open(image_path) as img:
            img.save(target_path, format=img_format)

        # Generate description using Gemini
        try:
            with Image.open(target_path) as img:
                response = self.model.generate_content([
                    "Describe this image in detail, focusing on any text, diagrams, or technical content visible. If it's a screenshot or technical diagram, explain its components and purpose.",
                    img
                ])
            description = response.text
        except Exception as e:
            description = f"Error generating description: {str(e)}"

        return {
            'project_key': project_key,
            'image_path': target_path,
            'description': description,
            'type': 'image'
        }

# Create a global instance
image_processor = ImageProcessor() 