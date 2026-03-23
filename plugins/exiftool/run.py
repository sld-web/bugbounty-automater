#!/usr/bin/env python3
"""ExifTool metadata extraction plugin."""
import argparse
import json
import subprocess
import sys
import os
from pathlib import Path

def extract_metadata(file_path: str, format: str = "json") -> dict:
    """Extract metadata using exiftool."""
    if not Path(file_path).exists():
        return {"error": f"File not found: {file_path}"}
    
    output_format = "-json" if format == "json" else "-short" if format == "short" else ""
    
    cmd = ["exiftool", output_format, file_path]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            if format == "json":
                try:
                    data = json.loads(result.stdout) if result.stdout.strip() else []
                    return {
                        "file": file_path,
                        "metadata": data,
                        "count": len(data) if isinstance(data, list) else 1,
                    }
                except json.JSONDecodeError:
                    return {
                        "file": file_path,
                        "metadata": result.stdout,
                        "format": format,
                    }
            else:
                return {
                    "file": file_path,
                    "output": result.stdout,
                    "format": format,
                }
        else:
            return {
                "error": "Exiftool failed",
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
    except subprocess.TimeoutExpired:
        return {"error": "Exiftool timed out", "file": file_path}
    except Exception as e:
        return {"error": str(e), "file": file_path}

def main():
    parser = argparse.ArgumentParser(description="ExifTool metadata extraction")
    parser.add_argument("--file", required=True, help="File to extract metadata from")
    parser.add_argument("--format", default="json", help="Output format: json, short, long")
    parser.add_argument("--params", help="JSON params")

    args = parser.parse_args()

    params = {}
    if args.params:
        params = json.loads(args.params)

    result = extract_metadata(
        file_path=args.file or params.get("file"),
        format=args.format or params.get("format", "json"),
    )

    print(json.dumps(result, indent=2))
    sys.exit(0 if "error" not in result else 1)

if __name__ == "__main__":
    main()
