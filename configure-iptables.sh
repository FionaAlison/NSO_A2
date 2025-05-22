#!/bin/bash
set -e

TARGET_IP="192.168.42.100"
PORT="5000"

# Add DNAT rule if it doesn't exist
iptables -t nat -C PREROUTING -p tcp --dport "$PORT" -j DNAT --to-destination "$TARGET_IP:$PORT" 2>/dev/null \
  || iptables -t nat -A PREROUTING -p tcp --dport "$PORT" -j DNAT --to-destination "$TARGET_IP:$PORT"

# Add FORWARD rule if it doesn't exist
iptables -C FORWARD -p tcp -d "$TARGET_IP" --dport "$PORT" -j ACCEPT 2>/dev/null \
  || iptables -A FORWARD -p tcp -d "$TARGET_IP" --dport "$PORT" -j ACCEPT

# Ensure iptables-persistent is installed
if ! dpkg -l | grep -q iptables-persistent; then
  apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent
fi

# Save rules
iptables-save > /etc/iptables/rules.v4
