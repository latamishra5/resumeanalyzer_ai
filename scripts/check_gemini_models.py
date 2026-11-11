#!/usr/bin/env python3
"""
Script to check available Gemini models
"""

import os
from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
import google.generativeai as genai

from backend.config.settings import ENV_PATH


def check_available_models():
    """Check what Gemini models are available"""

    load_dotenv(ENV_PATH)
    load_dotenv()

    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not google_api_key:
        print("Google API key is not configured. Please add it to your .env file.")
        return

    try:
        genai.configure(api_key=google_api_key)

        print("Available Gemini models:")
        print("=" * 50)

        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"- {model.name}")

        print("=" * 50)

        working_models = [
            "gemini-1.0-pro",
            "gemini-pro",
            "gemini-pro-vision",
            "text-bison-001",
            "chat-bison-001",
        ]

        print("\nTesting common models:")
        for model_name in working_models:
            try:
                model = genai.GenerativeModel(model_name)
                _response = model.generate_content("Hello")
                print(f"  {model_name}: WORKING")
                break
            except Exception as e:
                print(f"  {model_name}: Not working - {str(e)[:50]}...")

    except Exception as e:
        print(f"Error checking models: {str(e)}")


if __name__ == "__main__":
    check_available_models()
