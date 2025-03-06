#!/usr/bin/env python3

import re
import os
import sys
from pathlib import Path

def read_file(path):
    """Read the content of a file."""
    try:
        with open(path, 'r') as f:
            content = f.read()
            print(f"Read file {path}: {len(content)} bytes")
            return content
    except Exception as e:
        print(f"Error reading file {path}: {e}")
        return ""

def find_includes(content, base_dir, project_root):
    """Find all #include statements and return a list of file paths."""
    includes = []
    include_pattern = r'^\s*#include\s+[<"]([^>"]+)[>"]'
    
    for line in content.split('\n'):
        match = re.search(include_pattern, line)
        if match and not line.strip().startswith('//'):
            include_path = match.group(1)
            print(f"Found include: {include_path}")
            
            # Skip system includes and ZMK core includes
            if include_path.startswith('<') or include_path.startswith('dt-bindings/') or include_path.startswith('behaviors') or include_path.startswith('input/'):
                print(f"Skipping system/ZMK include: {include_path}")
                continue
                
            # Special handling for zmk-helpers files
            if include_path.startswith("zmk-helpers/"):
                candidates = [
                    os.path.join(project_root, include_path),
                    os.path.join(project_root, "..", include_path),
                    os.path.join(project_root, "..", "..", include_path)
                ]
            else:
                # Local include paths
                candidates = [
                    os.path.join(base_dir, include_path),
                    os.path.join(base_dir, "includes", include_path),
                    os.path.join(project_root, include_path),
                    os.path.join(project_root, "includes", include_path)
                ]
            
            found = False
            for candidate in candidates:
                if os.path.exists(candidate):
                    print(f"Found include file: {candidate}")
                    includes.append(candidate)
                    found = True
                    break
            
            if not found:
                print(f"WARNING: Could not find include file: {include_path}")
                # For sofle.h specifically, look in zmk-helpers folder
                if include_path.endswith("sofle.h") or "key-labels" in include_path:
                    # Try to find the key-labels folder
                    helpers_dirs = [
                        os.path.join(project_root, "zmk-helpers"),
                        os.path.join(project_root, "..", "zmk-helpers"),
                        os.path.join(project_root, "..", "..", "zmk-helpers")
                    ]
                    
                    for helpers_dir in helpers_dirs:
                        key_labels_path = os.path.join(helpers_dir, "include", "zmk-helpers", "key-labels")
                        if os.path.exists(key_labels_path):
                            sofle_h_path = os.path.join(key_labels_path, "sofle.h")
                            if os.path.exists(sofle_h_path):
                                print(f"Found sofle.h at: {sofle_h_path}")
                                includes.append(sofle_h_path)
                                found = True
                                break
                            
                    if not found:
                        print(f"INFO: Could not find key-labels/sofle.h in zmk-helpers")
    
    return includes

def extract_defines(content):
    """Extract #define statements and return a dictionary of replacements."""
    defines = {}
    define_pattern = r'^\s*#define\s+(\w+)\s+(.+)$'
    
    for line in content.split('\n'):
        match = re.search(define_pattern, line)
        if match and not line.strip().startswith('//'):
            key = match.group(1)
            value = match.group(2).strip()
            # Remove trailing comments
            value = re.sub(r'//.*$', '', value).strip()
            defines[key] = value
    
    print(f"Extracted {len(defines)} define statements")
    return defines

def extract_key_positions(content):
    """Extract key position definitions from a file."""
    key_positions = {}
    key_pos_pattern = r'^\s*#define\s+(L[NTMB][0-5]|R[NTMB][0-5]|L[H][0-4]|R[H][0-4]|[LR]EC)\s+(\d+)\s*'
    
    for line in content.split('\n'):
        match = re.search(key_pos_pattern, line)
        if match and not line.strip().startswith('//'):
            key = match.group(1)
            value = match.group(2)
            key_positions[key] = value
    
    if key_positions:
        print(f"Extracted {len(key_positions)} key positions")
        print(f"Sample key positions: {list(key_positions.items())[:5]}")
    
    return key_positions

def normalize_keymap(keymap_content):
    """Clean up and normalize the keymap file content."""
    # Remove comments
    keymap_content = re.sub(r'//.*$', '', keymap_content, flags=re.MULTILINE)
    
    # Remove empty lines
    keymap_content = re.sub(r'\n\s*\n', '\n', keymap_content)
    
    return keymap_content

