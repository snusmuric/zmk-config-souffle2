# ZMK Keymap Processing Tools

This directory contains tools for processing ZMK keymap files to:

1. Resolve all include statements
2. Replace symbolic key positions with numeric values
3. Replace symbolic layer IDs with numeric values
4. Generate a consolidated keymap file for visualization

## Setup Environment

### Prerequisites

- Python 3.10 or newer
- `keymap-drawer` (for visualization)

### Installing keymap-drawer

There are two ways to set up keymap-drawer:

#### Option 1: Install as a Python package (Recommended)

Install `keymap-drawer` directly from PyPI:

```bash
pip install keymap-drawer
```

This method is simpler and doesn't require keeping source code in your project.

#### Option 2: Clone the repository

If you prefer having the source code available:

1. Clone the repository into the parent directory:

   ```bash
   git clone https://github.com/caksoylar/keymap-drawer.git ../keymap-drawer
   ```

2. Install in development mode:
   ```bash
   cd ../keymap-drawer
   pip install -e .
   cd ../keymap-tools
   ```

## Quick Start

The easiest way to generate your keymap visualization is to use the provided all-in-one script:

```bash
./generate_keymap_visualization.sh
```

This script will:

1. Process your ZMK keymap from `../config/base.keymap`
2. Generate a YAML configuration file
3. Update the YAML with the correct keyboard layout
4. Create an SVG visualization

Intermediate files will be stored in the `out` directory, and the final SVG will be placed in the root project folder.

## Manual Process

If you prefer to run the steps manually or need more control:

### Step 1: Process ZMK Keymap

The `process_keymap.py` script takes a ZMK keymap file with includes and creates a consolidated file:

```bash
python3 process_keymap.py ../config/base.keymap ./out/processed_keymap.keymap
```

### Step 2: Generate YAML Configuration

Generate a YAML configuration from the processed keymap:

```bash
# If using installed package:
keymap parse -z ./out/processed_keymap.keymap -o ./out/keymap.yaml

# If using cloned repository:
cd ../keymap-drawer
python -m keymap_drawer parse -z ../keymap-tools/out/processed_keymap.keymap -o ../keymap-tools/out/keymap.yaml
cd ../keymap-tools
```

### Step 3: Edit YAML Configuration (if needed)

You may need to edit the YAML file to specify the correct keyboard layout:

```yaml
layout: { zmk_keyboard: sofle }
```

### Step 4: Generate SVG Visualization

Generate an SVG visualization of your keymap:

```bash
# If using installed package:
keymap draw ./out/keymap.yaml -o ../keymap.svg

# If using cloned repository:
cd ../keymap-drawer
python -m keymap_drawer draw ../keymap-tools/out/keymap.yaml -o ../keymap.svg
cd ../keymap-tools
```

## Files Description

- `process_keymap.py`: Main Python script for processing ZMK keymap files
- `out/processed_keymap.keymap`: Consolidated keymap file with resolved includes and numeric values
- `out/keymap.yaml`: Configuration file for keymap-drawer
- `../keymap.svg`: SVG visualization of your keyboard layout in the root directory
- `generate_keymap_visualization.sh`: All-in-one script to generate the visualization

## Troubleshooting

### Common Issues

1. **Missing include files**:

   - Some warnings about missing includes (like ZMK helpers) are normal and won't affect processing
   - Critical includes should be in your config directory

2. **Layout not found error**:

   - Make sure the YAML file specifies the correct keyboard layout
   - Example: `layout: { zmk_keyboard: sofle }`

3. **Key position mapping issues**:
   - If key positions aren't properly mapped, check your key position definitions
   - Make sure all used key positions are defined in your config files
