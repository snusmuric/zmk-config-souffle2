# Souffle Keyboard ZMK Configuration

This repository contains the ZMK configuration for the Souffle split ergonomic keyboard, which is based on the Sofle design. The keyboard features a 5x6 matrix layout with an additional rotary encoder.

## Keyboard Layout

![Keyboard Layout](keymap.svg)

## Overview

The Souffle configuration uses:

- 5 rows x 6 columns per half
- Homerow mods for improved ergonomics
- Multiple layers for symbols, numbers, navigation, and function keys
- Custom macros for improved productivity
- Combos for frequently used keys and shortcuts

## Tools

This repository includes custom tools for working with ZMK keymaps:

- **keymap-tools/process_keymap.py**: Processes ZMK keymap files, extracts key positions, and generates a consolidated keymap file
- **keymap-tools/generate_keymap_visualization.sh**: All-in-one script that processes the keymap and generates an SVG visualization

## Setup and Usage

1. Clone this repository
2. Set up the environment:
   ```bash
   cd keymap-tools
   ./generate_keymap_visualization.sh
   ```

This will:

- Check for and install keymap-drawer if needed
- Process the ZMK keymap files
- Generate a visual representation of the keyboard layout

## Support

For questions and support with this configuration, please open an issue in this repository.
