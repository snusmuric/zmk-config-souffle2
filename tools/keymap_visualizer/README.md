# ZMK Keymap Visualizer

A Python script to generate visual representations of ZMK keyboard layouts.

## Overview

This tool reads a ZMK keymap file and generates two types of visualizations in the `out` directory:

1. An interactive HTML view where you can switch between layers
2. A static SVG showing all layers at once

## How It Works

### 1. Data Model

The script uses three main data structures:

```python
@dataclass
class Key:
    code: str        # Raw ZMK key code (e.g., "&kp A")
    label: str       # Display label
    x: float        # Position in the grid
    y: float
    width: float    # For special-sized keys
    height: float
    color: str      # Based on key function
    labels: List[str] # Multiple labels for complex keys
```

```python
@dataclass
class Layer:
    name: str        # Layer identifier
    display_name: str # Human-readable name
    keys: List[Key]  # Keys in this layer
```

### 2. Processing Pipeline

1. **Parse Keymap File**

   - Reads `base.keymap`
   - Extracts layer definitions using regex
   - Parses key bindings within each layer

2. **Key Processing**

   - Converts key indices to grid positions
   - Determines key colors based on function
   - Parses complex key codes into readable labels

3. **Visualization Generation**
   - Creates HTML with interactive layer switching
   - Generates SVG with all layers stacked vertically

### 3. Key Layout

The script handles a 60-key split keyboard layout:

```
╭────────────────────────────┬────────────────────────────╮
│  0   1   2   3   4   5    │    6   7   8   9  10  11  │
│ 12  13  14  15  16  17    │   18  19  20  21  22  23  │
│ 24  25  26  27  28  29    │   30  31  32  33  34  35  │
│ 36  37  38  39  40  41 42 │43 44  45  46  47  48  49  │
╰───────╮ 50  51  52  53  54│55  56  57  58  59 ╭───────╯
```

### 4. Color Coding

Keys are color-coded based on their function:

- Light red (`#ffcccc`): Shift keys
- Light blue (`#cce5ff`): Other modifiers (Ctrl, Alt, GUI)
- Light green (`#e6ffcc`): Layer changes
- Light orange (`#ffe6cc`): Tap dance
- Light purple (`#e6ccff`): Combos
- Light gray (`#f2f2f2`): Regular keys

## Usage

1. Make sure the script is executable:

   ```bash
   chmod +x visualizer.py
   ```

2. Run the script:

   ```bash
   ./visualizer.py
   ```

3. Open the generated files in the `out` directory:
   - `out/keymap_layout.html` - Interactive view in your browser
   - `out/keymap_layout.svg` - Static view in any SVG viewer

## Output Files

### HTML Visualization

- Interactive layer switching via dropdown
- Hover effects on keys
- Key code tooltips
- Color-coded legend

### SVG Visualization

- All layers in one view
- Vertically stacked
- Maintains key positions and colors
- Useful for documentation

## Dependencies

- Python 3.x
- Standard library only (no external dependencies)
