# ZMK Config for Souffle Keyboard

This repository contains the ZMK configuration for the Souffle keyboard, a customized split ergonomic keyboard based on the Sofle design.

## Keyboard Layout

The following visualization shows the current keyboard layout configuration:

![Souffle Keyboard Layout](./keymap.svg)

## Features

- Split ergonomic design
- Multiple layers for different functionality (Base, Navigation, Numbers, Symbols, etc.)
- Custom keybindings optimized for programming and everyday typing
- ZMK firmware for wireless connectivity

## Getting Started

To build and flash this firmware:

1. Follow the [ZMK documentation](https://zmk.dev/docs) for setting up your development environment
2. Clone this repository
3. Build the firmware using the ZMK build scripts
4. Flash the firmware to your keyboard

## Setup Layout Visualization

This project uses [keymap-drawer](https://github.com/caksoylar/keymap-drawer) to generate keyboard layout visualizations. To set this up:

### Option 1: Install as a Python package (Recommended)

1. Make sure you have Python 3.10+ installed
2. Install keymap-drawer using pip:
   ```bash
   pip install keymap-drawer
   ```

### Option 2: Clone the repository

If you prefer to have the source code available:

1. Clone the keymap-drawer repository into this project:
   ```bash
   git clone https://github.com/caksoylar/keymap-drawer.git
   ```
2. Install the required dependencies:
   ```bash
   cd keymap-drawer
   pip install -e .
   cd ..
   ```

## Generating Layout Visualization

To update the visualization after making changes to your keymap:

```bash
cd keymap-tools
./generate_keymap_visualization.sh
```

This will process your keymap configuration and create an updated SVG visualization in the root directory.
