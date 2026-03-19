#!/usr/bin/env python3
"""Amass plugin entrypoint."""
import argparse
import json
import subprocess
import sys
import os


def run_amass(target: str, mode: str = "passive", wordlist: str | None = None) -> dict:
    """Run Amass enumeration."""
    output_file = "/tmp/amass_results.json"
    cmd = [
        "amass",
        "enum",
        "-passive" if mode == "passive" else "-active",
        "-d", target,
        "-json", output_file,
    ]

    if wordlist and os.path.exists(wordlist):
        cmd.extend(["-w", wordlist])

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,
        )

        subdomains = []
        if os.path.exists(output_file):
            with open(output_file) as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if "name" in data:
                            subdomains.append(data["name"])
                    except json.JSONDecodeError:
                        continue

        return {
            "subdomains": list(set(subdomains)),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "subdomains": [],
            "error": "Amass timed out",
            "exit_code": -1,
        }
    except Exception as e:
        return {
            "subdomains": [],
            "error": str(e),
            "exit_code": -1,
        }


def main():
    parser = argparse.ArgumentParser(description="Amass subdomain enumeration")
    parser.add_argument("--target", required=True, help="Target domain")
    parser.add_argument("--mode", default="passive", help="Scan mode")
    parser.add_argument("--wordlist", help="Wordlist path")
    parser.add_argument("--params", help="JSON params")

    args = parser.parse_args()

    params = {}
    if args.params:
        params = json.loads(args.params)

    result = run_amass(
        target=args.target,
        mode=args.mode or params.get("mode", "passive"),
        wordlist=args.wordlist or params.get("wordlist"),
    )

    print(json.dumps(result, indent=2))
    sys.exit(result.get("exit_code", 0))


if __name__ == "__main__":
    main()
