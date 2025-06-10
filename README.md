# StudyBuddy

StudyBuddy is a personal conversational assistant with audio capabilities that can help you study and learn new concepts. It runs entirely locally without requiring any API keys from larger language models.

## Features

- Speech recognition for hands-free interaction
- Text-to-speech responses
- Interrupt detection during conversation
- Simple desktop user interface
- Document upload and discussion (MVP implementation)

## Installation

### Prerequisites

- Python 3.8 or newer
- PyQt5
- CUDA-compatible GPU recommended (but not required)

### Setup

1. Clone this repository or download the source code

2. Install dependencies:

    ```powershell
    pip install -r requirements.txt
    ```

    Note: Some dependencies may require additional system packages:

    - For audio functionality: PortAudio
    - For TTS functionality: FFmpeg

## Usage

Run the application with:

```powershell
python main.py
```

Or for systems with multiple Python installations:

```powershell
python3 main.py
```

### Command Line Options

- `--no-tts`: Disable text-to-speech functionality
- `--debug`: Enable debug logging

## Study Feature

The MVP implementation supports basic document uploading and discussion:

1. Click "Upload Document" in the UI
2. Select a text (.txt) or markdown (.md) file
3. StudyBuddy will analyze the content and can discuss it with you

## Limitations

This is an MVP (Minimum Viable Product) with the following limitations:

- Speech recognition works best in quiet environments
- Text generation capabilities are limited by the local model size
- TTS quality depends on available system resources
- Document processing is basic and limited to simple text formats

## Troubleshooting

### Audio Issues

If you encounter errors related to audio processing:

1. **File Not Found Error**: If you see `"Error processing audio: [WinError 2] The system cannot find the file specified"`:
   - Run our automated troubleshooter: `.\fix_temp_dir.ps1` (right-click and "Run with PowerShell")
   - Make sure you have write permissions to your system's temp directory
   - Verify that no antivirus or security software is blocking temp file creation
   - Try running the application with administrator privileges
   - Check if Python has permissions to create temporary files
   - Ensure your Windows user account has full control over the %TEMP% directory
   
   **Quick Fix Commands** (Run in PowerShell as Administrator):
   ```powershell
   # Check temp directory
   $tempDir = [System.IO.Path]::GetTempPath()
   Write-Host "Your temp directory is: $tempDir"
   
   # Test if you can write to the temp directory
   "Test" | Out-File -FilePath "$tempDir\test.txt"
   Remove-Item "$tempDir\test.txt"
   
   # Grant yourself full permissions
   $acl = Get-Acl $tempDir
   $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
   $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($currentUser, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
   $acl.SetAccessRule($rule)
   Set-Acl $tempDir $acl
   ```

2. **Voice Activity Detection (VAD) Issues**:
   - Run the diagnostic tool: `python audio_diagnostic.py`
   - Make sure `webrtcvad` is properly installed: `pip install --upgrade webrtcvad`
   - On Windows, you may need Microsoft Visual C++ Redistributable (download from: [Microsoft Visual C++ Redistributable](https://aka.ms/vs/16/release/vc_redist.x64.exe))
   - Ensure audio samples are properly formatted for VAD (16-bit PCM at 8, 16, 32, or 48 kHz)
   - Try reinstalling with: `pip uninstall webrtcvad && pip install webrtcvad`

3. **No Sound Input/Output**:
   - Check if your microphone and speakers are properly connected and set as default devices
   - Verify microphone permissions for the Python application
   - Try running `python -m sounddevice` to check available audio devices
   - Use the Windows Sound control panel to test your microphone
   - Verify sample rates match between your microphone and the application (16kHz)

### Helpful Troubleshooting Tools

StudyBuddy comes with several tools to help diagnose and fix issues:

1. **Audio Diagnostic Tool**: Checks your audio setup and helps identify issues
   ```powershell
   python audio_diagnostic.py
   ```

2. **Temp Directory Fixer**: Fixes common permission issues with the temp directory
   ```powershell
   .\fix_temp_dir.ps1
   ```

3. **Installation Helper**: Reinstalls and verifies dependencies
   ```powershell
   .\install.ps1
   ```

### Model Loading Issues

If the application fails to load models:

- Ensure you have sufficient disk space for downloading models
- Try running with `--debug` flag for more information
- On first run, models will be downloaded which may take time

### Environment Setup

For the best experience:

- Use a dedicated virtual environment
- Install the exact versions specified in requirements.txt
- On Windows, ensure you have the Microsoft Visual C++ Redistributable installed

## Resource Requirements

- Minimum: 4-core CPU, 8GB RAM
- Recommended: 6+ core CPU, 16GB RAM, NVIDIA GPU with 4GB+ VRAM

## License

This project is released under the MIT License.
