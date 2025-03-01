#!/usr/bin/env bash

# Check if the device is connected
if ! mpremote ls > /dev/null 2>&1; then
  echo "Error: Device not connected or mpremote not working properly"
  exit 1
fi

# Parse command-line options
UPLOAD_BOOT=false
NUKE_BOARD=false
EXAMPLE_FILE=""
while getopts "bne:" opt; do
  case $opt in
    b) UPLOAD_BOOT=true ;;
    n) NUKE_BOARD=true ;;
    e) EXAMPLE_FILE="$OPTARG" ;;
    *) echo "Usage: $0 [-b] [-n] [-e example_file]"; exit 1 ;;
  esac
done

# Clean user and SSA directories
if [ "$NUKE_BOARD" = true ]; then
  mpremote run ./scripts/nuke.py
fi

# Create temporary directories
TEMP_DIR="./ssaHAL/.temp"
CONFIG_DIR="$TEMP_DIR/config"
SSA_DIR="$TEMP_DIR/ssa"
SSA_MODULES_DIR="$TEMP_DIR/modules"
mkdir -p "$CONFIG_DIR" || { echo "Error: Failed to create directory $CONFIG_DIR"; exit 1; }

# Process configuration files
jq -c < ./ssaHAL/config/config.json > "$CONFIG_DIR/config.json" || { echo "Error: Failed to process config.json"; exit 1; }
[ -f ./ssaHAL/config/secrets.json ] && jq -c < ./ssaHAL/config/secrets.json > "$CONFIG_DIR/secrets.json" || echo "Warning: secrets.json not found or processing failed"

python3 scripts/clean.py ./ssaHAL/ssa "$SSA_DIR" || { echo "Error: Failed to clean SSA directory"; exit 1; }
python3 scripts/clean.py ./ssaHAL/ssa_modules "$SSA_MODULES_DIR" || { echo "Error: Failed to clean SSA directory"; exit 1; }

# Compile SSA module to frozen bytecode
mkdir -p "$SSA_DIR/compiled/" || { echo "Error: Failed to create directory $SSA_DIR/compiled/"; exit 1; }
for file in $SSA_DIR/*.py; do
  mpy-cross "$file" -o "$SSA_DIR/compiled/$(basename "$file" .py).mpy"
done

# Compile SSA module to frozen bytecode
mkdir -p "$SSA_MODULES_DIR/compiled" || { echo "Error: Failed to create directory $SSA_MODULES_DIR/compiled"; exit 1; }
for file in $SSA_MODULES_DIR/*.py; do
  mpy-cross "$file" -o "$SSA_MODULES_DIR/compiled/$(basename "$file" .py).mpy"
done

# Upload required files
mpremote cp -r ./ssaHAL/lib/ :
mpremote cp -r $CONFIG_DIR/ :
mpremote mkdir :ssa
mpremote cp -r $SSA_DIR/compiled/* :./ssa/
mpremote cp -r $SSA_MODULES_DIR/compiled/* :./ssa_modules/

# Clean up
rm -rf $TEMP_DIR

# Conditionally upload boot.py
if [ "$UPLOAD_BOOT" = true ]; then
  mpremote cp ./ssaHAL/boot.py :
fi

# Conditionally upload example file
if [ -n "$EXAMPLE_FILE" ]; then
  if [ -f ./ssaHAL/examples/$EXAMPLE_FILE ]; then
    mpremote mkdir :user
    mpremote cp ./ssaHAL/examples/$EXAMPLE_FILE :user/app.py
  else
    echo "Error: Example file '$EXAMPLE_FILE' not found."
    exit 1
  fi
fi

