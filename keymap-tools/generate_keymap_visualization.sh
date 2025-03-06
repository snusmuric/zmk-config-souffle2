#!/bin/bash

# Force using local repository instead of installed command
FORCE_LOCAL_REPO=true

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

# Check if keymap-drawer repository exists and install it if necessary
if [ -d "$KEYMAP_DRAWER_DIR" ]; then
    echo -e "\nChecking keymap-drawer installation..."
    # Check if the package is installed in development mode
    if ! pip list | grep -q "keymap-drawer.*\(editable\|dev\)"; then
        echo "Installing keymap-drawer in development mode..."
        cd "$KEYMAP_DRAWER_DIR"
        pip install -e .
        cd "$TOOLS_DIR"
        echo "keymap-drawer installed successfully in development mode"
    else
        echo "keymap-drawer is already installed in development mode"
    fi
else
    echo -e "\nWARNING: keymap-drawer repository not found at $KEYMAP_DRAWER_DIR"
    echo "Would you like to clone and install it now? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Cloning keymap-drawer repository..."
        git clone https://github.com/caksoylar/keymap-drawer.git "$KEYMAP_DRAWER_DIR"
        echo "Installing keymap-drawer in development mode..."
        cd "$KEYMAP_DRAWER_DIR"
        pip install -e .
        cd "$TOOLS_DIR"
        echo "keymap-drawer cloned and installed successfully"
    else
        echo "Continuing without local keymap-drawer repository"
    fi
fi

# Ensure output directory exists
mkdir -p "$OUT_DIR"

# Step 1: Process the keymap
echo -e "\nProcessing keymap..."
python3 "$TOOLS_DIR/process_keymap.py" "$CONFIG_DIR/base.keymap" "$OUT_DIR/processed_keymap.keymap"

# Step 2: Generate YAML configuration
echo -e "\nGenerating YAML configuration..."

# Check if we should force local repo or if keymap command is not available
if [ "$FORCE_LOCAL_REPO" = true ] || ! command -v keymap &> /dev/null; then
    # Check if repository exists
    if [ -d "$KEYMAP_DRAWER_DIR" ]; then
        echo "Using local keymap-drawer repository"
        cd "$KEYMAP_DRAWER_DIR"
        python -m keymap_drawer parse -z "$OUT_DIR/processed_keymap.keymap" -o "$OUT_DIR/keymap.yaml"
        cd "$TOOLS_DIR"
    else
        echo "ERROR: keymap-drawer repository not found at $KEYMAP_DRAWER_DIR"
        echo "Please clone the repository: git clone https://github.com/caksoylar/keymap-drawer.git $KEYMAP_DRAWER_DIR"
        exit 1
    fi
else
    echo "Using installed keymap-drawer package"
    keymap parse -z "$OUT_DIR/processed_keymap.keymap" -o "$OUT_DIR/keymap.yaml"
fi

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
if [ "$FORCE_LOCAL_REPO" = true ] || ! command -v keymap &> /dev/null; then
    if [ -d "$KEYMAP_DRAWER_DIR" ]; then
        echo "Using local keymap-drawer repository for drawing"
        cd "$KEYMAP_DRAWER_DIR"
        python -m keymap_drawer draw "$OUT_DIR/keymap.yaml" -o "$SVG_OUTPUT"
        cd "$TOOLS_DIR"
    else
        # This should never happen since we already checked above
        echo "ERROR: keymap-drawer repository not found"
        exit 1
    fi
else
    echo "Using installed keymap-drawer package for drawing"
    keymap draw "$OUT_DIR/keymap.yaml" -o "$SVG_OUTPUT"
fi

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
