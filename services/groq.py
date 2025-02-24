import os
from groq import Groq

GroqClient = Groq(api_key=os.environ.get("GROQ_API_KEY"))
