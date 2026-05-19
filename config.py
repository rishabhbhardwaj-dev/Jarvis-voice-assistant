import os
from dotenv import load_dotenv

load_dotenv()

# Groq API key — free at console.groq.com
groq_api_key = os.getenv("GROQ_API_KEY")
