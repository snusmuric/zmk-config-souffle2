#!/usr/bin/env python3

import re
import os
import sys
from pathlib import Path
import subprocess
import yaml

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
    # Updated pattern to capture all key position definitions in sofle.h or other files
    key_pos_pattern = r'^\s*#define\s+(L[NTMBH][0-5]|R[NTMBH][0-5]|[LR]EC|L[H][0-4]|R[H][0-4])\s+(\d+)\s*'
    
    for line in content.split('\n'):
        match = re.search(key_pos_pattern, line)
        if match and not line.strip().startswith('//'):
            key = match.group(1)
            value = match.group(2)
            key_positions[key] = value
            print(f"Found key position: {key} -> {value}")
    
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
            # Left half (L prefix)
            "LN5": "0", "LN4": "1", "LN3": "2", "LN2": "3", "LN1": "4", "LN0": "5",
            "LT5": "12", "LT4": "13", "LT3": "14", "LT2": "15", "LT1": "16", "LT0": "17",
            "LM5": "24", "LM4": "25", "LM3": "26", "LM2": "27", "LM1": "28", "LM0": "29",
            "LB5": "36", "LB4": "37", "LB3": "38", "LB2": "39", "LB1": "40", "LB0": "41",
            "LEC": "42",
            "LH4": "50", "LH3": "51", "LH2": "52", "LH1": "53", "LH0": "54",
            
            # Right half (R prefix)
            "RN0": "6", "RN1": "7", "RN2": "8", "RN3": "9", "RN4": "10", "RN5": "11",
            "RT0": "18", "RT1": "19", "RT2": "20", "RT3": "21", "RT4": "22", "RT5": "23",
            "RM0": "30", "RM1": "31", "RM2": "32", "RM3": "33", "RM4": "34", "RM5": "35",
            "REC": "43",
            "RB0": "44", "RB1": "45", "RB2": "46", "RB3": "47", "RB4": "48", "RB5": "49",
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
                numeric_pos = key_positions[pos]
                numeric_positions.append(numeric_pos)
                print(f"Mapping {pos} -> {numeric_pos}")
            else:
                numeric_positions.append(pos)
                print(f"Warning: No mapping found for {pos}, keeping as is")
        
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

def extract_layer_definitions(layers_file_path):
    """Extract layer definitions from the layers_definitions.dtsi file."""
    if not os.path.exists(layers_file_path):
        print(f"Layers definitions file not found: {layers_file_path}")
        return {}
    
    # Read the layers file
    layers_content = read_file(layers_file_path)
    if not layers_content:
        return {}
    
    # Extract layer definitions using regex
    layer_pattern = r'#define\s+(\w+)\s+(\d+)'
    layer_definitions = {}
    
    for match in re.finditer(layer_pattern, layers_content):
        layer_name = match.group(1)
        layer_value = match.group(2)
        layer_definitions[layer_name] = layer_value
    
    print(f"Extracted {len(layer_definitions)} layer definitions")
    print(f"Sample layer definitions: {list(layer_definitions.items())[:5]}")
    
    return layer_definitions

