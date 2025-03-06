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

# Configuration file for keymap-drawer
CONFIG_FILE="$TOOLS_DIR/keymap_drawer.config.yaml"

# Final SVG in root directory
SVG_OUTPUT="$KEYMAP_DIR/keymap.svg"

echo "Working with paths:"
echo "- Root directory: $KEYMAP_DIR"
echo "- Config directory: $CONFIG_DIR"
echo "- Tools directory: $TOOLS_DIR"
echo "- Output directory: $OUT_DIR"
echo "- Keymap drawer directory: $KEYMAP_DRAWER_DIR"
echo "- Configuration file: $CONFIG_FILE"
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

# Step 1.5: Combo processing is now handled directly in the process_keymap.py script
echo -e "\nNOTE: Combos are now processed directly within the Python script"

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
    python -m keymap_drawer parse -z "$OUT_DIR/processed_keymap.keymap" -o "$OUT_DIR/keymap.yaml"
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

# Check if the YAML file has combos section already
if ! grep -q "^combos:" "$OUT_DIR/keymap.yaml"; then
    echo "No combos found in the parsed output. Extracting combos from processed keymap..."
    
    # Extract combo information from processed keymap.keymap
    COMBOS_FILE="$OUT_DIR/combos.yml"
    # Extract all combo definitions, format as YAML
    grep -A 6 "combo_" "$OUT_DIR/processed_keymap.keymap" | grep -E 'combo_|bindings|key-positions|timeout-ms|require-prior-idle-ms' | sed 's/;//' | sed 's/{//' | sed 's/}//' | sed 's/^\s*/  /' | sed 's/combo_\(.*\):/- name: \1/' | sed 's/bindings = /  binding: /' | sed 's/key-positions = /  positions: /' | sed 's/timeout-ms = /  timeout: /' | sed 's/require-prior-idle-ms = /  prior-idle: /' > "$COMBOS_FILE"
    
    # Add combos section to YAML file
    TMP_YAML=$(mktemp)
    cat "$OUT_DIR/keymap.yaml" > "$TMP_YAML"
    echo "combos:" >> "$TMP_YAML"
    cat "$COMBOS_FILE" >> "$TMP_YAML"
    mv "$TMP_YAML" "$OUT_DIR/keymap.yaml"
    rm "$COMBOS_FILE"
    echo "Added combos information to YAML file"
else
    echo "Combos section already exists in YAML file"
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

# Add combos directly to the YAML file
echo -e "\nAdding combos to the YAML file..."
COMBO_FILE="$CONFIG_DIR/includes/combos.dtsi"

if [ -f "$COMBO_FILE" ]; then
    echo "Found combos file: $COMBO_FILE"
    
    # Create a temporary file for combos
    TMP_COMBOS=$(mktemp)
    
    # Create a YAML combos section with the format keymap-drawer expects
    cat > "$TMP_COMBOS" << 'EOF'
combos:
  - p: [37, 25]
    k: LG(Z)
  - p: [28, 27]
    k: MY_REDO
  - p: [38, 26]
    k: LG(X)
  - p: [39, 27]
    k: LG(C)
  - p: [40, 28]
    k: LG(V)
  - p: [41, 53]
    k: NUM
  - p: [40, 52]
    k: NAV_LEFTHAND_SELECTION
  - p: [27, 28]
    k: ENTER
  - p: [26, 27]
    k: BACKSPACE
  - p: [31, 32]
    k: ENTER
  - p: [32, 33]
    k: BACKSPACE
  - p: [30, 44]
    k: LA(LSHIFT)
  - p: [1, 13]
    k: PRINTSCREEN
  - p: [2, 14]
    k: LA(LG(N5))
  - p: [3, 15]
    k: LA(LG(N6))
EOF
    
    # Check if the YAML file has a combos section
    if grep -q "^combos:" "$OUT_DIR/keymap.yaml"; then
        echo "Replacing existing combos section in YAML file"
        sed -i.bak '/^combos:/,/^[a-z]*:/s/^combos:.*$//' "$OUT_DIR/keymap.yaml"
        sed -i.bak '/^combos:/,/^[a-z]*:/s/^  - p:.*$//' "$OUT_DIR/keymap.yaml"
        sed -i.bak '/^combos:/,/^[a-z]*:/s/^    k:.*$//' "$OUT_DIR/keymap.yaml"
    fi
    
    # Append the combos to the keymap.yaml file
    cat "$TMP_COMBOS" >> "$OUT_DIR/keymap.yaml"
    echo "Adding combos to YAML file"
    
    # Clean up temp file
    rm "$TMP_COMBOS"
    
    # Check for potentially problematic cross-half combos
    echo -e "\nChecking for cross-half combos..."
    # Left half positions: 0-5, 12-17, 24-29, 36-42, 50-54
    # Right half positions: 6-11, 18-23, 30-35, 43-49, 55-59
    grep -n "p: \[[0-9]" "$OUT_DIR/keymap.yaml" | grep -E "p: \[([0-4]|1[2-7]|2[4-9]|3[6-9]|4[0-2]|5[0-4]),.*([6-9]|1[0-1]|1[8-9]|2[0-3]|3[0-5]|4[3-9]|5[5-9])\]|p: \[([6-9]|1[0-1]|1[8-9]|2[0-3]|3[0-5]|4[3-9]|5[5-9]),.*([0-5]|1[2-7]|2[4-9]|3[6-9]|4[0-2]|5[0-4])\]" || echo "No cross-half combos detected!"
else
    echo "WARNING: Combos file not found at $COMBO_FILE"
fi

# Merge configuration settings into keymap.yaml directly
echo -e "\nMerging configuration settings into keymap.yaml..."
if [ -f "$CONFIG_FILE" ] && [ -f "$OUT_DIR/keymap.yaml" ]; then
    # Create a temporary file
    TMP_FILE=$(mktemp)
    
    # Read the config file and append it to the keymap.yaml file
    cat "$OUT_DIR/keymap.yaml" > "$TMP_FILE"
    cat "$CONFIG_FILE" >> "$TMP_FILE"
    
    # Move the temp file back to the original location
    mv "$TMP_FILE" "$OUT_DIR/keymap.yaml"
    echo "Configuration settings merged successfully"
else
    echo "WARNING: Either configuration file or keymap.yaml not found. Proceeding without custom configuration."
fi

if [ "$FORCE_LOCAL_REPO" = true ] || ! command -v keymap &> /dev/null; then
    if [ -d "$KEYMAP_DRAWER_DIR" ]; then
        echo "Using local keymap-drawer repository for drawing"
        cd "$KEYMAP_DRAWER_DIR"
        # Use the configuration file to customize key size and appearance
        python -m keymap_drawer draw "$OUT_DIR/keymap.yaml" -o "$SVG_OUTPUT"
        cd "$TOOLS_DIR"
    else
        # This should never happen since we already checked above
        echo "ERROR: keymap-drawer repository not found"
        exit 1
    fi
else
    echo "Using installed keymap-drawer package for drawing"
    # Use the configuration file to customize key size and appearance
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
