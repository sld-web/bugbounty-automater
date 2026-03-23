#!/usr/bin/env python3
import json
import sys
import subprocess
import os

def run_nuclei(target: str, severity: list = None):
    output_file = "/tmp/nuclei.jsonl"
    cmd = ["nuclei", "-u", target, "-o", output_file, "-json", "-silent"]
    
    if severity:
        cmd.extend(["-severity", ",".join(severity)])
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        
        findings = []
        if os.path.exists(output_file):
            with open(output_file) as f:
                for line in f:
                    try:
                        findings.append(json.loads(line.strip()))
                    except:
                        pass
        
        return {
            "findings": findings,
            "count": len(findings)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--severity", default=None)
    args = parser.parse_args()
    
    severity = args.severity.split(",") if args.severity else None
    result = run_nuclei(args.target, severity)
    print(json.dumps(result))
