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

# Phase 1: Ensure script is running from the project root
check_project_root() {
  if [[ ! -d "ssaHAL" || ! -d "scripts" || ! -f "ssaHAL/config/config.json" ]]; then
    error "This script must be run from the project root directory."
    error "Expected to find 'ssaHAL/' directory and 'scripts/' directory."
    exit 1
  fi
  success "Running from the correct project directory."
}

# Phase 2: Check device connection
check_device() {
  info "Checking if device is connected..."
  if ! mpremote ls > /dev/null 2>&1; then
    error "Device not connected or mpremote not working properly."
    exit 1
  fi
  success "Device connected."
}

# Phase 3: Parse command-line options and source directories
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

# Phase 5: Prepare temporary directories
prepare_temp_dirs() {
  info "Preparing temporary directories..."
  # Use a generic temporary directory at the root.
  TEMP_DIR="./.temp"
  CONFIG_DIR="$TEMP_DIR/config"
  mkdir -p "$CONFIG_DIR" || { error "Failed to create directory $CONFIG_DIR"; exit 1; }
  success "Temporary directories created."
}

# Phase 6: Remove __pycache__ directories from each source directory
remove_pycache() {
  info "Removing '__pycache__' directories from source directories..."
  for src in "${SOURCE_DIRS[@]}"; do
    find "$src" -type d -name "__pycache__" -exec rm -rf {} + || { error "Failed to remove __pycache__ directories in $src"; exit 1; }
  done
  success "__pycache__ directories removed."
}

# Phase 7: Process configuration files (remains unchanged)
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
# to a temporary destination whose name is based on the source’s basename.
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

# Phase 9: Recursively compile source modules in each cleaned directory
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

# Phase 10: Upload compiled files to the device for each cleaned directory.
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

# Phase 13: Optionally upload an example file
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

# Main execution function: process options, then act on the passed source directories.
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

