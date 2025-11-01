#!/bin/bash
set -xeuo pipefail

# Install stress-ng for reproducible CPU load
amazon-linux-extras install epel -y || true
yum install -y stress-ng

# High Load: High 80% CPU load
# Validates power consumption model at high utilization
# Uses 2 CPU workers to simulate compute-intensive workloads
cat <<'SCRIPT' >/usr/local/bin/cpu-load.sh
#!/bin/bash
while true; do
  stress-ng --cpu 2 --cpu-load 80 --timeout 300s
  sleep 10
done
SCRIPT
chmod +x /usr/local/bin/cpu-load.sh

# Start CPU load in background
nohup /usr/local/bin/cpu-load.sh >/var/log/cpu-load.log 2>&1 &

echo "CPU 80% instance configured: Constant high load (2 workers)"
