#!/bin/bash

# Define paths relative to the script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
KEYMAP_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
CONFIG_DIR="$KEYMAP_DIR/config"
TOOLS_DIR="$SCRIPT_DIR"
OUT_DIR="$TOOLS_DIR/out"
KEYMAP_DRAWER_DIR="$KEYMAP_DIR/keymap-drawer"

# Final SVG in root directory
SVG_OUTPUT="$KEYMAP_DIR/keymap.svg"

echo "Working with paths:"
echo "- Root directory: $KEYMAP_DIR"
echo "- Config directory: $CONFIG_DIR"
echo "- Tools directory: $TOOLS_DIR"
echo "- Output directory: $OUT_DIR"
echo "- Keymap drawer directory: $KEYMAP_DRAWER_DIR"
echo "- SVG output: $SVG_OUTPUT"

# Ensure output directory exists
mkdir -p "$OUT_DIR"

# Step 1: Process the keymap
echo -e "\nProcessing keymap..."
python3 "$TOOLS_DIR/process_keymap.py" "$CONFIG_DIR/base.keymap" "$OUT_DIR/processed_keymap.keymap"

# Step 2: Generate YAML configuration
echo -e "\nGenerating YAML configuration..."
cd "$KEYMAP_DRAWER_DIR"
python -m keymap_drawer parse -z "$OUT_DIR/processed_keymap.keymap" -o "$OUT_DIR/keymap.yaml"

# Update YAML to specify the correct layout (sofle)
echo -e "\nUpdating YAML layout..."
if [ -f "$OUT_DIR/keymap.yaml" ]; then
    # Create a temporary file for the update
    TMP_FILE=$(mktemp)
    # Update the layout line and save to temp file
    sed 's/zmk_keyboard: processed_keymap/zmk_keyboard: sofle/g' "$OUT_DIR/keymap.yaml" > "$TMP_FILE"
    # Move the temp file back to the original location
    mv "$TMP_FILE" "$OUT_DIR/keymap.yaml"
    echo "Updated YAML layout to 'sofle'"
else
    echo "ERROR: YAML file not found at $OUT_DIR/keymap.yaml"
    echo "Parsing may have failed. Check for errors above."
    exit 1
fi

# Manually copy a working example keymap.yaml if available
if [ ! -s "$OUT_DIR/keymap.yaml" ]; then
    echo "WARNING: YAML file is empty. Attempting to use a working example."
    if [ -f "$KEYMAP_DIR/keymap.yaml" ]; then
        cp "$KEYMAP_DIR/keymap.yaml" "$OUT_DIR/keymap.yaml"
        echo "Copied existing keymap.yaml to $OUT_DIR/keymap.yaml"
    else
        echo "ERROR: No example YAML file found. Cannot continue."
        exit 1
    fi
fi

# Step 3: Generate SVG visualization
echo -e "\nGenerating SVG visualization..."
python -m keymap_drawer draw "$OUT_DIR/keymap.yaml" -o "$SVG_OUTPUT"

# Check if the SVG was generated
if [ -f "$SVG_OUTPUT" ]; then
    echo -e "\nSuccess! SVG visualization created."
else
    echo -e "\nERROR: Failed to create SVG visualization."
    exit 1
fi

echo -e "\nDone! Generated files:"
echo "- Processed keymap: $OUT_DIR/processed_keymap.keymap"
echo "- YAML config: $OUT_DIR/keymap.yaml"
echo "- SVG visualization: $SVG_OUTPUT" 
