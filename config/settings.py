import os
from dotenv import load_dotenv

load_dotenv()

EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY", "")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
