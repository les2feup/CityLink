#!/usr/bin/env bash
set -e
set -o pipefail

# Define colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
error() { echo -e "${RED}[ERROR]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
debug() { 
    if [[ "$DEBUG" == "true" ]] then
        echo -e "${YELLOW}[DEBUG]${NC} $1";
    fi
}

# Global variables for command-line options
UPLOAD_BOOT=false
NUKE_BOARD=false
EXAMPLE_FILE=""
SSA_IMPL_DIR=""
DEBUG=false

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
#   -s <directory>  Specify the SSA implementation directory.
#   -d              Enable debug output.
parse_options() {
    while getopts "bne:s:d" opt; do
        case $opt in
            b) UPLOAD_BOOT=true ;;
            n) NUKE_BOARD=true ;;
            e) EXAMPLE_FILE="$OPTARG" ;;
            s) SSA_IMPL_DIR="$OPTARG" ;;
            d) DEBUG=true ;;
            *) error "Usage: $0 [-b] [-n] [-e example_file] [-d] -s <ssa core implementation directory>"; exit 1 ;;
        esac
    done
    
    # Shift to remove processed options
    shift $((OPTIND-1))

    # Ensure that the ssa implementation directory was provided.
    if [ -z "$SSA_IMPL_DIR" ]; then
        error "SSA implementation directory must be specified with -s option."
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
    if [ ! -d "$SSA_IMPL_DIR/examples" ] && [ -n "$EXAMPLE_FILE" ]; then
        error "'$SSA_IMPL_DIR' does not contain an 'examples' directory, but an example file was requested."
        exit 1
    elif [ ! -d "$SSA_IMPL_DIR/examples" ]; then
        info "Warning: '$SSA_IMPL_DIR' does not contain an 'examples' directory. Example upload will be skipped if requested."
    fi
    info "Using SSA implementation directory: $SSA_IMPL_DIR"
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
    find ssa -type d -name "__pycache__" -exec rm -rf {} \; 2>/dev/null || true
    find "$SSA_IMPL_DIR/src" -type d -name "__pycache__" -exec rm -rf {} \; 2>/dev/null || true
    success "__pycache__ directories removed."
}

# Prepares temporary directories for cleaning and compilation.
prepare_temp_dirs() {
    info "Preparing temporary directories..."
    TEMP_DIR="./.temp"
    SSA_TEMP="$TEMP_DIR/ssa"
    IMPL_TEMP="$TEMP_DIR/ssa_impl"
    rm -rf "$TEMP_DIR" # Clean up any existing temp directory
    mkdir -p "$SSA_TEMP" "$IMPL_TEMP" || { error "Failed to create temporary directories"; exit 1; }
    success "Temporary directories created."
}

# Inspect directory contents (debug function)
inspect_directory() {
    if [[ "$DEBUG" == "true" ]]; then
        local dir="$1"
        debug "Inspecting directory: $dir"
        find "$dir" -type f | sort
    fi
}

# Cleans a directory by running the cleaning script.
# Arguments:
#   $1: source directory
#   $2: destination directory for cleaned output
clean_directory() {
    local src="$1"
    local dest="$2"
    info "Cleaning directory '$src'..."
    
    # Directly copy files instead of using the clean.py script
    # This ensures we don't miss any files
    if [[ "$DEBUG" == "true" ]]; then
        debug "Source directory contents ($src):"
        find "$src" -type f -name "*.py" | sort
    fi

    # First, copy all Python files
    rsync -a --include="*/" --include="*.py" --exclude="*" "$src/" "$dest/"
    
    # Check if we have files after cleaning
    local file_count=$(find "$dest" -type f -name "*.py" | wc -l)
    if [[ "$file_count" -eq 0 ]]; then
        error "No Python files found after cleaning directory $src. Something might be wrong."
        debug "Trying original clean script as fallback..."
        python3 scripts/clean.py "$src" "$dest" || { error "Failed to clean directory $src"; exit 1; }
        
        file_count=$(find "$dest" -type f -name "*.py" | wc -l)
        if [[ "$file_count" -eq 0 ]]; then
            error "Still no Python files found after cleaning with original script. Check your source directory and clean.py script."
            exit 1
        fi
    fi
    
    if [[ "$DEBUG" == "true" ]]; then
        debug "Destination directory contents after cleaning ($dest):"
        find "$dest" -type f -name "*.py" | sort
    fi
    
    success "Cleaned '$src' - copied $file_count Python files."
}

