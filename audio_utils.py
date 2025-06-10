"""
Helper utilities for audio processing in StudyBuddy.
"""

import os
import tempfile
import numpy as np
import sounddevice as sd
import wave

def check_audio_system(sample_rate=16000):
    """
    Check if the audio system is properly configured.
    
    Returns:
        tuple: (success, message) where success is a boolean and message is a string
    """
    try:
        # Check if audio devices are available
        devices = sd.query_devices()
        if len(devices) == 0:
            return False, "No audio devices found"
            
        # Verify temp directory is writable
        try:
            with tempfile.NamedTemporaryFile(delete=True) as tmp:
                tmp.write(b"test")
        except Exception as e:
            return False, f"Temp directory not writable: {e}. Audio recording will fail."
            
        # All checks passed
        return True, "Audio system OK"
    except Exception as e:
        return False, f"Audio system check failed: {e}"

def save_audio_to_wav(audio_data, sample_rate=16000):
    """
    Save audio data to a temporary WAV file with proper error handling.
    
    Args:
        audio_data: List of audio data arrays
        sample_rate: Audio sample rate (default: 16000)
        
    Returns:
        tuple: (success, result) where success is a boolean and result is either file path or error message
    """
    temp_file = None
    try:
        # Create a secure temporary file with a guaranteed unique name
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
            temp_file = temp.name
            
        # Process the audio data
        audio_array = np.concatenate(audio_data, axis=0).flatten()
        # Normalize audio data to 16-bit PCM
        audio_array = np.clip(audio_array, -1.0, 1.0)
        audio_int16 = (audio_array * 32767).astype(np.int16)
        
        # Write WAV file using wave for better error handling
        with wave.open(temp_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes for 16-bit audio
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
        
        # Verify the file exists
        if not os.path.exists(temp_file):
            raise FileNotFoundError(f"Failed to create temporary audio file at {temp_file}")
            
        return True, temp_file
        
    except Exception as e:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        return False, str(e)

def cleanup_temp_file(file_path):
    """
    Safely remove a temporary file if it exists.
    
    Args:
        file_path: Path to the file to remove
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Warning: Could not clean up temporary file {file_path}: {e}")
        return False
