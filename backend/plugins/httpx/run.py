#!/usr/bin/env python3
import json
import sys
import subprocess
import os

def run_httpx(targets: list):
    with open("/tmp/hosts.txt", "w") as f:
        f.write("\n".join(targets))
    
    cmd = ["httpx", "-l", "/tmp/hosts.txt", "-o", "/tmp/httpx.json", "-silent", "-json"]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        results = []
        if os.path.exists("/tmp/httpx.json"):
            with open("/tmp/httpx.json") as f:
                for line in f:
                    try:
                        results.append(json.loads(line.strip()))
                    except:
                        pass
        
        return {
            "live_hosts": results,
            "count": len(results)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", required=True)
    args = parser.parse_args()
    
    targets = args.targets.split(",")
    result = run_httpx(targets)
    print(json.dumps(result))
