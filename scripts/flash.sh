#!/usr/bin/env bash
set -e
set -o pipefail

# Define colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions for logging
error() { echo -e "${RED}[ERROR]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
info() { echo -e "${YELLOW}[INFO]${NC} $1"; }

# Global variables for command-line options
UPLOAD_BOOT=false
NUKE_BOARD=false
EXAMPLE_FILE=""

# Global temporary directories (will be set in prepare_temp_dirs)
TEMP_DIR=""
CONFIG_DIR=""

# Global arrays for source directories and their cleaned counterparts.
declare -a SOURCE_DIRS
declare -a CLEANED_DIRS

# Checks whether the script is executed from the correct project root.
#
# This function verifies that the current directory contains the expected project structure by ensuring the
# presence of the 'ssaHAL' and 'scripts' directories and the 'ssaHAL/config/config.json' configuration file.
# If any of these are missing, it logs error messages and exits the script.
#
# Globals:
#   error    - Function used to log error messages.
#   success  - Function used to log a success message when the check passes.
#
# Outputs:
#   Logs an error message to STDERR if the required directories or configuration file are not found.
#   Logs a success message to STDOUT if the project root is confirmed.
#
# Returns:
#   Exits the script with a non-zero status code if the check fails.
#
# Example:
#   check_project_root
#   # If the current directory is the project root, a success message is logged.
#   # Otherwise, error messages are logged and the script exits.
check_project_root() {
  if [[ ! -d "ssaHAL" || ! -d "scripts" || ! -f "ssaHAL/config/config.json" ]]; then
    error "This script must be run from the project root directory."
    error "Expected to find 'ssaHAL/' directory and 'scripts/' directory."
    exit 1
  fi
  success "Running from the correct project directory."
}

# Checks whether a device is connected by invoking 'mpremote ls'.
#
# This function logs an informational message to indicate that a device check is being performed.
# It then calls 'mpremote ls' to determine if a device is available. If the command fails,
# the function logs an error message and exits the script with a status code of 1. If the device is
# successfully detected, it logs a success message.
#
# Globals:
#   Utilizes global logging functions: info, error, success.
#
# Arguments:
#   None.
#
# Outputs:
#   Logs messages to STDOUT and STDERR.
#
# Returns:
#   Exits the script with a status code of 1 if the device is not connected.
#
# Example:
#   check_device
check_device() {
  info "Checking if device is connected..."
  if ! mpremote ls > /dev/null 2>&1; then
    error "Device not connected or mpremote not working properly."
    exit 1
  fi
  success "Device connected."
}

# Parses command-line options and sets up source directories.
#
# Globals:
#   UPLOAD_BOOT  - Set to true if the -b flag is provided (enables boot file upload).
#   NUKE_BOARD   - Set to true if the -n flag is provided (enables board nuking).
#   EXAMPLE_FILE - Contains the filename specified by the -e option, if provided.
#   SOURCE_DIRS  - Array to hold the source directories passed as positional arguments.
#
# Arguments:
#   Options:
#     -b              Enable uploading of boot.py.
#     -n              Enable nuking of the board.
#     -e <filename>   Specify an example file to be used.
#   Positional:
#     One or more source directories containing Python files.
#
# Outputs:
#   Logs informational messages detailing the parsed options and source directories.
#   Logs error messages and exits if no source directories are provided or upon invalid usage.
#
# Returns:
#   Exits with status 1 if an error occurs; otherwise, sets necessary global variables.
#
# Example:
#   ./flash.sh -b -n -e example.py src_dir1 src_dir2
parse_options() {
  while getopts "bne:" opt; do
    case $opt in
      b) UPLOAD_BOOT=true ;;
      n) NUKE_BOARD=true ;;
      e) EXAMPLE_FILE="$OPTARG" ;;
      *) error "Usage: $0 [-b] [-n] [-e example_file] source_dir1 [source_dir2 ...]"; exit 1 ;;
    esac
  done
  shift $((OPTIND - 1))
  if [ "$#" -lt 1 ]; then
    error "No source directories provided."
    error "Usage: $0 [-b] [-n] [-e example_file] source_dir1 [source_dir2 ...]"
    exit 1
  fi
  # The remaining arguments are our source directories.
  SOURCE_DIRS=("$@")
  info "Options parsed: UPLOAD_BOOT=$UPLOAD_BOOT, NUKE_BOARD=$NUKE_BOARD, EXAMPLE_FILE='$EXAMPLE_FILE'"
  info "Source directories: ${SOURCE_DIRS[*]}"
}

# Phase 4: Nuke board if requested
nuke_board() {
  if [ "$NUKE_BOARD" = true ]; then
    info "Cleaning board (nuke)..."
    mpremote run ./scripts/nuke.py || { error "Failed to nuke board."; exit 1; }
    success "Board nuked successfully."
  fi
}

