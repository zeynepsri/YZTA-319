import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load env variables from root directory or current directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    # Optional fallback to check other keys, but default to warning
    import warnings
    warnings.warn("GEMINI_API_KEY environment variable is not set. AI agents might fail if key is not passed runtime.")

# Default model configuration
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TEXT_MODEL = "gemini-2.5-flash"

def get_genai_client():
    """
    Returns the configured genai module.
    """
    return genai
