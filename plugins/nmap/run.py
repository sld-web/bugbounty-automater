#!/usr/bin/env python3
"""Nmap plugin entrypoint."""
import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET


def parse_nmap_xml(xml_output: str) -> list[dict]:
    """Parse Nmap XML output."""
    ports = []

    try:
        root = ET.fromstring(xml_output)
        for host in root.findall(".//host"):
            for port in host.findall(".//port"):
                port_id = port.get("portid")
                protocol = port.get("protocol")
                state = port.find("state")
                service = port.find("service")

                port_info = {
                    "port": int(port_id) if port_id else 0,
                    "protocol": protocol or "tcp",
                    "state": state.get("state") if state is not None else "unknown",
                    "service": service.get("name") if service is not None else "unknown",
                    "product": service.get("product") if service is not None else None,
                    "version": service.get("version") if service is not None else None,
                }

                ports.append(port_info)

    except ET.ParseError as e:
        print(f"Failed to parse XML: {e}", file=sys.stderr)

    return ports


def parse_nmap_text(stdout: str) -> list[dict]:
    """Parse nmap text output as fallback."""
    ports = []
    for line in stdout.split("\n"):
        if "/tcp" in line or "/udp" in line:
            parts = line.split()
            if len(parts) >= 3:
                port_proto = parts[0].split("/")
                ports.append({
                    "port": int(port_proto[0]),
                    "protocol": port_proto[1] if len(port_proto) > 1 else "tcp",
                    "state": parts[1],
                    "service": parts[2] if len(parts) > 2 else "unknown",
                })
    return ports


def run_nmap(target: str, ports: str = "-T4 -F") -> dict:
    """Run Nmap scan."""
    output_file = "/tmp/nmap_results.xml"
    cmd = ["nmap", "-oX", output_file]

    if ports == "-T4 -F":
        cmd.extend(["-T4", "-F"])
    elif ports.startswith("-"):
        cmd.extend(ports.split())
    else:
        cmd.extend(["-p", ports])

    cmd.append(target)

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )

        ports_found = []
        if result.returncode in (0, 1):
            if os.path.exists(output_file):
                try:
                    with open(output_file) as f:
                        ports_found = parse_nmap_xml(f.read())
                except Exception:
                    pass
            if not ports_found and "PORT" in result.stdout:
                ports_found = parse_nmap_text(result.stdout)

        return {
            "ports": ports_found,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "ports": [],
            "error": "Nmap timed out",
            "exit_code": -1,
        }
    except Exception as e:
        return {
            "ports": [],
            "error": str(e),
            "exit_code": -1,
        }


def main():
    parser = argparse.ArgumentParser(description="Nmap port scanning")
    parser.add_argument("--target", required=True, help="Target IP or hostname")
    parser.add_argument("--ports", default="-T4 -F", help="Port specification")
    parser.add_argument("--params", help="JSON params")

    args = parser.parse_args()

    params = {}
    if args.params:
        params = json.loads(args.params)

    result = run_nmap(
        target=args.target,
        ports=args.ports or params.get("ports", "-T4 -F"),
    )

    print(json.dumps(result, indent=2))
    sys.exit(result.get("exit_code", 0))


if __name__ == "__main__":
    main()
