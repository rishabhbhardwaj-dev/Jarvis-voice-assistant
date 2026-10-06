import os
from dotenv import load_dotenv

load_dotenv()

# Groq API key — free at console.groq.com
groq_api_key = os.getenv("GROQ_API_KEY")

# Groq Models — configurable via environment variables
groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
groq_vision_model = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")

