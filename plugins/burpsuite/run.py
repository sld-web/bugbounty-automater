#!/usr/bin/env python3
"""BurpSuite plugin entrypoint - wrapper for local BurpSuite CLI."""
import argparse
import json
import subprocess
import sys
import os
from pathlib import Path

BURPSUITE_CLI_PATHS = [
    "/opt/BurpSuitePro/burpsuite_pro.jar",
    "/opt/BurpSuite/BurpSuitePro.jar",
    os.path.expanduser("~/BurpSuitePro/BurpSuitePro.jar"),
    os.path.expanduser("~/.burp/burpsuite_pro.jar"),
]

def find_burpsuite():
    """Find BurpSuite installation."""
    for path in BURPSUITE_CLI_PATHS:
        if Path(path).exists():
            return path
    
    burp_home = os.environ.get("BURPSUITE_HOME")
    if burp_home and Path(burp_home).exists():
        jar = Path(burp_home) / "burpsuite_pro.jar"
        if jar.exists():
            return str(jar)
    
    return None

def run_spider(target: str) -> dict:
    """Run basic spider scan."""
    return {
        "status": "local_tool",
        "message": "Configure BurpSuite path in settings for automated scanning",
        "target": target,
        "instructions": [
            "1. Open BurpSuite locally",
            "2. Configure proxy to point to target",
            "3. Use Spider to crawl the application",
            "4. Run Active Scan for vulnerability detection",
            "5. Export findings as JSON"
        ]
    }

def run_basic_scan(target: str, scan_type: str = "light") -> dict:
    """Run BurpSuite scan."""
    burpsuite_path = find_burpsuite()
    
    if not burpsuite_path:
        return {
            "error": "BurpSuite not found",
            "message": "Please install BurpSuite and set BURPSUITE_HOME or configure path",
            "target": target,
            "scan_type": scan_type,
        }
    
    return {
        "status": "ready",
        "burpsuite_path": burpsuite_path,
        "target": target,
        "scan_type": scan_type,
        "message": "BurpSuite found - automated scanning requires BurpSuite Professional with CLI"
    }

def main():
    parser = argparse.ArgumentParser(description="BurpSuite web vulnerability scanner")
    parser.add_argument("--target", required=True, help="Target URL")
    parser.add_argument("--scan_type", default="light", help="Scan type: light, medium, deep")
    parser.add_argument("--proxy_port", type=int, default=8080, help="Proxy port")
    parser.add_argument("--params", help="JSON params")

    args = parser.parse_args()

    params = {}
    if args.params:
        params = json.loads(args.params)

    result = run_basic_scan(
        target=args.target,
        scan_type=args.scan_type or params.get("scan_type", "light"),
    )

    print(json.dumps(result, indent=2))
    sys.exit(0 if "error" not in result else 1)

if __name__ == "__main__":
    main()
