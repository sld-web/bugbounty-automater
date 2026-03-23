#!/usr/bin/env python3
import json
import sys
import subprocess

def run_subfinder(target: str):
    cmd = ["subfinder", "-d", target, "-o", "/tmp/subfinder.txt", "-silent"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        
        subdomains = []
        if os.path.exists("/tmp/subfinder.txt"):
            with open("/tmp/subfinder.txt") as f:
                subdomains = [line.strip() for line in f if line.strip()]
        
        return {
            "subdomains": subdomains,
            "count": len(subdomains)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    
    result = run_subfinder(args.target)
    print(json.dumps(result))