def process_keymap(keymap_path, output_path):
    """Process the keymap file and its includes to create a consolidated keymap."""
    base_dir = os.path.dirname(keymap_path)
    project_root = os.path.dirname(base_dir)
    
    print(f"Base directory: {base_dir}")
    print(f"Project root: {project_root}")
    
    keymap_content = read_file(keymap_path)
    if not keymap_content:
        print(f"Error: Empty keymap content from {keymap_path}")
        return ""
    
    # Find and read sofle.keymap for key position info
    sofle_keymap_path = os.path.join(base_dir, "sofle.keymap")
    sofle_content = ""
    if os.path.exists(sofle_keymap_path):
        sofle_content = read_file(sofle_keymap_path)
    
    # Extract all includes recursively
    all_content = [keymap_content, sofle_content]
    includes_to_process = find_includes(keymap_content, base_dir, project_root)
    if sofle_content:
        includes_to_process.extend(find_includes(sofle_content, base_dir, project_root))
    
    processed_includes = set()
    
    while includes_to_process:
        include_path = includes_to_process.pop(0)
        if include_path in processed_includes:
            continue
            
        processed_includes.add(include_path)
        include_content = read_file(include_path)
        
        if include_content:
            all_content.append(include_content)
            
            # Find nested includes
            new_includes = find_includes(include_content, os.path.dirname(include_path), project_root)
            includes_to_process.extend([inc for inc in new_includes if inc not in processed_includes])
    
    print(f"Processed {len(processed_includes)} includes")
    combined_content = '\n'.join(all_content)
    
    # Extract all #define statements
    defines = extract_defines(combined_content)
    
    # Extract key position definitions
    key_positions = extract_key_positions(combined_content)
    
    # Check if we have any key positions - this is critical
    if not key_positions:
        print("WARNING: No key positions found. Using hardcoded Sofle layout...")
        # Manual key positions based on the standard Sofle layout
        key_positions = {
            "LN0": "5", "LN1": "4", "LN2": "3", "LN3": "2", "LN4": "1", "LN5": "0",
            "RN0": "6", "RN1": "7", "RN2": "8", "RN3": "9", "RN4": "10", "RN5": "11",
            "LT0": "17", "LT1": "16", "LT2": "15", "LT3": "14", "LT4": "13", "LT5": "12",
            "RT0": "18", "RT1": "19", "RT2": "20", "RT3": "21", "RT4": "22", "RT5": "23",
            "LM0": "29", "LM1": "28", "LM2": "27", "LM3": "26", "LM4": "25", "LM5": "24",
            "RM0": "30", "RM1": "31", "RM2": "32", "RM3": "33", "RM4": "34", "RM5": "35",
            "LB0": "41", "LB1": "40", "LB2": "39", "LB3": "38", "LB4": "37", "LB5": "36",
            "LEC": "42", "REC": "43",
            "RB0": "44", "RB1": "45", "RB2": "46", "RB3": "47", "RB4": "48", "RB5": "49",
            "LH0": "54", "LH1": "53", "LH2": "52", "LH3": "51", "LH4": "50",
            "RH0": "55", "RH1": "56", "RH2": "57", "RH3": "58", "RH4": "59"
        }
        print(f"Using manual key position mappings: {len(key_positions)} positions defined")
    
    # Normalize the keymap content
    processed_content = normalize_keymap(keymap_content)
    
    # Replace key positions in key-positions attributes
    def replace_key_positions(match):
        positions_str = match.group(1)
        positions = re.findall(r'(\w+)', positions_str)
        numeric_positions = []
        
        for pos in positions:
            if pos in key_positions:
                numeric_positions.append(key_positions[pos])
            else:
                numeric_positions.append(pos)
        
        return f'key-positions = <{" ".join(numeric_positions)}>;'
    
    key_pos_pattern = r'key-positions\s*=\s*<([^>]+)>;'
    processed_content = re.sub(key_pos_pattern, replace_key_positions, processed_content)
    
    # Replace layer references
    layer_replacements = 0
    for layer_name, layer_id in defines.items():
        if re.match(r'^[A-Z_]+$', layer_name) and layer_name in processed_content:
            # Only replace if it looks like a layer name (all caps with underscores)
            # and is actually used in the keymap
            try:
                # Try to convert to int to verify it's a number
                int(layer_id)
                # Use word boundary to avoid partial matches
                old_content = processed_content
                processed_content = re.sub(r'\b' + layer_name + r'\b', layer_id, processed_content)
                if old_content != processed_content:
                    layer_replacements += 1
            except ValueError:
                # Not a numeric value, skip
                pass
    
    print(f"Made {layer_replacements} layer name replacements")
    
    # Create a human-readable layer mapping
    layer_names = {}
    for name, id_str in defines.items():
        if re.match(r'^[A-Z_]+$', name):
            try:
                layer_id = int(id_str)
                layer_names[layer_id] = name
            except ValueError:
                continue
    
    # Print layer mapping
    print("\nLayer mapping:")
    for layer_id in sorted(layer_names.keys()):
        print(f"Layer {layer_id}: {layer_names[layer_id]}")
    
    # Return the processed content
    return processed_content

def main():
    """Main function for processing a keymap file."""
    # Default paths based on the repository structure
    current_dir = os.path.dirname(os.path.abspath(__file__))
    keymap_path = os.path.join(os.path.dirname(current_dir), "config", "base.keymap")
    output_path = os.path.join(current_dir, "processed_keymap.keymap")
    
    # Allow command line arguments to override defaults
    if len(sys.argv) > 1:
        keymap_path = os.path.abspath(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = os.path.abspath(sys.argv[2])
    
    print(f"Input file: {keymap_path}")
    print(f"Output file: {output_path}")
    
    if not os.path.exists(keymap_path):
        print(f"Error: Input file does not exist: {keymap_path}")
        sys.exit(1)
    
    # Process the keymap
    processed_content = process_keymap(keymap_path, output_path)
    
    # Write the processed content to the output file
    if processed_content:
        with open(output_path, 'w') as f:
            f.write(processed_content)
        print(f"Processed keymap saved to {output_path}")
    else:
        print("Error: Failed to process keymap")
        sys.exit(1)

if __name__ == "__main__":
    main() 
