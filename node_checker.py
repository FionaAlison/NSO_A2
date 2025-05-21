#!/usr/bin/python3
import subprocess
import time
import requests
import os
import json

def get_nodes_from_inventory():
    """Read node IPs from Ansible-generated inventory file"""
    inventory_path = "/etc/ansible/hosts"
    try:
        with open(inventory_path) as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('[')]
        return [line.split()[1].split('=')[1] for line in lines if 'ansible_host' in line]
    except Exception as e:
        print(f"Error reading inventory: {e}")
        return []

def check_node(node_ip):
    try:
        subprocess.check_call(
            ["ping", "-c", "1", "-W", "1", node_ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

if __name__ == "__main__":
    # Get nodes from environment variable (set by Ansible)
    NODE_IPS = os.getenv('NODE_IPS', '').split(',')
    if not NODE_IPS or NODE_IPS == ['']:
        NODE_IPS = get_nodes_from_inventory()
    
    INFLUXDB_URL = "http://localhost:8086"
    
    while True:
        for ip in NODE_IPS:
            if not ip:  # Skip empty entries
                continue
                
            status = check_node(ip)
            try:
                requests.post(
                    f"{INFLUXDB_URL}/write?db=monitoring",
                    data=f"node_status,host={ip} value={int(status)}",
                    timeout=1
                )
            except requests.RequestException as e:
                print(f"Failed to send metrics for {ip}: {e}")
        
        time.sleep(30)  # Matches project's 30s check requirement