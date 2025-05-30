from flask import Flask, jsonify
import subprocess
from datetime import datetime
import requests
import shlex

app = Flask(__name__)

NODES_FILE = "/tmp/nodes.list"
PROXIES_FILE = "/tmp/proxies.list"
INFLUXDB_URL = "http://localhost:8086/write?db=monitoring"

def check_node(ip, port=5000):
    ping_ok = subprocess.call(
        ["ping", "-c", "1", "-W", "2", ip],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ) == 0
    port_ok = subprocess.call(
        ["nc", "-z", "-w", "2", ip, str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ) == 0
    return ping_ok and port_ok

def send_to_influx(measurement, ip, status, extra_tags=None):
    tags = f"host={ip},type={measurement}"
    if extra_tags:
        tags += "," + ",".join(f"{k}={v}" for k, v in extra_tags.items())
    data = f"{measurement},{tags} value={int(status)}"
    try:
        requests.post(INFLUXDB_URL, data=data, timeout=2)
    except requests.RequestException as e:
        print(f"[InfluxDB] Failed to post {measurement} for {ip}: {e}")

@app.route("/health")
def health():
    now = datetime.now().isoformat()
    try:
        with open(NODES_FILE, "r") as f:
            ips = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return jsonify({
            "error": "Node list file not found",
            "healthy_nodes": [],
            "timestamp": now
        }), 404

    healthy_nodes = []
    for ip in ips:
        is_up = check_node(ip)
        send_to_influx("node_status", ip, is_up)
        if is_up:
            healthy_nodes.append(ip)

    return jsonify({
        "healthy_nodes": healthy_nodes,
        "timestamp": now
    })

@app.route("/proxy-health")
def proxy_health():
    now = datetime.now().isoformat()
    try:
        with open(PROXIES_FILE, "r") as f:
            ips = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return jsonify({
            "error": "Proxy list file not found",
            "proxies": [],
            "timestamp": now
        }), 404

    proxies_status = []
    for ip in ips:
        try:
            cmd = f"ssh -o BatchMode=yes -o ConnectTimeout=3 ubuntu@{ip} sudo cat /var/run/keepalived.state"
            proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=5)
            state = proc.stdout.strip().upper() if proc.returncode == 0 else "UNKNOWN"
        except Exception:
            state = "UNREACHABLE"

        proxies_status.append({"ip": ip, "status": state})
        send_to_influx("proxy_status", ip, 1 if state == "MASTER" else 0, extra_tags={"vrrp_state": state.lower()})

    return jsonify({
        "proxies": proxies_status,
        "timestamp": now
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=15000)