def process_combos(combo_file_path, key_positions, layer_definitions=None):
    """Process the combos file and extract combo definitions."""
    if not os.path.exists(combo_file_path):
        print(f"Combos file not found at {combo_file_path}")
        return []
    
    print(f"Read file {combo_file_path}: {os.path.getsize(combo_file_path)} bytes")
    with open(combo_file_path, 'r') as f:
        combos_content = f.read()
    
    if not combos_content:
        print("Combos file is empty")
        return []
    
    print(f"Sample of combos content: {combos_content[:200]}...")
    
    # Parse each combo directly from the combos.dtsi file
    yaml_combos = []

    # Pattern to match combo definitions
    combo_pattern = r'combo_(\w+)\s*{([^}]*)}'
    combo_matches = re.finditer(combo_pattern, combos_content)
    
    combo_count = 0
    for match in combo_matches:
        combo_count += 1
        name = match.group(1)
        combo_body = match.group(2)
        
        # Extract key positions
        key_pos_match = re.search(r'key-positions\s*=\s*<([^>]+)>', combo_body)
        if not key_pos_match:
            continue
            
        key_pos_str = key_pos_match.group(1)
        positions = []
        for pos in key_pos_str.split():
            if pos in key_positions:
                positions.append(int(key_positions[pos]))
            elif pos.isdigit():
                positions.append(int(pos))
        
        if not positions:
            continue
            
        # Extract binding
        binding_match = re.search(r'bindings\s*=\s*<([^>]+)>', combo_body)
        if not binding_match:
            continue
            
        binding = binding_match.group(1)
        
        # Extract key character from binding
        key_char = binding
        if '&kp ' in binding:
            key_char = binding.replace('&kp ', '')
            
        # Add the combo to our list with just positions and key
        yaml_combos.append({
            'p': positions,
            'k': key_char
        })
    
    print(f"Processed {combo_count} combos, extracted {len(yaml_combos)} valid combos")
    
    # For debugging, print the first few combos
    if yaml_combos:
        print("Sample of extracted combos:")
        for i, combo in enumerate(yaml_combos[:3]):
            print(f"  Combo {i+1}: positions={combo['p']}, key={combo['k']}")
    else:
        print("No combos were extracted")
    
    return yaml_combos