# Prepares temporary directories for configuration files.
#
# This function sets up a generic temporary directory (./.temp) and a subdirectory for configuration files.
# It logs informational messages during the process. If the creation of the configuration directory fails,
# it logs an error and exits the script.
#
# Globals:
#   TEMP_DIR: The root temporary directory, set to "./.temp".
#   CONFIG_DIR: The directory for configuration files, set to "$TEMP_DIR/config".
#
# Outputs:
#   Logs progress and error messages to STDOUT.
#
# Example:
#   prepare_temp_dirs
prepare_temp_dirs() {
  info "Preparing temporary directories..."
  # Use a generic temporary directory at the root.
  TEMP_DIR="./.temp"
  CONFIG_DIR="$TEMP_DIR/config"
  mkdir -p "$CONFIG_DIR" || { error "Failed to create directory $CONFIG_DIR"; exit 1; }
  success "Temporary directories created."
}

# Removes all __pycache__ directories recursively from each directory in the SOURCE_DIRS array.
#
# Globals:
#   SOURCE_DIRS - An array containing the paths of source directories to clean.
#
# Outputs:
#   Logs informational messages to STDOUT and error messages to STDERR.
#
# Returns:
#   Exits with status 1 if removal of any __pycache__ directory fails.
#
# Example:
#   remove_pycache
remove_pycache() {
  info "Removing '__pycache__' directories from source directories..."
  for src in "${SOURCE_DIRS[@]}"; do
    find "$src" -type d -name "__pycache__" -exec rm -rf {} + || { error "Failed to remove __pycache__ directories in $src"; exit 1; }
  done
  success "__pycache__ directories removed."
}

# Processes JSON configuration files and saves the processed output into the temporary configuration directory.
#
# Globals:
#   CONFIG_DIR - Directory where the processed configuration files (config.json and secrets.json) are stored.
#
# Outputs:
#   Writes a minified version of './ssaHAL/config/config.json' to "$CONFIG_DIR/config.json".
#   If './ssaHAL/config/secrets.json' exists, attempts to write its minified version to "$CONFIG_DIR/secrets.json" and logs a warning if processing fails.
#
# Returns:
#   Exits the script if processing of 'config.json' fails.
#
# Example:
#   process_configs
process_configs() {
  info "Processing configuration files..."
  jq -c < ./ssaHAL/config/config.json > "$CONFIG_DIR/config.json" || { error "Failed to process config.json"; exit 1; }
  if [ -f ./ssaHAL/config/secrets.json ]; then
    jq -c < ./ssaHAL/config/secrets.json > "$CONFIG_DIR/secrets.json" || info "Warning: secrets.json processing failed"
  else
    info "Warning: secrets.json not found"
  fi
  success "Configuration files processed."
}

# Phase 8: Clean source directories
# For each provided source directory, run the cleaning script and copy its cleaned content
# Cleans each source directory in SOURCE_DIRS by running a Python cleaning script and storing the cleaned output
# in a temporary directory based on the source's basename.
#
# Globals:
#   TEMP_DIR       - Temporary directory used to store cleaned directories.
#   SOURCE_DIRS    - Array of source directory paths to be cleaned.
#   CLEANED_DIRS   - Array that will be populated with the paths to the cleaned directories.
#
# Outputs:
#   Logs informational, success, and error messages.
#
# Returns:
#   None. Exits with an error code if the cleaning script fails for any source directory.
#
# Example:
#   clean_source_directories
clean_source_directories() {
  info "Cleaning source directories..."
  CLEANED_DIRS=()
  for src in "${SOURCE_DIRS[@]}"; do
    dest="$TEMP_DIR/$(basename "$src")"
    python3 scripts/clean.py "$src" "$dest" || { error "Failed to clean directory $src"; exit 1; }
    CLEANED_DIRS+=("$dest")
  done
  success "Source directories cleaned."
}

# Recursively compiles Python source files in each cleaned directory to frozen bytecode.
#
# Globals:
#   CLEANED_DIRS - An array of directories containing cleaned Python source files.
#
# Outputs:
#   Logs progress and error messages via the 'info', 'error', and 'success' functions.
#
# Returns:
#   Exits with a non-zero status if directory creation or file compilation fails.
#
# Example:
#   compile_modules
compile_modules() {
  info "Compiling module files to frozen bytecode recursively..."
  for src in "${CLEANED_DIRS[@]}"; do
    info "Compiling .py files in directory '$src' recursively..."
    compiled_dir="$src/compiled"
    mkdir -p "$compiled_dir" || { error "Failed to create directory $compiled_dir"; exit 1; }
    # Find all .py files recursively, but skip files already in the compiled subdirectory.
    find "$src" -type f -name "*.py" ! -path "$compiled_dir/*" | while read -r file; do
      rel_path=$(realpath --relative-to="$src" "$file")
      out_file="$compiled_dir/${rel_path%.py}.mpy"
      mkdir -p "$(dirname "$out_file")" || { error "Failed to create directory for $out_file"; exit 1; }
      mpy-cross "$file" -o "$out_file" || { error "Failed to compile $file"; exit 1; }
    done
  done
  success "Compilation complete."
}

