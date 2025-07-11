#!/usr/bin/env python3
"""
Setup script for NutriSense Diet Companion

This script handles potential charmap encoding issues on Windows systems
by explicitly specifying UTF-8 encoding for file operations.
"""

import os
import subprocess
import sys
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False
    return True

def setup_environment():
    """Set up environment variables"""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    print("Setting up environment variables...")
    mistral_key = input("Enter your Mistral API key (or press Enter to skip): ").strip()
    exa_key = input("Enter your Exa API key (or press Enter to skip): ").strip()
    
    env_content = f"""# Environment variables for NutriSense Diet Companion
# Get your Mistral API key from https://mistral.ai/api-key
MISTRAL_API_KEY={mistral_key if mistral_key else 'your-mistral-api-key-here'}

# Get your Exa API key from https://exa.ai/
EXA_API_KEY={exa_key if exa_key else 'your-exa-api-key-here'}

# Optional: Set chainlit settings
CHAINLIT_HOST=localhost
CHAINLIT_PORT=8000
"""
    
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        print("✅ Environment file created!")
        if not mistral_key:
            print("⚠️  Don't forget to add your Mistral API key to the .env file!")
        if not exa_key:
            print("⚠️  Don't forget to add your Exa API key to the .env file!")
        return True
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        print(f"❌ Error creating environment file (encoding issue): {e}")
        print("💡 Try running this script with: python -X utf8 setup.py")
        return False
    except Exception as e:
        print(f"❌ Error creating environment file: {e}")
        return False

def main():
    """Main setup function"""
    print("🍽️  Setting up NutriSense Diet Companion...")
    print("=" * 50)
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Setup environment
    if not setup_environment():
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Add your Mistral API key to the .env file")
    print("2. Add your Exa API key to the .env file (for web search functionality)")
    print("3. Run the application with: python run.py")
    print("4. Open your browser to http://localhost:8000")
    print("\n💡 For more information, see README.MD")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 