def main():
    if len(sys.argv) < 2:
        print("Usage: python process_keymap.py <keymap_file> [output_file]")
        sys.exit(1)
    
    keymap_path = sys.argv[1]
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        output_path = os.path.join(os.path.dirname(keymap_path), "processed_keymap.keymap")
    
    print(f"Input file: {keymap_path}")
    print(f"Output file: {output_path}")
    
    base_dir = os.path.dirname(keymap_path)
    project_root = os.path.dirname(os.path.dirname(keymap_path))
    print(f"Base directory: {base_dir}")
    print(f"Project root: {project_root}")
    
    processed_keymap = process_keymap(keymap_path, output_path)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write the processed keymap to the output file
    with open(output_path, 'w') as f:
        f.write(processed_keymap)
    
    print(f"Processed keymap saved to {output_path}")
    
    print("\nNOTE: Combos are now processed directly within the Python script")
    
    # Extract layer definitions
    layer_defs_file = os.path.join(base_dir, "includes", "layers_definitions.dtsi")
    layer_definitions = extract_layer_definitions(layer_defs_file)
    
    # Extract key positions from ZMK key-labels header
    key_positions = {}
    try:
        # Try to find the key-labels file
        sofle_key_labels = os.path.join(project_root, "zmk-helpers", "include", "zmk-helpers", "key-labels", "sofle.h")
        if os.path.exists(sofle_key_labels):
            with open(sofle_key_labels, 'r') as f:
                content = f.read()
                key_positions = extract_key_positions(content)
                print(f"Extracted {len(key_positions)} key positions")
                print(f"Sample key positions: {list(key_positions.items())[:5]}")
        else:
            print(f"Key labels file not found at {sofle_key_labels}")
    except Exception as e:
        print(f"Error extracting key positions: {e}")
    
    if layer_definitions:
        print(f"Made {len(layer_definitions)} layer name replacements")
        print("\nLayer mapping:")
        for layer_name, layer_value in layer_definitions.items():
            print(f"Layer {layer_value}: {layer_name}")
    
    # Create the yaml config file path
    yaml_path = os.path.join(output_dir, "keymap.yaml")
    
    # Call keymap-drawer to generate the yaml config
    try:
        print("\nGenerating YAML configuration...")
        print("Using local keymap-drawer repository")
        
        # Parse processed keymap to yaml
        subprocess.run(["python", "-m", "keymap_drawer", "parse", "-z", output_path, "-o", yaml_path], check=True)
        
        # Update YAML layout to sofle
        print("\nUpdating YAML layout...")
        try:
            with open(yaml_path, 'r') as f:
                yaml_content = yaml.safe_load(f)
            
            if yaml_content and 'layout' in yaml_content:
                yaml_content['layout'] = {"zmk_keyboard": "sofle"}
                with open(yaml_path, 'w') as f:
                    yaml.dump(yaml_content, f, default_flow_style=False)
                    print(f"YAML written to: {yaml_path}")
                    
                # Verify file content after writing
                try:
                    with open(yaml_path, 'r') as f:
                        written_content = yaml.safe_load(f)
                        print("Written YAML content keys:", written_content.keys())
                except Exception as e:
                    print(f"Error verifying written YAML: {e}")
                print("Updated YAML layout to 'sofle'")
        except Exception as e:
            print(f"Error updating YAML layout: {e}")
            print("Continuing with default layout")
        
        # Extract combos from the processed keymap
        print("No combos found in the parsed output. Extracting combos from processed keymap...")
        combos_file = os.path.join(base_dir, "includes", "combos.dtsi")
        yaml_combos = process_combos(combos_file, key_positions, layer_definitions)
        
        # Add combos to the YAML file
        if yaml_combos:
            try:
                print(f"Processing {len(yaml_combos)} combos")
                print("Sample combos:", yaml_combos[:3])  # Show first 3 combos for verification
                
                with open(yaml_path, 'r') as f:
                    yaml_content = yaml.safe_load(f) or {}
                    print("Existing YAML content keys:", yaml_content.keys())
                
                # Ensure combos section exists and preserve any existing combos
                if 'combos' not in yaml_content:
                    print("Creating new combos section")
                    yaml_content['combos'] = []
                
                # Add new combos
                print(f"Adding {len(yaml_combos)} combos to YAML")
                yaml_content['combos'].extend(yaml_combos)
                
                # Write updated content
                with open(yaml_path, 'w') as f:
                    yaml.dump(yaml_content, f, default_flow_style=False)
                    print(f"YAML written to: {yaml_path}")
                    
                print("Combos successfully added to YAML file")
                print("Final YAML content keys:", yaml_content.keys())
            except Exception as e:
                print(f"Error adding combos to YAML: {e}")
                print("YAML content at time of error:", yaml_content)
        
        # Generate SVG visualization
        print("\nGenerating SVG visualization...")
        svg_output = os.path.join(project_root, "keymap.svg")
        config_file = os.path.join(os.path.dirname(output_dir), "keymap_drawer.config.yaml")
        
        if os.path.exists(config_file):
            print("\nMerging configuration settings into keymap.yaml...")
            try:
                # Load config file
                with open(config_file, 'r') as f:
                    config_content = yaml.safe_load(f)
                
                # Load the yaml file
                with open(yaml_path, 'r') as f:
                    yaml_content = yaml.safe_load(f)
                
                # Merge config settings into yaml_content
                if config_content and yaml_content:
                    # For each top-level key in config_content
                    for key, value in config_content.items():
                        if key not in yaml_content:
                            yaml_content[key] = value
                    
                    # Write the merged content back to the yaml file
                    with open(yaml_path, 'w') as f:
                        yaml.dump(yaml_content, f, default_flow_style=False)
                        print(f"YAML written to: {yaml_path}")
                        
                    # Verify file content after writing
                    try:
                        with open(yaml_path, 'r') as f:
                            written_content = yaml.safe_load(f)
                            print("Written YAML content keys:", written_content.keys())
                    except Exception as e:
                        print(f"Error verifying written YAML: {e}")
                
                print("Configuration settings merged successfully")
            except Exception as e:
                print(f"Error merging configuration settings: {e}")
        
        print("Using local keymap-drawer repository for drawing")
        subprocess.run(["python", "-m", "keymap_drawer", "draw", yaml_path, svg_output], check=True)
        
        print("\nSuccess! SVG visualization created.")
        
        print("\nDone! Generated files:")
        print(f"- Processed keymap: {output_path}")
        print(f"- YAML config: {yaml_path}")
        print(f"- SVG visualization: {svg_output}")
    
    except subprocess.CalledProcessError as e:
        print(f"Error calling keymap-drawer: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 
