#!/usr/bin/env python3
import json
import sys
import subprocess
import os

def run_amass(target: str, mode: str = "passive"):
    cmd = ["amass", "enum", "-"+mode[0], "-o", "/tmp/amass.txt", "-d", target]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        subdomains = []
        if os.path.exists("/tmp/amass.txt"):
            with open("/tmp/amass.txt") as f:
                subdomains = [line.strip() for line in f if line.strip()]
        
        return {
            "subdomains": subdomains,
            "domains": [target],
            "count": len(subdomains)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--mode", default="passive")
    args = parser.parse_args()
    
    result = run_amass(args.target, args.mode)
    print(json.dumps(result))
