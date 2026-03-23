#!/usr/bin/env python3
"""OWASP ZAP plugin entrypoint."""
import argparse
import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional

ZAP_CLI_PATHS = [
    "/opt/ZAP_2.12.0/zap.sh",
    "/opt/zap/zap.sh",
    "/zap/zap.sh",
    os.path.expanduser("~/ZAP_2.12.0/zap.sh"),
]

def find_zap():
    """Find ZAP installation."""
    for path in ZAP_CLI_PATHS:
        if Path(path).exists():
            return path
    
    zap_home = os.environ.get("ZAP_HOME")
    if zap_home:
        zap_sh = Path(zap_home) / "zap.sh"
        if zap_sh.exists():
            return str(zap_sh)
    
    if Path("/zap/zap.sh").exists():
        return "/zap/zap.sh"
    
    return None

def run_zap_spider(target: str) -> dict:
    """Run ZAP spider scan."""
    zap_path = find_zap()
    
    if not zap_path:
        return {
            "error": "ZAP not found",
            "message": "ZAP CLI not installed. Install from: https://www.zaproxy.org/download/",
            "target": target,
        }
    
    output_file = "/tmp/zap_spider_out.json"
    cmd = [
        zap_path,
        "-cmd",
        "-quickurl", target,
        "-quickout", output_file,
        "-spider"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        
        return {
            "status": "completed",
            "target": target,
            "mode": "spider",
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:2000],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": "ZAP spider timed out", "target": target}
    except Exception as e:
        return {"error": str(e), "target": target}

def run_zap_baseline(target: str) -> dict:
    """Run ZAP baseline scan."""
    zap_path = find_zap()
    
    if not zap_path:
        return {
            "error": "ZAP not found",
            "message": "ZAP CLI not installed. Install from: https://www.zaproxy.org/download/",
            "target": target,
        }
    
    report_file = "/tmp/zap_baseline_report.html"
    cmd = [
        zap_path,
        "-cmd",
        "-quickurl", target,
        "-quickout", report_file,
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=900,
        )
        
        return {
            "status": "completed",
            "target": target,
            "mode": "baseline",
            "report_file": report_file if Path(report_file).exists() else None,
            "stdout": result.stdout[:5000],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": "ZAP baseline timed out", "target": target}
    except Exception as e:
        return {"error": str(e), "target": target}

def main():
    parser = argparse.ArgumentParser(description="OWASP ZAP scanner")
    parser.add_argument("--target", required=True, help="Target URL")
    parser.add_argument("--scan_mode", default="baseline", help="Scan mode: baseline, full, api, spider")
    parser.add_argument("--spider", type=bool, default=True, help="Run spider first")
    parser.add_argument("--params", help="JSON params")

    args = parser.parse_args()

    params = {}
    if args.params:
        params = json.loads(args.params)

    scan_mode = args.scan_mode or params.get("scan_mode", "baseline")
    
    if scan_mode == "spider":
        result = run_zap_spider(args.target)
    else:
        result = run_zap_baseline(args.target)

    print(json.dumps(result, indent=2))
    sys.exit(0 if "error" not in result else 1)

if __name__ == "__main__":
    main()
