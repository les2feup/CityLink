#!/usr/bin/env bash
set -e
set -o pipefail

# Define colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
error() { echo -e "${RED}[ERROR]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
info() { echo -e "${YELLOW}[INFO]${NC} $1"; }

# Global variables for command-line options
UPLOAD_BOOT=false
NUKE_BOARD=false
EXAMPLE_FILE=""
SSA_IMPL_DIR=""

# Global temporary directories
TEMP_DIR=""
SSA_TEMP=""
IMPL_TEMP=""

# Checks that the script is run from the project root by verifying required directories exist.
# Expects a folder "ssa" (the internal library) and the presence of boot.py.
check_project_root() {
    if [[ ! -d "ssa" ]]; then
        error "Project root must contain the 'ssa' directory."
        exit 1
    fi
    if [[ ! -f "boot.py" ]]; then
        error "boot.py not found in the project root."
        exit 1
    fi
    success "Project root check passed."
}

# Checks whether a device is connected via mpremote.
check_device() {
    info "Checking if device is connected..."
    if ! mpremote ls > /dev/null 2>&1; then
        error "Device not connected or mpremote not working properly."
        exit 1
    fi
    success "Device connected."
}

# Parses command-line options.
#
# Options:
#   -b              Optionally upload boot.py to device.
#   -n              Nuke (clean) the board before flashing new firmware.
#   -e <filename>   Specify an example file (located in <ssa implementation>/examples) to upload as main.py.
#   -s <directory>  Specify the ssa implementation directory (must contain "src/" and optionally "examples/").
parse_options() {
    while getopts "bn:e:s:" opt; do
        case $opt in
            b) UPLOAD_BOOT=true ;;
            n) NUKE_BOARD=true ;;
            e) EXAMPLE_FILE="$OPTARG" ;;
            s) SSA_IMPL_DIR="$OPTARG" ;;
            *) error "Usage: $0 [-b] [-n] [-e example_file] -s ssa_implementation_directory"; exit 1 ;;
        esac
    done

    # Ensure that the ssa implementation directory was provided.
    if [ -z "$SSA_IMPL_DIR" ]; then
        error "ssa implementation directory must be specified with -s option."
        exit 1
    fi

    if [ ! -d "$SSA_IMPL_DIR" ]; then
        error "Directory '$SSA_IMPL_DIR' does not exist."
        exit 1
    fi
    if [ ! -d "$SSA_IMPL_DIR/src" ]; then
        error "'$SSA_IMPL_DIR' must contain a 'src' directory."
        exit 1
    fi
    if [ ! -d "$SSA_IMPL_DIR/examples" ]; then
        info "Warning: '$SSA_IMPL_DIR' does not contain an 'examples' directory. Example upload will be skipped if requested."
    fi
    info "Using ssa implementation directory: $SSA_IMPL_DIR"
}

# Nuke board if the -n flag is provided.
nuke_board() {
    if [ "$NUKE_BOARD" = true ]; then
        info "Cleaning board (nuke)..."
        mpremote run ./scripts/nuke.py || { error "Failed to nuke board."; exit 1; }
        success "Board nuked successfully."
    fi
}

# Removes all __pycache__ directories from the given directories.
remove_pycache() {
    info "Removing __pycache__ directories from 'ssa' and '$SSA_IMPL_DIR/src'..."
    find ssa -type d -name "__pycache__" -exec rm -rf {} + || { error "Failed to remove __pycache__ in ssa"; exit 1; }
    find "$SSA_IMPL_DIR/src" -type d -name "__pycache__" -exec rm -rf {} + || { error "Failed to remove __pycache__ in $SSA_IMPL_DIR/src"; exit 1; }
    success "__pycache__ directories removed."
}

# Prepares temporary directories for cleaning and compilation.
prepare_temp_dirs() {
    info "Preparing temporary directories..."
    TEMP_DIR="./.temp"
    SSA_TEMP="$TEMP_DIR/ssa"
    IMPL_TEMP="$TEMP_DIR/ssa_impl"
    mkdir -p "$SSA_TEMP" "$IMPL_TEMP" || { error "Failed to create temporary directories"; exit 1; }
    success "Temporary directories created."
}

