from flask import Flask, jsonify
import subprocess
from datetime import datetime

app = Flask(__name__)

NODES_FILE = "/tmp/nodes.list"
PROXIES_FILE = "/tmp/proxies.list"

def check_node(ip, port=5000):
    """Check if a node/proxy is reachable by ping + port check."""
    ping_ok = subprocess.call(
        ["ping", "-c", "1", "-W", "2", ip],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ) == 0
    port_ok = subprocess.call(
        ["nc", "-z", "-w", "2", ip, str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ) == 0
    return ping_ok and port_ok

@app.route("/health")
def health():
    """Check health of service nodes"""
    try:
        with open(NODES_FILE, "r") as f:
            ips = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return jsonify({
            "error": "Node list file not found",
            "healthy_nodes": [],
            "timestamp": datetime.now().isoformat()
        }), 404

    healthy_nodes = [ip for ip in ips if check_node(ip, port=5000)]

    return jsonify({
        "healthy_nodes": healthy_nodes,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/proxy-health")
def proxy_health():
    """Check health/status of proxy nodes by checking VRRP status via SSH"""
    try:
        with open(PROXIES_FILE, "r") as f:
            ips = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return jsonify({
            "error": "Proxy list file not found",
            "proxies": [],
            "timestamp": datetime.now().isoformat()
        }), 404

    proxies_status = []

    for ip in ips:
        # Instead of ping + port, here check VRRP state remotely
        # This requires SSH access, assumes ssh keys & permissions configured on bastion
        try:
            # Run 'ip -brief addr show dev ens3' or 'vrrp-script' or check keepalived state on proxy
            # Example: use 'ssh' to check keepalived state via a remote script or command
            import shlex
            import subprocess

            cmd = f"ssh -o BatchMode=yes -o ConnectTimeout=3 ubuntu@{ip} sudo cat /var/run/keepalived.state"
            proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=5)
            state = proc.stdout.strip().upper() if proc.returncode == 0 else "UNKNOWN"
        except Exception:
            state = "UNREACHABLE"

        proxies_status.append({"ip": ip, "status": state})

    return jsonify({
        "proxies": proxies_status,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=15000)
