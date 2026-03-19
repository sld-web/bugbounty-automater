#!/usr/bin/env python3
"""Nuclei plugin entrypoint."""
import argparse
import json
import subprocess
import sys


def run_nuclei(
    target: str,
    templates: str = "templates",
    severity: list[str] | None = None,
    rate_limit: int = 150,
) -> dict:
    """Run Nuclei vulnerability scan."""
    output_file = "/tmp/nuclei_results.jsonl"
    cmd = [
        "nuclei",
        "-u", target,
        "-json", "-o", output_file,
        "-rl", str(rate_limit),
    ]

    if templates:
        if " " in templates:
            cmd.extend(["-tags", templates])
        else:
            cmd.extend(["-t", templates])

    if severity:
        cmd.extend(["-severity", ",".join(severity)])

    print(f"Running: {' '.join(cmd)}")

    findings = []
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,
        )

        if result.returncode in (0, 1):
            if sys.path.exists(output_file):
                with open(output_file) as f:
                    for line in f:
                        try:
                            finding = json.loads(line.strip())
                            findings.append({
                                "template": finding.get("template-id"),
                                "name": finding.get("info", {}).get("name"),
                                "severity": finding.get("info", {}).get("severity"),
                                "matched_at": finding.get("matched-at"),
                                "extracted_results": finding.get("extracted-results", []),
                                "curl_command": finding.get("curl-command"),
                            })
                        except json.JSONDecodeError:
                            continue

        return {
            "findings": findings,
            "count": len(findings),
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:2000],
            "exit_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "findings": findings,
            "count": len(findings),
            "error": "Nuclei timed out",
            "exit_code": -1,
        }
    except Exception as e:
        return {
            "findings": [],
            "error": str(e),
            "exit_code": -1,
        }


def main():
    parser = argparse.ArgumentParser(description="Nuclei vulnerability scanning")
    parser.add_argument("--target", required=True, help="Target URL")
    parser.add_argument("--templates", default="templates", help="Templates")
    parser.add_argument("--severity", nargs="+", help="Severity levels")
    parser.add_argument("--rate-limit", type=int, default=150, help="Rate limit")
    parser.add_argument("--params", help="JSON params")

    args = parser.parse_args()

    params = {}
    if args.params:
        params = json.loads(args.params)

    result = run_nuclei(
        target=args.target,
        templates=args.templates or params.get("templates", "templates"),
        severity=args.severity or params.get("severity"),
        rate_limit=args.rate_limit or params.get("rate_limit", 150),
    )

    print(json.dumps(result, indent=2))
    sys.exit(result.get("exit_code", 0))


if __name__ == "__main__":
    main()