# Cleans a directory by running the cleaning script.
# Arguments:
#   $1: source directory
#   $2: destination directory for cleaned output
clean_directory() {
    local src="$1"
    local dest="$2"
    info "Cleaning directory '$src'..."
    python3 scripts/clean.py "$src" "$dest" || { error "Failed to clean directory $src"; exit 1; }
    success "Cleaned '$src'."
}

# Compiles Python files to frozen bytecode recursively in a cleaned directory.
compile_directory() {
    local src="$1"
    local compiled_dir="$src/compiled"
    info "Compiling Python files in '$src'..."
    mkdir -p "$compiled_dir" || { error "Failed to create directory $compiled_dir"; exit 1; }
    find "$src" -type f -name "*.py" ! -path "$compiled_dir/*" | while read -r file; do
        rel_path=$(realpath --relative-to="$src" "$file")
        out_file="$compiled_dir/${rel_path%.py}.mpy"
        mkdir -p "$(dirname "$out_file")" || { error "Failed to create directory for $out_file"; exit 1; }
        mpy-cross "$file" -o "$out_file" || { error "Failed to compile $file"; exit 1; }
    done
    success "Compilation complete in '$src'."
}

# Cleans and compiles the internal ssa directory.
process_ssa() {
    clean_directory "ssa" "$SSA_TEMP"
    compile_directory "$SSA_TEMP"
}

# Cleans and compiles the ssa implementation source directory.
process_ssa_impl() {
    clean_directory "$SSA_IMPL_DIR/src" "$IMPL_TEMP"
    compile_directory "$IMPL_TEMP"
}

# Uploads the compiled files from both ssa and ssa implementation to the device.
upload_files() {
    info "Uploading compiled files..."
    mpremote mkdir :lib || info "Directory 'lib' may already exist on device."
    mpremote mkdir :lib/ssa || info "Directory 'lib/ssa' may already exist on device."
    mpremote mkdir :lib/ssa_core || info "Directory 'lib/ssa_core' may already exist on device."

    if [ -d "$SSA_TEMP/compiled" ]; then
        mpremote cp -r "$SSA_TEMP/compiled/"* ":lib/ssa/" || { error "Failed to upload ssa compiled files"; exit 1; }
        info "Uploaded ssa to lib/ssa."
    else
        info "No compiled ssa files found."
    fi

    if [ -d "$IMPL_TEMP/compiled" ]; then
        mpremote cp -r "$IMPL_TEMP/compiled/"* ":lib/ssa_core/" || { error "Failed to upload ssa implementation compiled files"; exit 1; }
        info "Uploaded ssa implementation to lib/ssa_core."
    else
        info "No compiled ssa implementation files found."
    fi

    success "Files uploaded successfully."
}

# Optionally uploads boot.py to the device's root.
upload_boot() {
    if [ "$UPLOAD_BOOT" = true ]; then
        info "Uploading boot.py to device root..."
        mpremote cp boot.py : || { error "Failed to upload boot.py"; exit 1; }
        success "boot.py uploaded successfully."
    fi
}

# Optionally uploads an example file from the ssa implementation's examples folder as main.py.
upload_example() {
    if [ -n "$EXAMPLE_FILE" ]; then
        local example_path="$SSA_IMPL_DIR/examples/$EXAMPLE_FILE"
        if [ -f "$example_path" ]; then
            info "Uploading example file '$EXAMPLE_FILE' as main.py..."
            mpremote cp "$example_path" :main.py || { error "Failed to upload example file"; exit 1; }
            success "Example file uploaded successfully."
        else
            error "Example file '$EXAMPLE_FILE' not found in $SSA_IMPL_DIR/examples."
            exit 1
        fi
    fi
}

# Removes temporary directories.
cleanup() {
    info "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR" || { error "Failed to remove temporary directory"; exit 1; }
    success "Cleanup complete."
}

# Main execution flow.
main() {
    check_project_root
    check_device
    parse_options "$@"
    nuke_board
    remove_pycache
    prepare_temp_dirs
    process_ssa
    process_ssa_impl
    upload_files
    cleanup
    upload_boot
    upload_example
    success "All tasks completed successfully."
}

main "$@"

