#!/usr/bin/env bash
set -e
set -o pipefail

# Define colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions for logging
error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

info() {
  echo -e "${YELLOW}[INFO]${NC} $1"
}

# Global variables for command-line options
UPLOAD_BOOT=false
NUKE_BOARD=false
EXAMPLE_FILE=""

# Global temporary directories (will be set in prepare_temp_dirs)
TEMP_DIR=""
CONFIG_DIR=""
SSA_DIR=""
SSA_MODULES_DIR=""

# Phase 1: Check device connection
check_device() {
  info "Checking if device is connected..."
  if ! mpremote ls > /dev/null 2>&1; then
    error "Device not connected or mpremote not working properly."
    exit 1
  fi
  success "Device connected."
}

# Phase 2: Parse command-line options
parse_options() {
  while getopts "bne:" opt; do
    case $opt in
      b) UPLOAD_BOOT=true ;;
      n) NUKE_BOARD=true ;;
      e) EXAMPLE_FILE="$OPTARG" ;;
      *) error "Usage: $0 [-b] [-n] [-e example_file]"; exit 1 ;;
    esac
  done
  info "Options parsed: UPLOAD_BOOT=$UPLOAD_BOOT, NUKE_BOARD=$NUKE_BOARD, EXAMPLE_FILE='$EXAMPLE_FILE'"
}

# Phase 3: Nuke board if requested
nuke_board() {
  if [ "$NUKE_BOARD" = true ]; then
    info "Cleaning board (nuke)..."
    mpremote run ./scripts/nuke.py || { error "Failed to nuke board."; exit 1; }
    success "Board nuked successfully."
  fi
}

# Phase 4: Prepare temporary directories
prepare_temp_dirs() {
  info "Preparing temporary directories..."
  TEMP_DIR="./ssaHAL/.temp"
  CONFIG_DIR="$TEMP_DIR/config"
  SSA_DIR="$TEMP_DIR/ssa"
  SSA_MODULES_DIR="$TEMP_DIR/modules"
  mkdir -p "$CONFIG_DIR" || { error "Failed to create directory $CONFIG_DIR"; exit 1; }
  success "Temporary directories created."
}

# Phase 5: Process configuration files
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

# Phase 6: Clean SSA directories
clean_ssa_directories() {
  info "Cleaning SSA directories..."
  python3 scripts/clean.py ./ssaHAL/ssa "$SSA_DIR" || { error "Failed to clean SSA directory"; exit 1; }
  python3 scripts/clean.py ./ssaHAL/ssa_modules "$SSA_MODULES_DIR" || { error "Failed to clean SSA modules directory"; exit 1; }
  success "SSA directories cleaned."
}

# Phase 7: Compile SSA modules to frozen bytecode
compile_modules() {
  info "Compiling SSA module files to frozen bytecode..."

  mkdir -p "$SSA_DIR/compiled/" || { error "Failed to create directory $SSA_DIR/compiled/"; exit 1; }
  for file in "$SSA_DIR"/*.py; do
    [ -e "$file" ] || continue
    mpy-cross "$file" -o "$SSA_DIR/compiled/$(basename "$file" .py).mpy" || { error "Failed to compile $file"; exit 1; }
  done

  mkdir -p "$SSA_MODULES_DIR/compiled" || { error "Failed to create directory $SSA_MODULES_DIR/compiled"; exit 1; }
  for file in "$SSA_MODULES_DIR"/*.py; do
    [ -e "$file" ] || continue
    mpy-cross "$file" -o "$SSA_MODULES_DIR/compiled/$(basename "$file" .py).mpy" || { error "Failed to compile $file"; exit 1; }
  done
  success "Compilation complete."
}

# Phase 8: Upload required files to the device
upload_files() {
  info "Uploading required files..."
  mpremote cp -r ./ssaHAL/lib/ : || { error "Failed to copy lib files"; exit 1; }
  mpremote cp -r "$CONFIG_DIR"/ : || { error "Failed to copy configuration files"; exit 1; }
  
  # Create remote directories and tolerate errors if they already exist
  mpremote mkdir :ssa || info "Directory 'ssa' may already exist on device."
  mpremote cp -r "$SSA_DIR/compiled/"* :./ssa/ || { error "Failed to copy SSA compiled files"; exit 1; }
  mpremote mkdir :ssa_modules || info "Directory 'ssa_modules' may already exist on device."
  mpremote cp -r "$SSA_MODULES_DIR/compiled/"* :./ssa_modules/ || { error "Failed to copy SSA modules compiled files"; exit 1; }
  success "Files uploaded successfully."
}

# Phase 9: Clean up temporary directories
cleanup() {
  info "Cleaning up temporary files..."
  rm -rf "$TEMP_DIR" || { error "Failed to remove temporary directory"; exit 1; }
  success "Cleanup complete."
}

# Phase 10: Optionally upload boot.py
upload_boot() {
  if [ "$UPLOAD_BOOT" = true ]; then
    info "Uploading boot.py..."
    mpremote cp ./ssaHAL/boot.py : || { error "Failed to upload boot.py"; exit 1; }
    success "boot.py uploaded successfully."
  fi
}

# Phase 11: Optionally upload an example file
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

# Main execution function
main() {
  check_device
  parse_options "$@"
  nuke_board
  prepare_temp_dirs
  process_configs
  clean_ssa_directories
  compile_modules
  upload_files
  cleanup
  upload_boot
  upload_example
  success "All tasks completed successfully."
}

main "$@"

