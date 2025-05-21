from flask import Flask, jsonify
import os
import subprocess
from datetime import datetime

app = Flask(__name__)

NODES_FILE = "/tmp/nodes.list"

def check_node(ip):
    """Check if a node is healthy via ping and port check on 9103"""
    ping_ok = subprocess.call(["ping", "-c", "1", "-W", "2", ip],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    port_ok = subprocess.call(["nc", "-z", "-w", "2", ip, "9103"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    return ping_ok and port_ok

@app.route("/health")
def health():
    try:
        with open(NODES_FILE, "r") as f:
            ips = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return jsonify({
            "error": "Node list file not found",
            "healthy_nodes": [],
            "timestamp": datetime.now().isoformat()
        })

    healthy_nodes = []
    for ip in ips:
        if check_node(ip):
            healthy_nodes.append(ip)

    return jsonify({
        "healthy_nodes": healthy_nodes,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
