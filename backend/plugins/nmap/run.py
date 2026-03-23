#!/usr/bin/env python3
import json
import sys
import subprocess
import xml.etree.ElementTree as ET
import os

def run_nmap(target: str, ports: str = None):
    output_file = "/tmp/nmap.xml"
    cmd = ["nmap", "-oX", output_file, "-p-"]
    
    if ports:
        cmd[2] = f"-p{ports}"
    
    cmd.append(target)
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        
        open_ports = []
        if os.path.exists(output_file):
            tree = ET.parse(output_file)
            root = tree.getroot()
            
            for port in root.iter("port"):
                state = port.find("state")
                if state is not None and state.get("state") == "open":
                    open_ports.append({
                        "port": port.get("portid"),
                        "protocol": port.get("protocol"),
                        "service": port.find("service").get("name") if port.find("service") is not None else "unknown"
                    })
        
        return {
            "open_ports": open_ports,
            "count": len(open_ports)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--ports", default=None)
    args = parser.parse_args()
    
    result = run_nmap(args.target, args.ports)
    print(json.dumps(result))
