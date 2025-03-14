#!/usr/bin/env python3
"""
Script to find and document unused code in the Archimedius project.
Uses Vulture to identify potentially unused code and generates a report.
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def run_vulture(min_confidence=60, exclude=None):
    """
    Run Vulture on the project and return the results.
    
    Args:
        min_confidence: Minimum confidence level (0-100)
        exclude: List of directories or files to exclude
        
    Returns:
        List of dictionaries with unused code information
    """
    exclude_args = []
    if exclude:
        exclude_args = ["--exclude", ",".join(exclude)]
    
    cmd = ["vulture", ".", "--min-confidence", str(min_confidence)] + exclude_args
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        
        unused_code = []
        for line in lines:
            if not line:
                continue
                
            # Parse Vulture output format: file.py:line: unused X 'name' (confidence%)
            parts = line.split(": ", 1)
            if len(parts) != 2:
                continue
                
            file_line, message = parts
            file_parts = file_line.split(":")
            if len(file_parts) != 2:
                continue
                
            filename, line_num = file_parts
            
            # Extract confidence level
            confidence = 0
            if "confidence" in message:
                confidence_str = message.split("(")[1].split("%")[0]
                try:
                    confidence = int(confidence_str)
                except ValueError:
                    pass
            
            # Extract type and name
            type_name = None
            name = None
            
            if "unused variable" in message:
                type_name = "variable"
                name = message.split("unused variable ")[1].split(" (")[0].strip("'")
            elif "unused function" in message:
                type_name = "function"
                name = message.split("unused function ")[1].split(" (")[0].strip("'")
            elif "unused method" in message:
                type_name = "method"
                name = message.split("unused method ")[1].split(" (")[0].strip("'")
            elif "unused class" in message:
                type_name = "class"
                name = message.split("unused class ")[1].split(" (")[0].strip("'")
            elif "unused import" in message:
                type_name = "import"
                name = message.split("unused import ")[1].split(" (")[0].strip("'")
            elif "unused attribute" in message:
                type_name = "attribute"
                name = message.split("unused attribute ")[1].split(" (")[0].strip("'")
            
            if name and type_name:
                unused_code.append({
                    "file": filename,
                    "line": int(line_num),
                    "type": type_name,
                    "name": name,
                    "confidence": confidence,
                    "message": message
                })
        
        return unused_code
    
    except subprocess.CalledProcessError as e:
        print(f"Error running Vulture: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def generate_report(unused_code, output_file=None):
    """
    Generate a report of unused code.
    
    Args:
        unused_code: List of dictionaries with unused code information
        output_file: File to write the report to (optional)
    """
    if not unused_code:
        print("No unused code found.")
        return
    
    # Group by file
    by_file = {}
    for item in unused_code:
        filename = item["file"]
        if filename not in by_file:
            by_file[filename] = []
        by_file[filename].append(item)
    
    # Sort by confidence level (highest first)
    for filename, items in by_file.items():
        by_file[filename] = sorted(items, key=lambda x: x["confidence"], reverse=True)
    
    # Generate report
    report = []
    report.append("# Unused Code Report")
    report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("## Summary")
    report.append("")
    
    # Count by type
    type_counts = {}
    for item in unused_code:
        type_name = item["type"]
        type_counts[type_name] = type_counts.get(type_name, 0) + 1
    
    for type_name, count in sorted(type_counts.items()):
        report.append(f"- {count} unused {type_name}{'s' if count != 1 else ''}")
    
    report.append("")
    report.append("## Details")
    
    # Add details by file
    for filename, items in sorted(by_file.items()):
        report.append("")
        report.append(f"### {filename}")
        report.append("")
        report.append("| Line | Type | Name | Confidence |")
        report.append("|------|------|------|------------|")
        
        for item in items:
            report.append(f"| {item['line']} | {item['type']} | `{item['name']}` | {item['confidence']}% |")
    
    report_text = "\n".join(report)
    
    if output_file:
        with open(output_file, "w") as f:
            f.write(report_text)
        print(f"Report written to {output_file}")
    else:
        print(report_text)
    
    # Also save as JSON for programmatic use
    if output_file:
        json_file = output_file.replace(".md", ".json")
        with open(json_file, "w") as f:
            json.dump(unused_code, f, indent=2)
        print(f"JSON data written to {json_file}")

def main():
    """Main function."""
    min_confidence = 60
    exclude = ["venv", "__pycache__", ".git"]
    output_file = "unused_code_report.md"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        min_confidence = int(sys.argv[1])
    
    print(f"Finding unused code with minimum confidence of {min_confidence}%...")
    unused_code = run_vulture(min_confidence, exclude)
    generate_report(unused_code, output_file)

if __name__ == "__main__":
    main() 