# Compiles Python files to frozen bytecode recursively in a cleaned directory.
compile_directory() {
    local src="$1"
    local compiled_dir="$src/compiled"
    info "Compiling Python files in '$src'..."
    mkdir -p "$compiled_dir" || { error "Failed to create directory $compiled_dir"; exit 1; }
    
    # Find all Python files in the source directory
    local python_files=$(find "$src" -type f -name "*.py" ! -path "$compiled_dir/*")
    if [ -z "$python_files" ]; then
        error "No Python files found in '$src'. Cannot compile."
        exit 1
    fi
    
    # Count for logging
    local file_count=0
    
    # Compile each file
    echo "$python_files" | while read -r file; do
        rel_path=$(realpath --relative-to="$src" "$file")
        out_file="$compiled_dir/${rel_path%.py}.mpy"
        out_dir=$(dirname "$out_file")
        mkdir -p "$out_dir" || { error "Failed to create directory for $out_file"; exit 1; }
        debug "Compiling $file to $out_file"
        mpy-cross "$file" -o "$out_file" || { error "Failed to compile $file"; exit 1; }
        file_count=$((file_count + 1))
    done
    
    # Verify compilation results
    local compiled_count=$(find "$compiled_dir" -type f -name "*.mpy" | wc -l)
    if [[ "$compiled_count" -eq 0 ]]; then
        error "No compiled files found in $compiled_dir. Compilation may have failed."
        exit 1
    fi
    
    if [[ "$DEBUG" == "true" ]]; then
        debug "Compiled directory contents ($compiled_dir):"
        find "$compiled_dir" -type f -name "*.mpy" | sort
    fi
    
    success "Compilation complete in '$src'. Created $compiled_count .mpy files."
}

# Cleans and compiles the internal ssa directory.
process_ssa() {
    info "Processing SSA directory..."
    clean_directory "ssa" "$SSA_TEMP"
    inspect_directory "$SSA_TEMP"
    compile_directory "$SSA_TEMP"
    inspect_directory "$SSA_TEMP/compiled"
}

# Cleans and compiles the ssa implementation source directory.
process_ssa_impl() {
    info "Processing SSA implementation directory..."
    clean_directory "$SSA_IMPL_DIR/src" "$IMPL_TEMP"
    inspect_directory "$IMPL_TEMP"
    compile_directory "$IMPL_TEMP"
    inspect_directory "$IMPL_TEMP/compiled"
}

# Uploads the compiled files from both ssa and ssa implementation to the device.
upload_files() {
    info "Uploading compiled files..."
    
    # Ensure directories exist on device
    mpremote mkdir :lib 2>/dev/null || info "Directory 'lib' may already exist on device."
    mpremote mkdir :lib/ssa 2>/dev/null || info "Directory 'lib/ssa' may already exist on device."
    mpremote mkdir :lib/ssa_core 2>/dev/null || info "Directory 'lib/ssa_core' may already exist on device."

    # Check what's on the device before uploading (debug)
    if [[ "$DEBUG" == "true" ]]; then
        debug "Device contents before upload:"
        mpremote ls :lib || true
        mpremote ls :lib/ssa || true
        mpremote ls :lib/ssa_core || true
    fi

    # Upload SSA files using manual copy for better reliability
    if [ -d "$SSA_TEMP/compiled" ]; then
        info "Uploading SSA compiled files..."
        mpremote cp -r "$SSA_TEMP/compiled/"* ":lib/ssa/" || {
            error "Both upload methods failed for SSA. Check device connection and file permissions."
            exit 1
        }

        info "Uploaded SSA to lib/ssa."
    else
        error "No compiled SSA directory found."
        exit 1
    fi

    # Upload SSA impl files using manual copy
    if [ -d "$IMPL_TEMP/compiled" ]; then
        info "Uploading SSA implementation compiled files..."
        mpremote cp -r "$IMPL_TEMP/compiled/"* ":lib/ssa_core/" || {
            error "Both upload methods failed for SSA implementation. Check device connection and file permissions."
            exit 1
        }
        info "Uploaded SSA implementation to lib/ssa_core."
    else
        error "No compiled SSA implementation directory found."
        exit 1
    fi

    if [ -d "$SSA_IMPL_DIR/lib" ]; then
        info "Uploading additional libraries from $SSA_IMPL_DIR/lib..."
        mpremote cp -r "$SSA_IMPL_DIR/lib/"* ":lib/" || {
            error "Failed to upload additional libraries from $SSA_IMPL_DIR/lib."
            exit 1
        }
        info "Uploaded additional libraries."
    fi

    # Check what's on the device after uploading (debug)
    if [[ "$DEBUG" == "true" ]]; then
        debug "Device contents after upload:"
        mpremote ls :lib || true
        mpremote ls :lib/ssa || true
        mpremote ls :lib/ssa_core || true
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
    if [[ "$DEBUG" != "true" ]]; then
        rm -rf "$TEMP_DIR" || { error "Failed to remove temporary directory"; exit 1; }
        success "Cleanup complete."
    else
        info "Debug mode: Keeping temporary files in $TEMP_DIR for inspection."
    fi
}

# Display usage information
show_usage() {
    echo "Usage: $0 [-b] [-n] [-e example_file] [-d] -s <ssa core implementation directory>"
    echo
    echo "Options:"
    echo "  -b              Upload boot.py to device"
    echo "  -n              Nuke (clean) the board before flashing new firmware"
    echo "  -e <filename>   Specify an example file to upload as main.py"
    echo "  -s <directory>  Specify the SSA implementation directory (required)"
    echo "  -d              Enable debug output"
    echo
    echo "Example:"
    echo "  $0 -b -n -e hello_world.py -s ./my_ssa_impl"
}

# Main execution flow.
main() {
    # Show usage if no arguments provided
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi
    
    check_project_root
    check_device
    parse_options "$@"
    nuke_board
    remove_pycache
    prepare_temp_dirs
    process_ssa
    process_ssa_impl
    upload_files
    upload_boot
    upload_example
    cleanup
    success "All tasks completed successfully."
}

main "$@"
