#!/usr/bin/env python3
"""
StudyBuddy audio diagnostic utility.

This script helps diagnose common audio issues with the StudyBuddy application.
"""

import os
import sys
import tempfile
import platform

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def check_dependencies():
    """Check for required Python packages."""
    print_header("Checking dependencies")
    
    try:
        import numpy
        print("✓ NumPy is installed")
    except ImportError:
        print("✗ NumPy is missing. Run: pip install numpy")
    
    try:
        import sounddevice
        print("✓ Sounddevice is installed")
    except ImportError:
        print("✗ Sounddevice is missing. Run: pip install sounddevice")
        
    try:
        import webrtcvad
        print("✓ WebRTC VAD is installed")
    except ImportError:
        print("✗ WebRTC VAD is missing. Run: pip install webrtcvad")
        
    try:
        import whisper
        print("✓ Whisper is installed")
    except ImportError:
        print("✗ Whisper is missing. Check installation in requirements.txt")

def check_audio_devices():
    """Check available audio devices."""
    print_header("Checking audio devices")
    
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        print(f"Found {len(devices)} audio devices:")
        
        # Find default input/output devices
        default_input = sd.query_devices(kind='input')
        default_output = sd.query_devices(kind='output')
        
        print("\nDefault input device:")
        print(f"  {default_input['name']} (channels: {default_input['max_input_channels']})")
        
        print("\nDefault output device:")
        print(f"  {default_output['name']} (channels: {default_output['max_output_channels']})")
        
        print("\nAll devices:")
        for i, device in enumerate(devices):
            direction = []
            if device['max_input_channels'] > 0:
                direction.append("INPUT")
            if device['max_output_channels'] > 0:
                direction.append("OUTPUT")
            
            default = ""
            if device['name'] == default_input['name'] and 'INPUT' in direction:
                default = " (default input)"
            if device['name'] == default_output['name'] and 'OUTPUT' in direction:
                default = " (default output)"
                
            print(f"  [{i}] {device['name']} - {', '.join(direction)}{default}")
        
    except Exception as e:
        print(f"Error checking audio devices: {e}")

def check_temp_directory():
    """Check if the temp directory is writable."""
    print_header("Checking temporary directory")
    
    temp_dir = tempfile.gettempdir()
    print(f"Temporary directory: {temp_dir}")
    
    try:
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(b"StudyBuddy audio diagnostic test")
            tmp_path = tmp.name
            print(f"✓ Successfully created temporary file: {os.path.basename(tmp_path)}")
    except Exception as e:
        print(f"✗ Failed to write to temp directory: {e}")
        print("\nPossible solutions:")
        print("- Check permissions on the temp directory")
        print("- Check if antivirus software is blocking temp file creation")
        print("- Try running this script as administrator")

def check_system_info():
    """Display system information."""
    print_header("System information")
    
    print(f"OS: {platform.system()} {platform.release()} {platform.version()}")
    print(f"Python: {platform.python_version()}")
    print(f"Architecture: {platform.machine()}")

def check_basic_audio():
    """Try to record and play a short audio sample."""
    print_header("Testing audio recording and playback")
    
    try:
        import numpy as np
        import sounddevice as sd
        
        # Parameters
        duration = 3  # seconds
        sample_rate = 16000
        channels = 1
        
        print(f"Recording {duration} seconds of audio...")
        print("Please speak into your microphone...")
        
        # Record audio
        recording = sd.rec(int(duration * sample_rate), 
                          samplerate=sample_rate, 
                          channels=channels,
                          dtype='float32')
        sd.wait()
        
        # Check if audio was recorded
        if np.abs(recording).max() > 0.01:
            print("✓ Audio successfully recorded")
        else:
            print("⚠ Audio recorded, but signal level is very low")
            print("  Check if your microphone is properly connected and unmuted")
        
        # Playback
        print("\nPlaying back the recorded audio...")
        sd.play(recording, sample_rate)
        sd.wait()
        print("✓ Audio playback completed")
        
    except Exception as e:
        print(f"✗ Error during audio test: {e}")

def main():
    """Run all diagnostic checks."""
    print("\nStudyBuddy Audio Diagnostic Tool")
    print("--------------------------------")
    
    check_system_info()
    check_dependencies()
    check_temp_directory()
    check_audio_devices()
    
    print("\nDo you want to test audio recording/playback? (y/n)")
    response = input("> ").strip().lower()
    if response == 'y':
        check_basic_audio()
    
    print("\nDiagnostic complete!")

if __name__ == "__main__":
    main()
