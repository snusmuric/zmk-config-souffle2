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

## Layout Visualization

The keyboard layout visualization is automatically generated using the `keymap-tools` scripts. To update the visualization after making changes to your keymap:

```bash
cd keymap-tools
./generate_keymap_visualization.sh
```

This will process your keymap configuration and create an updated SVG visualization in the root directory.
