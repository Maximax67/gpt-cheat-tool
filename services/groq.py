import os
from groq import Groq

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY") or "not provided")
