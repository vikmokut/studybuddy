#!/bin/bash
# Install script for StudyBuddy dependencies on Linux/macOS systems

echo "Installing StudyBuddy dependencies..."

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "pip not found. Please install Python and pip first."
    exit 1
fi

# Create a virtual environment (optional but recommended)
echo "Creating virtual environment..."
python -m venv studybuddy_env
source studybuddy_env/bin/activate

# Install dependencies
echo "Installing Python packages..."
pip install -r requirements.txt

echo "Installation complete. Activate the environment with:"
echo "source studybuddy_env/bin/activate"
echo "Then run: python main.py"
