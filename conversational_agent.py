"""
Conversational agent core functionality for StudyBuddy.
"""

import torch
import sounddevice as sd
import numpy as np
import threading
import queue
import time
import os
import sys
import wave
import tempfile
from transformers import AutoModelForCausalLM, AutoTokenizer
import whisper
from audio_utils import save_audio_to_wav, cleanup_temp_file, check_audio_system as check_system

# Try to import webrtcvad - essential for voice activity detection
# Define as global variable at module level
WEBRTCVAD_AVAILABLE = False
try:
    import webrtcvad
    WEBRTCVAD_AVAILABLE = True
except ImportError:
    print("WARNING: webrtcvad not available, voice interruption detection will be disabled")

# Try to import TTS - not essential for core functionality
try:
    try:
        from TTS.api import TTS
    except ImportError:
        from TTS import TTS
    TTS_AVAILABLE = True
except ImportError:
    print("TTS not available, using system TTS fallback")
    import pyttsx3
    TTS_AVAILABLE = False

class ConversationalAgent:
    """Main class for the conversational agent"""
    
    def __init__(self, use_tts=True):
        """Initialize the conversational agent"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load speech recognition model
        print("Loading speech recognition model...")
        self.speech_model = whisper.load_model("base")
        
        # Load text generation model
        print("Loading text generation model...")
        # Using a smaller model for MVP
        model_id = "distilgpt2"
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.text_model = AutoModelForCausalLM.from_pretrained(model_id)
        
        # Text-to-Speech setup
        self.use_tts = use_tts and TTS_AVAILABLE
        if self.use_tts:
            print("Loading TTS model...")
            try:
                self.tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")
            except:
                print("Failed to load TTS model, falling back to system TTS")
                self.use_tts = False
                import pyttsx3
                self.tts_engine = pyttsx3.init()
        
        if not self.use_tts:
            print("Using system TTS")
            if 'pyttsx3' not in locals():
                import pyttsx3
            self.tts_engine = pyttsx3.init()        # Voice activity detection for interruption detection
        self.vad = None
        global WEBRTCVAD_AVAILABLE
        if WEBRTCVAD_AVAILABLE:
            try:
                self.vad = webrtcvad.Vad(3)  # Aggressiveness level 3
                print("Voice activity detection initialized")
            except Exception as e:
                print(f"Failed to initialize voice activity detection: {e}")
                WEBRTCVAD_AVAILABLE = False
        
        # Audio parameters
        self.sample_rate = 16000
        self.frame_duration = 30  # ms
        self.audio_queue = queue.Queue()
        self.is_speaking = False
        self.is_listening = False
        self.current_audio_level = 0.0
        
        # Storage for callback functions
        self.audio_callback = None
        self.callback_wrapper = None
        
    def listen(self, timeout=5):
        """Records audio from microphone and returns transcribed text"""
        self.is_listening = True
        audio_data = []
        audio_buffer = []
        frame_duration_ms = 30
        frame_size = int(self.sample_rate * frame_duration_ms / 1000)
        
        def callback(indata, frames, time, status):
            if status:
                print(f"Error: {status}")
            
            audio_buffer.append(indata.copy())
            audio_data.append(indata.copy())
            
            # Update audio level for visualization
            if hasattr(self, 'callback_wrapper') and self.callback_wrapper:
                self.callback_wrapper(indata)
            
            # Calculate current audio level
            self.current_audio_level = float(np.abs(indata).mean())
            # Check for voice activity (for interrupt detection)
            global WEBRTCVAD_AVAILABLE
            if self.is_speaking and len(audio_buffer) > 0 and self.vad is not None and WEBRTCVAD_AVAILABLE:
                # Process in 30ms chunks for VAD
                while len(audio_buffer) * frames >= frame_size:
                    # Take the right amount of data
                    chunk_data = []
                    total_frames = 0
                    while total_frames < frame_size and audio_buffer:
                        chunk = audio_buffer.pop(0)
                        chunk_data.append(chunk)
                        total_frames += len(chunk)
                    
                    if total_frames >= frame_size:
                        try:
                            # Create a 30ms audio frame
                            frame_data = np.concatenate(chunk_data, axis=0)[:frame_size]
                            frame_bytes = (frame_data * 32767).astype(np.int16).tobytes()
                            
                            # Check if it's speech
                            if self.vad.is_speech(frame_bytes, self.sample_rate):
                                self.audio_queue.put("INTERRUPT")
                                break                        
                        except Exception as e:
                            print(f"VAD error: {e}")                            # If there's a persistent VAD error, disable it
                            if str(e).find("file") >= 0:  # File-related error
                                WEBRTCVAD_AVAILABLE = False
                                print("Disabling VAD due to file errors")
        
        # Start recording
        start_time = time.time()
        with sd.InputStream(callback=callback, channels=1, samplerate=self.sample_rate, 
                           blocksize=int(self.sample_rate * 0.1)):  # 100ms blocks
            print("Listening... (Press Ctrl+C to stop)")
            try:
                while self.is_listening and (time.time() - start_time < timeout):
                    time.sleep(0.1)
            except KeyboardInterrupt:
                pass
        
        if not audio_data:
            self.is_listening = False
            return ""        # Save the audio data to a temporary file (Whisper works better with files)
        temp_file = None
        try:
            # Check if we have audio data
            if not audio_data:
                print("No audio data captured")
                self.is_listening = False
                return ""
                
            # Try to use a fixed location in user's documents if temp directory fails
            try:
                # First try with audio_utils
                success, result = save_audio_to_wav(audio_data, self.sample_rate)
                
                if not success:
                    # If that fails, try alternative approach
                    print(f"Using alternative temp file approach due to error: {result}")
                    user_dir = os.path.expanduser("~")
                    docs_dir = os.path.join(user_dir, "Documents")
                    os.makedirs(os.path.join(docs_dir, "StudyBuddy"), exist_ok=True)
                    
                    alt_temp_file = os.path.join(docs_dir, "StudyBuddy", "recording.wav")
                    
                    # Process the audio data directly
                    audio_array = np.concatenate(audio_data, axis=0).flatten()
                    audio_array = np.clip(audio_array, -1.0, 1.0)
                    audio_int16 = (audio_array * 32767).astype(np.int16)
                    
                    with wave.open(alt_temp_file, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(self.sample_rate)
                        wf.writeframes(audio_int16.tobytes())
                        
                    temp_file = alt_temp_file
                else:
                    temp_file = result
                
            except Exception as inner_e:
                print(f"Both temp file approaches failed: {inner_e}")
                print("Trying direct transcription without saving to file...")
                
                # As a last resort, try to transcribe audio directly from memory
                audio_array = np.concatenate(audio_data, axis=0).flatten()
                result = self.speech_model.transcribe(audio_array)
                text = result["text"].strip()
                
                self.is_listening = False
                return text
                
            # Verify the file exists before transcription
            if not os.path.exists(temp_file):
                raise FileNotFoundError(f"Failed to create audio file at {temp_file}")
            
            # Transcribe the audio
            print(f"Transcribing audio from {temp_file}")
            result = self.speech_model.transcribe(temp_file)
            text = result["text"].strip()
            
            self.is_listening = False
            return text        
        except Exception as e:
            print(f"Error processing audio: {e}")
            if "system cannot find the file specified" in str(e).lower():
                print("\nTemporary file error detected. Possible solutions:")
                print("1. Check if your account has write permissions to the temp directory")
                print("2. Try running as administrator")
                print("3. Check if antivirus is blocking file operations")
                print("4. Run the diagnostic: python audio_diagnostic.py\n")
            self.is_listening = False
            return ""
        finally:
            # Ensure the temporary file is always cleaned up
            if temp_file:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        print(f"Removed temporary file: {temp_file}")
                except Exception as cleanup_error:
                    print(f"Warning: Could not clean up temporary file: {cleanup_error}")
        
    def generate_response(self, user_input, document_content=None):
        """Generates text response based on user input"""
        try:
            # Include document context if available
            if document_content:
                prompt = f"Document: {document_content[:500]}...\n\nUser: {user_input}\nAssistant:"
            else:
                prompt = f"User: {user_input}\nAssistant:"
                
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            # Generate response
            outputs = self.text_model.generate(
                inputs.input_ids, 
                max_length=150,  # Longer for document discussions
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                top_k=50,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Decode the response and format it
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract just the assistant's response
            if "Assistant:" in response:
                response = response.split("Assistant:", 1)[1].strip()
            else:
                # If the model didn't follow the format correctly, take everything after the prompt
                response = response[len(prompt):].strip()
                
            return response
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm sorry, I couldn't process that properly."

    def speak(self, text):
        """Converts text to speech and plays it"""
        self.is_speaking = True
        
        try:
            if self.use_tts:
                # Use the TTS library
                wav = self.tts.tts(text)
                
                def audio_callback(_outdata, frames, _time, _status):
                    if not self.audio_queue.empty():
                        message = self.audio_queue.get()
                        if message == "INTERRUPT":
                            raise sd.CallbackAbort
                        
                # Play the generated audio
                sd.play(wav, self.sample_rate, callback=audio_callback)
                sd.wait()
            else:
                # Use system TTS
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Error during speech: {e}")
        finally:
            self.is_speaking = False

    def run(self, timeout=10):
        """Main loop for the conversational agent"""
        print("Hello! I'm your conversational agent. Start speaking to interact with me.")
        
        # Check audio system before starting
        audio_ok, message = self.check_audio_system()
        if not audio_ok:
            print(f"WARNING: {message}")
            print("Attempting to continue anyway...")
            print("For detailed diagnostics, run: python audio_diagnostic.py")
        
        # Initial greeting
        try:
            self.speak("Hello! I'm your study buddy. How can I help you today?")
        except Exception as e:
            print(f"Error during initial speech: {e}")
            print("Continuing without speech output...")
        
        error_count = 0
        max_consecutive_errors = 3
        
        while True:
            try:
                print("Listening for input... (Press Ctrl+C to stop)")
                user_input = self.listen(timeout)
                
                # Reset error count on successful operation
                error_count = 0
                
                if not user_input:
                    print("No input detected, listening again...")
                    continue
                    
                print(f"You said: {user_input}")
                
                response = self.generate_response(user_input)
                print(f"Agent: {response}")
                self.speak(response)
                
            except KeyboardInterrupt:
                print("\nStopping conversation...")
                break
                
            except Exception as e:
                error_count += 1
                print(f"Error in conversation loop: {e}")
                
                if error_count >= max_consecutive_errors:
                    print(f"Too many consecutive errors ({max_consecutive_errors}).")
                    print("Please run 'python audio_diagnostic.py' to troubleshoot audio issues.")
                    print("Exiting conversation loop.")
                    break
                print(f"Restarting conversation... (Error {error_count}/{max_consecutive_errors})")
                # Short pause before trying again
                time.sleep(1)
    
    def check_audio_system(self):
        """Check if audio system is properly configured and available"""
        # Use the utility function for basic audio checks
        audio_ok, message = check_system(self.sample_rate)
        
        # Additional check for VAD if available
        global WEBRTCVAD_AVAILABLE
        if audio_ok and WEBRTCVAD_AVAILABLE and self.vad is not None:
            try:
                # Test with 30ms of silence (480 samples at 16kHz)
                self.vad.is_speech(b'\x00' * 480, self.sample_rate)
            except Exception as e:
                print(f"Voice activity detection warning: {e}")
                print("Voice interruption detection will be disabled")
                # Don't fail completely if VAD is not working
                WEBRTCVAD_AVAILABLE = False        
        elif not WEBRTCVAD_AVAILABLE:
            print("Note: Voice activity detection not available")
            
        # Additional checks for common issues
        try:
            # Check for write access to current directory
            test_file = "test_write_access.tmp"
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            print("✓ Working directory is writable")
        except Exception as e:
            print(f"✗ Working directory is not writable: {e}")
            audio_ok = False
            message += " Working directory not writable."
        
        # Check for specific whisper usage
        try:
            # Just import and verify, don't run anything
            import whisper
            print(f"✓ Whisper module available (version: {whisper.__version__ if hasattr(whisper, '__version__') else 'unknown'})")
        except Exception as e:
            print(f"✗ Whisper import error: {e}")
        
        # If Windows, check if Visual C++ Redistributable is likely installed
        if sys.platform == 'win32':
            try:
                import ctypes
                msvcr = ctypes.CDLL('msvcp140.dll')
                print("✓ Microsoft Visual C++ Redistributable appears to be installed")
            except:
                print("⚠ Microsoft Visual C++ Redistributable might be missing")
                print("Download from: https://aka.ms/vs/16/release/vc_redist.x64.exe")
                # Don't fail completely, just warn
        
        return audio_ok, message


if __name__ == "__main__":
    agent = ConversationalAgent(use_tts=True)
    agent.run()
