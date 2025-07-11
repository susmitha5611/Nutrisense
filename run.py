#!/usr/bin/env python3
"""
Run script for NutriSense Diet Companion
"""

import os
import sys
from pathlib import Path

def find_project_root():
    """Find the project root directory"""
    current_path = Path(__file__).parent.absolute()
    
    # Check if we're in the correct directory
    if (current_path / "agent.py").exists():
        return current_path
    
    # Look for nutrisense_diet_companion directory
    for parent in current_path.parents:
        nutrisense_path = parent / "nutrisense_diet_companion"
        if nutrisense_path.exists() and (nutrisense_path / "agent.py").exists():
            return nutrisense_path
    
    # Look in current working directory
    cwd = Path.cwd()
    if (cwd / "nutrisense_diet_companion" / "agent.py").exists():
        return cwd / "nutrisense_diet_companion"
    
    return None

def check_environment():
    """Check if environment is properly configured"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please run 'python setup.py' first to set up the environment.")
        return False
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key or api_key == "your-mistral-api-key-here":
            print("❌ MISTRAL_API_KEY not configured!")
            print("Please add your Mistral API key to the .env file.")
            return False
        
        exa_key = os.getenv("EXA_API_KEY")
        if not exa_key or exa_key == "your-exa-api-key-here":
            print("⚠️  EXA_API_KEY not configured!")
            print("Web search functionality will be limited without the Exa API key.")
            print("You can still use other features, but consider adding the key for full functionality.")
        
        return True
        
    except ImportError:
        print("❌ Required dependencies not installed!")
        print("Please run 'pip install -r requirements.txt' to install dependencies.")
        return False

def main():
    """Main run function"""
    print("🍽️  Starting NutriSense Diet Companion...")
    
    # Find and change to project root
    project_root = find_project_root()
    if not project_root:
        print("❌ Could not find project root directory!")
        print("Please make sure you're running this script from the correct location.")
        print("Expected to find 'agent.py' in the current directory or 'nutrisense_diet_companion' subdirectory.")
        sys.exit(1)
    
    print(f"📁 Project root: {project_root}")
    os.chdir(project_root)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    print("✅ Environment check passed")
    
    # Check for agent.py
    if not Path("agent.py").exists():
        print("❌ agent.py not found in project directory!")
        print(f"Current directory: {Path.cwd()}")
        sys.exit(1)
    
    print("🚀 Starting Chainlit application...")
    print("📱 Open your browser to http://localhost:8000")
    print("\n💡 Press Ctrl+C to stop the application")
    
    # Import and run the agent
    try:
        from chainlit.cli import run_chainlit
        run_chainlit("agent.py")
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed with 'pip install -r requirements.txt'")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("\n💡 Try running 'python test_setup.py' to diagnose issues")
        sys.exit(1)

if __name__ == "__main__":
    main() 