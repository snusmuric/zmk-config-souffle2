#!/usr/bin/env python3

import re
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import xml.etree.ElementTree as ET
import html

@dataclass
class Key:
    code: str
    label: str
    x: float
    y: float
    width: float = 1
    height: float = 1
    color: str = "#cccccc"
    labels: List[str] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = self.parse_labels()

    def parse_labels(self) -> List[str]:
        """Parse complex key codes into multiple labels"""
        code = self.code.strip()
        if not code.startswith('&'):
            return [code]

        # Remove & prefix
        code = code[1:]

        # Special cases
        if code.startswith('td_'):
            return ['TD', code[3:].replace('_', '\n')]
        if code.startswith('hm_'):
            parts = code[3:].split('_')
            return [parts[-1], f"HM\n{parts[0]}"]
        if code.startswith('lt_'):
            parts = code[3:].split('_')
            return [parts[-1], f"LT\n{parts[0]}"]
        if code.startswith('mo_'):
            return ['MO', code[3:]]
        if code.startswith('tog_'):
            return ['TOG', code[4:]]
        if code.startswith('kp_'):
            return [code[3:]]
        if code.startswith('kp '):
            return [code[3:]]
        
        # Basic key
        return [code]

@dataclass
class Layer:
    name: str
    display_name: str
    keys: List[Key]

def get_key_color(key: Key) -> str:
    """Determine key color based on its function"""
    code = key.code.lower()
    if 'shift' in code:
        return "#ffcccc"  # Light red for shifts
    if any(mod in code for mod in ['ctrl', 'alt', 'gui']):
        return "#cce5ff"  # Light blue for modifiers
    if any(mod in code for mod in ['mo_', 'lt_', 'tog_']):
        return "#e6ffcc"  # Light green for layer changes
    if 'td_' in code:
        return "#ffe6cc"  # Light orange for tap dance
    if 'combo' in code:
        return "#e6ccff"  # Light purple for combos
    return "#f2f2f2"  # Light gray for regular keys

def get_key_position(idx: int) -> Tuple[int, int]:
    """
    Convert key index to x,y coordinates based on the 60-key layout:
    First 4 rows: 12 keys each (0-47)
    Last row: 5 thumb keys per side (48-57)
    
    Layout:
    ╭────────────────────────────┬────────────────────────────╮
    │  0   1   2   3   4   5    │    6   7   8   9  10  11  │
    │ 12  13  14  15  16  17    │   18  19  20  21  22  23  │
    │ 24  25  26  27  28  29    │   30  31  32  33  34  35  │
    │ 36  37  38  39  40  41 42 │43 44  45  46  47  48  49  │
    ╰───────╮ 50  51  52  53  54│55  56  57  58  59 ╭───────╯
    """
    if idx < 48:  # Regular keys (4 rows × 12 keys)
        row = idx // 12
        col = idx % 12
        if col >= 6:  # Right half
            col += 2  # Add gap between halves
    else:  # Thumb keys
        row = 4
        thumb_idx = idx - 48
        if thumb_idx < 5:  # Left thumb cluster
            col = thumb_idx
        else:  # Right thumb cluster
            col = (thumb_idx - 5) + 8  # Start after the gap
    
    return col, row

def parse_keymap_file(file_path: str) -> List[Layer]:
    with open(file_path, 'r') as f:
        content = f.read()

    layers = []
    # First find all layer definitions
    layer_matches = re.finditer(r'(\w+)_layer\s*{[^}]*display-name\s*=\s*"([^"]+)"[^}]*bindings\s*=\s*<([^>]+)>', content)
    
    for match in layer_matches:
        layer_name = match.group(1)
        display_name = match.group(2)
        bindings = match.group(3)

        # Clean up the bindings string
        bindings = re.sub(r'\s+', ' ', bindings).strip()
        
        # Parse bindings into individual keys
        keys = []
        # Split on & but keep the & with the code
        key_codes = ['&' + code for code in bindings.split('&') if code.strip()]
        
        # Process each key
        for idx, code in enumerate(key_codes):
            if not code or code.strip() == '&none' or code.strip() == '&trans':
                continue
                
            if idx >= 60:  # Only process first 60 keys
                break
                
            x, y = get_key_position(idx)
            
            # Clean up the code and create a readable label
            code = code.strip()
            label = code[1:]  # Remove &
            if ' ' in label:  # If it has parameters
                parts = label.split()
                label = parts[0]  # Use the command name
                if len(parts) > 1:  # Add parameters as sublabels
                    label = parts[-1]  # Use the last parameter as main label
            
            key = Key(
                code=code,
                label=label,
                x=x,
                y=y,
                width=1,
                height=1,
                color=get_key_color(Key(code=code, label="", x=0, y=0))
            )
            keys.append(key)

        layers.append(Layer(layer_name, display_name, keys))

    return layers

