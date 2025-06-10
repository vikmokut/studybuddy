#!/usr/bin/env python
"""
Main entry point for StudyBuddy application.
"""

import sys
import os
import argparse
from PyQt5.QtWidgets import QApplication

from studybuddy_ui import ConversationalAgentUI

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="StudyBuddy - Conversational AI Study Assistant")
    parser.add_argument("--no-tts", action="store_true", help="Disable Text-to-Speech")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def check_environment():
    """Check for necessary environment components and dependencies"""
    try:
        # Check for critical dependencies
        import numpy
        import torch
        import sounddevice
        import whisper
        
        # Check if temp directory is writable
        import tempfile
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"test")
            
        return True, ""
    except ImportError as e:
        return False, f"Missing dependency: {str(e)}"
    except Exception as e:
        return False, f"Environment error: {str(e)}"

def main():
    """Main application entry point"""
    args = parse_args()
    
    # Configure logging
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        print("Debug logging enabled")
    
    # Check environment before starting
    env_ok, env_message = check_environment()
    if not env_ok:
        print(f"ERROR: {env_message}")
        print("Please run 'python audio_diagnostic.py' to troubleshoot.")
        print("You can also try reinstalling dependencies with: pip install -r requirements.txt")
        sys.exit(1)
    
    try:
        # Initialize the application
        app = QApplication(sys.argv)
        app.setApplicationName("StudyBuddy")
        
        # Create and show the main window
        window = ConversationalAgentUI()
        window.show()
        
        # Start the event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Error starting application: {e}")
        print("Please run 'python audio_diagnostic.py' to troubleshoot.")
        sys.exit(1)

if __name__ == "__main__":
    main()
