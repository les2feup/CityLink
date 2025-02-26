#!/usr/bin/env bash

# Parse command-line options
UPLOAD_BOOT=false
NUKE_BOARD=false
EXAMPLE_FILE=""
while getopts "bne:" opt; do
  case $opt in
    b) UPLOAD_BOOT=true ;;
    n) NUKE_BOARD=true ;;
    e) EXAMPLE_FILE="$OPTARG" ;;
    *) echo "Usage: $0 [-b] [-e example_file]"; exit 1 ;;
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
mkdir -p "$CONFIG_DIR"

# Process configuration files
jq -c < ./ssaHAL/config/config.json > "$CONFIG_DIR/config.json"
jq -c < ./ssaHAL/config/secrets.json > "$CONFIG_DIR/secrets.json"

python3 scripts/clean.py ./ssaHAL/ssa "$SSA_DIR"

# Upload required files
mpremote cp -r ./ssaHAL/lib/ :
mpremote cp -r "$CONFIG_DIR/" :
mpremote cp -r "$SSA_DIR/" :

# Clean up
rm -rf "$TEMP_DIR"

# Conditionally upload boot.py
if [ "$UPLOAD_BOOT" = true ]; then
  mpremote cp ./ssaHAL/boot.py :
fi

# Conditionally upload example file
if [ -n "$EXAMPLE_FILE" ]; then
  if [ -f ./ssaHAL/examples/$EXAMPLE_FILE ]; then
    mpremote mkdir :user
    premote cp ./ssaHAL/examples/$EXAMPLE_FILE :user/app.py
  else
    echo "Error: Example file '$EXAMPLE_FILE' not found."
    exit 1
  fi
fi
