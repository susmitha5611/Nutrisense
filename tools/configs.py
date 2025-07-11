from mistralai import Mistral
from dotenv import load_dotenv
import os

load_dotenv()

# Mistral model configuration
mistral_model = "mistral-medium-2505"

# Mistral client
client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))

# Environment check
if not os.environ.get("MISTRAL_API_KEY"):
    print("⚠️  Warning: MISTRAL_API_KEY not found in environment variables")
    print("Please ensure your .env file contains the API key")