def generate_html(layers: List[Layer], output_file: str):
    """Generate an interactive HTML visualization"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ZMK Keymap Visualization</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .controls { margin-bottom: 20px; }
            .layer { display: none; margin-bottom: 40px; }
            .layer.active { display: block; }
            .keyboard { 
                display: grid; 
                grid-gap: 5px; 
                padding: 20px; 
                background: #eee; 
                border-radius: 10px;
                box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
            }
            .key { 
                width: 60px; height: 60px; 
                border: 1px solid #666;
                border-radius: 5px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                font-family: monospace;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
                background: white;
                box-shadow: 0 2px 3px rgba(0,0,0,0.1);
            }
            .key:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                z-index: 1;
            }
            .key-label { font-weight: bold; }
            .key-sublabel { font-size: 10px; color: #666; }
            .legend { 
                margin-top: 20px;
                padding: 10px;
                border-top: 1px solid #eee;
            }
            .legend-item { 
                display: inline-block; 
                margin-right: 20px;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 14px;
            }
            .color-box { 
                display: inline-block; 
                width: 20px; 
                height: 20px; 
                margin-right: 5px;
                vertical-align: middle;
                border: 1px solid #666;
                border-radius: 3px;
            }
            select {
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #ccc;
                font-size: 16px;
                outline: none;
            }
            select:focus {
                border-color: #666;
                box-shadow: 0 0 5px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ZMK Keymap Visualization</h1>
            
            <div class="controls">
                <label>Select Layer: </label>
                <select id="layerSelect" onchange="showLayer(this.value)">
    """
    
    # Add layer options
    for layer in layers:
        html_content += f'<option value="{layer.name}">{layer.display_name}</option>\n'
    
    html_content += """
                </select>
            </div>
            
    """
    
    # Add each layer
    for layer in layers:
        html_content += f'<div id="{layer.name}" class="layer">\n'
        html_content += f'<h2>{layer.display_name} Layer</h2>\n'
        html_content += '<div class="keyboard" style="grid-template-columns: repeat(14, 60px);">\n'
        
        # Create a matrix to hold keys
        matrix = [[None for _ in range(14)] for _ in range(5)]
        
        # Place keys in matrix
        for key in layer.keys:
            if 0 <= key.x < 14 and 0 <= key.y < 5:
                matrix[int(key.y)][int(key.x)] = key
        
        # Generate HTML for each key
        for row in matrix:
            for key in row:
                if key is None:
                    # Empty space
                    html_content += '<div style="width: 60px; height: 60px;"></div>\n'
                else:
                    labels_html = ""
                    for i, label in enumerate(key.labels):
                        class_name = "key-label" if i == 0 else "key-sublabel"
                        labels_html += f'<div class="{class_name}">{html.escape(label)}</div>'
                    
                    html_content += f"""
                    <div class="key" style="background: {key.color};" title="{html.escape(key.code)}">
                        {labels_html}
                    </div>
                    """
        
        html_content += '</div>\n</div>\n'
    
    # Add legend and JavaScript
    html_content += """
            <div class="legend">
                <div class="legend-item"><div class="color-box" style="background: #ffcccc;"></div>Shift</div>
                <div class="legend-item"><div class="color-box" style="background: #cce5ff;"></div>Modifiers</div>
                <div class="legend-item"><div class="color-box" style="background: #e6ffcc;"></div>Layer Change</div>
                <div class="legend-item"><div class="color-box" style="background: #ffe6cc;"></div>Tap Dance</div>
                <div class="legend-item"><div class="color-box" style="background: #e6ccff;"></div>Combos</div>
                <div class="legend-item"><div class="color-box" style="background: #f2f2f2;"></div>Regular Keys</div>
            </div>
        </div>
        
        <script>
        function showLayer(layerId) {
            document.querySelectorAll('.layer').forEach(layer => {
                layer.classList.remove('active');
            });
            document.getElementById(layerId).classList.add('active');
        }
        
        // Show first layer by default
        window.onload = function() {
            const firstLayer = document.querySelector('.layer');
            if (firstLayer) {
                firstLayer.classList.add('active');
            }
        }
        </script>
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_content)

def generate_svg(output_file: str, layers: List[Layer]):
    SVG_KEY_SIZE = 60
    SVG_GAP = 5
    
    # Calculate dimensions
    max_x = 14  # Fixed width for the keyboard
    max_y = 5   # Fixed height for each layer
    
    width = (max_x * (SVG_KEY_SIZE + SVG_GAP))
    height = (max_y * (SVG_KEY_SIZE + SVG_GAP) + 40) * len(layers)
    
    # Create SVG root
    svg = ET.Element('svg', {
        'width': str(width),
        'height': str(height),
        'xmlns': 'http://www.w3.org/2000/svg'
    })
    
    # Add style
    style = ET.SubElement(svg, 'style')
    style.text = '''
        .key { stroke: #666666; stroke-width: 1; }
        .key-label { font-family: monospace; font-size: 8px; }
        .key-sublabel { font-family: monospace; font-size: 6px; fill: #666666; }
        .layer-name { font-family: sans-serif; font-size: 20px; font-weight: bold; }
    '''
    
    # Draw each layer
    for layer_idx, layer in enumerate(layers):
        layer_g = ET.SubElement(svg, 'g', {
            'transform': f'translate(0, {layer_idx * (max_y * (SVG_KEY_SIZE + SVG_GAP) + 40)})'
        })
        
        # Layer name
        layer_name = ET.SubElement(layer_g, 'text', {
            'x': '10',
            'y': '25',
            'class': 'layer-name'
        })
        layer_name.text = f"{layer.name} Layer"
        
        # Create a matrix to hold keys
        matrix = [[None for _ in range(max_x)] for _ in range(max_y)]
        
        # Place keys in matrix
        for key in layer.keys:
            if 0 <= key.x < max_x and 0 <= key.y < max_y:
                matrix[int(key.y)][int(key.x)] = key
        
        # Draw keys
        for row_idx, row in enumerate(matrix):
            for col_idx, key in enumerate(row):
                if key is None:
                    continue
                    
                x = col_idx * (SVG_KEY_SIZE + SVG_GAP)
                y = row_idx * (SVG_KEY_SIZE + SVG_GAP) + 40
                
                # Key rectangle
                ET.SubElement(layer_g, 'rect', {
                    'x': str(x),
                    'y': str(y),
                    'width': str(SVG_KEY_SIZE),
                    'height': str(SVG_KEY_SIZE),
                    'rx': '5',
                    'class': 'key',
                    'fill': key.color
                })
                
                # Key labels
                labels = key.labels
                if len(labels) == 1:
                    text = ET.SubElement(layer_g, 'text', {
                        'x': str(x + SVG_KEY_SIZE/2),
                        'y': str(y + SVG_KEY_SIZE/2),
                        'text-anchor': 'middle',
                        'alignment-baseline': 'middle',
                        'class': 'key-label'
                    })
                    text.text = labels[0]
                else:
                    for i, label in enumerate(labels):
                        text = ET.SubElement(layer_g, 'text', {
                            'x': str(x + SVG_KEY_SIZE/2),
                            'y': str(y + 15 + i * 15),
                            'text-anchor': 'middle',
                            'class': 'key-label' if i == 0 else 'key-sublabel'
                        })
                        text.text = label
    
    # Write to file
    tree = ET.ElementTree(svg)
    ET.indent(tree)
    tree.write(output_file)

def main():
    # Parse keymap file
    keymap_path = os.path.join(os.path.dirname(__file__), '../../config/base.keymap')
    output_dir = os.path.join(os.path.dirname(__file__), 'out')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    layers = parse_keymap_file(keymap_path)
    
    # Generate both SVG and HTML
    generate_svg(output_file=os.path.join(output_dir, 'keymap_layout.svg'), layers=layers)
    generate_html(layers=layers, output_file=os.path.join(output_dir, 'keymap_layout.html'))
    
    print(f"Generated visualization with {len(layers)} layers")
    print(f"Files generated in {output_dir}:")
    print("- keymap_layout.svg (Static visualization)")
    print("- keymap_layout.html (Interactive visualization)")
    print("\nColor coding:")
    print("- Light red: Shift keys")
    print("- Light blue: Other modifiers (Ctrl, Alt, GUI)")
    print("- Light green: Layer changes")
    print("- Light orange: Tap dance")
    print("- Light purple: Combos")
    print("- Light gray: Regular keys")

if __name__ == '__main__':
    main() 
