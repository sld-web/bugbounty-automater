#!/usr/bin/env python3
"""Subfinder plugin entrypoint."""
import argparse
import json
import subprocess
import sys


def run_subfinder(
    target: str,
    sources: list[str] | None = None,
    use_all: bool = True,
) -> dict:
    """Run Subfinder subdomain discovery."""
    output_file = "/tmp/subfinder_results.txt"
    cmd = [
        "subfinder",
        "-d", target,
        "-o", output_file,
    ]

    if use_all:
        cmd.append("-all")
    elif sources:
        cmd.extend(["-sources", ",".join(sources)])

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )

        subdomains = []
        if result.returncode == 0 and sys.path.exists(output_file):
            with open(output_file) as f:
                subdomains = [line.strip() for line in f if line.strip()]

        return {
            "subdomains": list(set(subdomains)),
            "count": len(subdomains),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "subdomains": [],
            "error": "Subfinder timed out",
            "exit_code": -1,
        }
    except Exception as e:
        return {
            "subdomains": [],
            "error": str(e),
            "exit_code": -1,
        }


def main():
    parser = argparse.ArgumentParser(description="Subfinder subdomain discovery")
    parser.add_argument("--target", required=True, help="Target domain")
    parser.add_argument("--sources", nargs="+", help="Specific sources")
    parser.add_argument("--all", action="store_true", default=True, help="Use all sources")
    parser.add_argument("--params", help="JSON params")

    args = parser.parse_args()

    params = {}
    if args.params:
        params = json.loads(args.params)

    result = run_subfinder(
        target=args.target,
        sources=args.sources or params.get("sources"),
        use_all=args.all if hasattr(args, "all") else params.get("all", True),
    )

    print(json.dumps(result, indent=2))
    sys.exit(result.get("exit_code", 0))


if __name__ == "__main__":
    main()