# Uploads library files, configuration files, and compiled Python modules to the connected device.
#
# This function uses mpremote to transfer required files to the device:
#   1. It copies library files from the local "ssaHAL/lib" directory.
#   2. It copies configuration files from the directory specified by CONFIG_DIR.
#   3. For each directory in the CLEANED_DIRS array, it creates a corresponding directory on the device (using the local directory's basename) and, if present, uploads compiled files from a "compiled" subdirectory.
#
# Globals:
#   CONFIG_DIR   - Path to the directory containing configuration files.
#   CLEANED_DIRS - Array of directories with cleaned source files.
#
# Outputs:
#   Informational and error messages are printed to STDOUT/STDERR.
#   Exits with an error code (1) if any file transfer operation fails.
#
# Example:
#   upload_files
upload_files() {
  info "Uploading required files..."
  mpremote cp -r ./ssaHAL/lib/ : || { error "Failed to copy lib files"; exit 1; }
  mpremote cp -r "$CONFIG_DIR"/ : || { error "Failed to copy configuration files"; exit 1; }
  
  for dir in "${CLEANED_DIRS[@]}"; do
    dest_dir=$(basename "$dir")
    mpremote mkdir ":$dest_dir" || info "Directory '$dest_dir' may already exist on device."
    if [ -d "$dir/compiled" ]; then
      mpremote cp -r "$dir/compiled/"* ":./$dest_dir/" || { error "Failed to copy compiled files from $dir"; exit 1; }
    else
      info "No compiled files found in $dir"
    fi
  done
  success "Files uploaded successfully."
}

# Phase 11: Clean up temporary directories
cleanup() {
  info "Cleaning up temporary files..."
  rm -rf "$TEMP_DIR" || { error "Failed to remove temporary directory"; exit 1; }
  success "Cleanup complete."
}

# Phase 12: Optionally upload boot.py
upload_boot() {
  if [ "$UPLOAD_BOOT" = true ]; then
    info "Uploading boot.py..."
    mpremote cp ./ssaHAL/boot.py : || { error "Failed to upload boot.py"; exit 1; }
    success "boot.py uploaded successfully."
  fi
}

# Uploads the example file to the device as "user/app.py" if an example has been specified.
#
# Globals:
#   EXAMPLE_FILE - If non-empty, represents the name of the example file expected in "./ssaHAL/examples/". The function verifies its existence before uploading.
#
# Outputs:
#   Logs informational, error, and success messages during its execution. In case of failure (missing file or upload issue), an error is logged and the script exits with status 1.
#
# Example:
#   EXAMPLE_FILE="example.py"
#   upload_example
upload_example() {
  if [ -n "$EXAMPLE_FILE" ]; then
    if [ -f "./ssaHAL/examples/$EXAMPLE_FILE" ]; then
      info "Uploading example file '$EXAMPLE_FILE' as user/app.py..."
      mpremote mkdir :user || info "Directory 'user' may already exist on device."
      mpremote cp ./ssaHAL/examples/"$EXAMPLE_FILE" :user/app.py || { error "Failed to upload example file"; exit 1; }
      success "Example file uploaded successfully."
    else
      error "Example file '$EXAMPLE_FILE' not found."
      exit 1
    fi
  fi
}

# Main execution function that orchestrates the flashing process.
#
# This function serves as the entry point of the script. It verifies the execution environment,
# processes command-line options, and sequentially calls helper functions to prepare, clean,
# compile, and upload Python files to the connected device. A success message is logged upon
# successful completion of all tasks.
#
# Globals:
#   SOURCE_DIRS   - Array of source directories provided as command-line arguments.
#   CLEANED_DIRS  - Array containing paths to cleaned source directories.
#   UPLOAD_BOOT, NUKE_BOARD, EXAMPLE_FILE - Flags controlling optional upload and board operations.
#   TEMP_DIR, CONFIG_DIR - Directories used for temporary storage during processing.
#
# Arguments:
#   "$@" - Command-line arguments, including source directories and optional flags.
#
# Outputs:
#   Logs messages to STDOUT and STDERR.
#
# Returns:
#   None. Exits the script on any critical failure.
#
# Example:
#   ./flash.sh src_dir1 src_dir2 --upload-boot --nuke-board
main() {
  check_project_root
  check_device
  parse_options "$@"
  nuke_board
  prepare_temp_dirs
  remove_pycache
  process_configs
  clean_source_directories
  compile_modules
  upload_files
  cleanup
  upload_boot
  upload_example
  success "All tasks completed successfully."
}

main "$@"

