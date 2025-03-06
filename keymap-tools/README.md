# ZMK Keymap Processing Tools

This directory contains tools for processing ZMK keymap files to:

1. Resolve all include statements
2. Replace symbolic key positions with numeric values
3. Replace symbolic layer IDs with numeric values
4. Generate a consolidated keymap file for visualization

## Setup Environment

### Prerequisites

- Python 3.6 or newer
- `keymap-drawer` (for visualization)

### Installing Dependencies

1. Install Python from [python.org](https://python.org) if you don't have it already.

2. Install `keymap-drawer`:
   ```bash
   pip install keymap-drawer
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

All output files will be saved in this directory.

## Manual Process

If you prefer to run the steps manually or need more control:

### Step 1: Process ZMK Keymap

The `process_keymap.py` script takes a ZMK keymap file with includes and creates a consolidated file:

```bash
python3 process_keymap.py ../config/base.keymap ./processed_keymap.keymap
```

### Step 2: Generate YAML Configuration

Generate a YAML configuration from the processed keymap:

```bash
cd ../keymap-drawer
python -m keymap_drawer parse -z ../keymap-tools/processed_keymap.keymap -o ../keymap-tools/keymap.yaml
```

### Step 3: Edit YAML Configuration (if needed)

You may need to edit the YAML file to specify the correct keyboard layout:

```yaml
layout: { zmk_keyboard: sofle }
```

### Step 4: Generate SVG Visualization

Generate an SVG visualization of your keymap:

```bash
cd ../keymap-drawer
python -m keymap_drawer draw ../keymap-tools/keymap.yaml -o ../keymap-tools/keymap.svg
```

## Files Description

- `process_keymap.py`: Main Python script for processing ZMK keymap files
- `processed_keymap.keymap`: Consolidated keymap file with resolved includes and numeric values
- `keymap.yaml`: Configuration file for keymap-drawer
- `keymap.svg`: SVG visualization of your keyboard layout
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
