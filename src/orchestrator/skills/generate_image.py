#!/usr/bin/env python3
"""
Agent Skill: Generate Image
Generates an image from a text prompt using Gemini Imagen,
then uploads to a public host (Imgur or catbox.moe) and returns the URL.
"""

import base64
import os
import sys
from typing import Dict, Any

try:
    from .base_skill import BaseSkill, run_skill
except ImportError:
    from base_skill import BaseSkill, run_skill


class GenerateImageSkill(BaseSkill):
    """Generate an image via Gemini Imagen and return a public URL."""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        prompt = params.get('prompt', '').strip()
        if not prompt:
            return {'success': False, 'error': 'prompt is required'}

        image_bytes = self._generate_with_gemini(prompt)
        image_url = self._upload_image(image_bytes)

        self.logger.info(f"Image ready: {image_url}")
        return {'success': True, 'image_url': image_url, 'prompt': prompt}

    def _generate_with_gemini(self, prompt: str) -> bytes:
        from google import genai
        from google.genai import types

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")

        client = genai.Client(api_key=api_key)
        response = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type='image/jpeg',
            ),
        )
        image_bytes = response.generated_images[0].image.image_bytes
        self.logger.info(f"Imagen generated {len(image_bytes)} bytes")
        return image_bytes

    def _upload_image(self, image_bytes: bytes) -> str:
        imgur_client_id = os.getenv('IMGUR_CLIENT_ID')
        if imgur_client_id:
            try:
                return self._upload_to_imgur(image_bytes, imgur_client_id)
            except Exception as e:
                self.logger.warning(f"Imgur failed, falling back to catbox: {e}")
        return self._upload_to_catbox(image_bytes)

    def _upload_to_imgur(self, image_bytes: bytes, client_id: str) -> str:
        import requests
        resp = requests.post(
            'https://api.imgur.com/3/image',
            headers={'Authorization': f'Client-ID {client_id}'},
            data={
                'image': base64.b64encode(image_bytes).decode('utf-8'),
                'type': 'base64',
            },
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get('success'):
            url = result['data']['link']
            self.logger.info(f"Uploaded to Imgur: {url}")
            return url
        raise RuntimeError(f"Imgur rejected upload: {result}")

    def _upload_to_catbox(self, image_bytes: bytes) -> str:
        import requests
        resp = requests.post(
            'https://catbox.moe/user/api.php',
            data={'reqtype': 'fileupload'},
            files={'fileToUpload': ('image.jpg', image_bytes, 'image/jpeg')},
            timeout=30,
        )
        resp.raise_for_status()
        url = resp.text.strip()
        if url.startswith('https://'):
            self.logger.info(f"Uploaded to catbox: {url}")
            return url
        raise RuntimeError(f"Catbox returned unexpected response: {url!r}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_image.py '<json_params>'")
        print('Example: python generate_image.py \'{"prompt": "A developer coding on a laptop in a modern office"}\'')
        sys.exit(1)
    run_skill(GenerateImageSkill, sys.argv[1])
