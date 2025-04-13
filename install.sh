#!/usr/bin/env bash

# SYNOPSIS:
#   Installs Python dependencies and the 'faw' command for Bash/Zsh.
#
# DESCRIPTION:
#   This script first installs required Python packages from requirements.txt
#   using pip. Then, it adds a function named 'faw' to your shell profile file
#   (~/.bashrc or ~/.zshrc) to run the find_a_workinator.py script easily.
#
# NOTES:
#   File Name: install.sh
#   Requires : Bash or Zsh, Python 3+ with pip available (preferably as 'python3').
#              A 'requirements.txt' file must exist in the same directory.
#   Usage    : chmod +x install.sh && ./install.sh
#

# --- Configuration ---
SCRIPT_PYTHON_NAME="find_a_workinator.py"
REQUIREMENTS_FILENAME="requirements.txt"
FUNCTION_NAME="faw"

# --- Helper Function for Colored Output ---
color_echo() {
    local color_code="$1"; shift; local message="$@";
    if [ -t 1 ]; then echo -e "\033[${color_code}m${message}\033[0m"; else echo "${message}"; fi
}
info() { color_echo "36" "$@"; }      # Cyan
success() { color_echo "32" "$@"; }   # Green
warning() { color_echo "33" "$@"; }   # Yellow
error() { color_echo "31" "$@"; }     # Red

# --- Script Logic ---

info "Starting installation for '$FUNCTION_NAME' command..."

# Get the absolute directory where this installation script is located
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "$INSTALL_DIR" ]; then
    error "Could not determine the script installation directory."; exit 1
fi

# Construct the full path to the target Python script and requirements file
TARGET_SCRIPT_PATH="$INSTALL_DIR/$SCRIPT_PYTHON_NAME"
REQUIREMENTS_PATH="$INSTALL_DIR/$REQUIREMENTS_FILENAME"

# Verify that the target Python script exists
if [ ! -f "$TARGET_SCRIPT_PATH" ]; then
    error "Python script '$SCRIPT_PYTHON_NAME' not found at: $TARGET_SCRIPT_PATH"; exit 1
fi
info "Python script found at: $TARGET_SCRIPT_PATH"

# --- Install Dependencies ---
info "Checking for requirements file: $REQUIREMENTS_PATH"
if [ ! -f "$REQUIREMENTS_PATH" ]; then
    warning "Requirements file '$REQUIREMENTS_FILENAME' not found at '$REQUIREMENTS_PATH'."
    warning "Skipping dependency installation. The '$FUNCTION_NAME' command might fail."
else
    info "Found '$REQUIREMENTS_FILENAME'. Attempting to install dependencies..."
    # Prefer python3 for running pip
    PYTHON_EXE=""
    if command -v python3 &> /dev/null; then
        PYTHON_EXE="python3"
    elif command -v python &> /dev/null; then
        PYTHON_EXE="python"
    else
        error "Neither 'python3' nor 'python' command was found. Cannot install dependencies."
        exit 1
    fi

    # Check if pip is available via the found python executable
    if ! "$PYTHON_EXE" -m pip --version &> /dev/null; then
        error "Could not execute '$PYTHON_EXE -m pip'. Ensure pip is installed for your Python environment."
        exit 1
    fi

    info "Running: $PYTHON_EXE -m pip install -r \"$REQUIREMENTS_PATH\""
    "$PYTHON_EXE" -m pip install -r "$REQUIREMENTS_PATH"
    PIP_EXIT_CODE=$? # Capture pip exit code

    if [ $PIP_EXIT_CODE -ne 0 ]; then
        error "Failed to install Python dependencies from '$REQUIREMENTS_FILENAME'. Exit code: $PIP_EXIT_CODE"
        error "Please check pip output above. The '$FUNCTION_NAME' command might not work."
        # exit 1 # Decide if you want to stop installation
    else
        success "Python dependencies installed successfully."
    fi
}
# --- End Install Dependencies ---


# Define the shell function
FUNCTION_DEFINITION=$(cat <<EOF

# Function added by find-a-workinator installer ($INSTALL_DIR/install.sh)
# Usage: $FUNCTION_NAME [arguments_for_python_script]
function $FUNCTION_NAME() {
    local _script_to_run="$TARGET_SCRIPT_PATH" # Path embedded by installer
    local _python_exe
    if command -v python3 &> /dev/null; then _python_exe="python3";
    elif command -v python &> /dev/null; then _python_exe="python";
    else echo "Error: Python 3 not found." >&2; return 1; fi
    "\$_python_exe" "\$_script_to_run" "\$@"
}
EOF
)

# Determine Shell and Profile File
CURRENT_SHELL=$(basename "$SHELL")
PROFILE_FILE=""
if [ "$CURRENT_SHELL" = "bash" ]; then PROFILE_FILE="$HOME/.bashrc"; info "Detected Bash shell. Target profile: $PROFILE_FILE";
elif [ "$CURRENT_SHELL" = "zsh" ]; then PROFILE_FILE="$HOME/.zshrc"; info "Detected Zsh shell. Target profile: $PROFILE_FILE";
else warning "Unrecognized shell: $CURRENT_SHELL. Using ~/.profile."; PROFILE_FILE="$HOME/.profile"; fi

# Ensure profile file exists
touch "$PROFILE_FILE"
if [ $? -ne 0 ]; then error "Failed to create profile file '$PROFILE_FILE'."; exit 1; fi
info "Ensured profile file exists: $PROFILE_FILE"

# Add function to profile if it doesn't exist already
if grep -q -E "^function\s+$FUNCTION_NAME\s*\(\s*\)\s*\{" "$PROFILE_FILE"; then
    warning "Function '$FUNCTION_NAME' seems to already exist in '$PROFILE_FILE'."
    warning "Dependencies were checked/installed, but the function was not added again."
else
    info "Adding '$FUNCTION_NAME' function to profile '$PROFILE_FILE'..."
    echo "" >> "$PROFILE_FILE" # Add newline for safety
    echo "$FUNCTION_DEFINITION" >> "$PROFILE_FILE"
    if [ $? -eq 0 ]; then
        success "'$FUNCTION_NAME' function added successfully."
        success "Please restart your terminal/shell or run 'source \"$PROFILE_FILE\"' to activate the command."
    else
        error "Failed to write to profile file '$PROFILE_FILE'."; exit 1
    fi
fi

info "Installation process complete."