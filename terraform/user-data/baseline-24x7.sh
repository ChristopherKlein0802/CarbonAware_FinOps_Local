#!/bin/bash
set -xeuo pipefail

# Install stress-ng for reproducible CPU load
amazon-linux-extras install epel -y || true
yum install -y stress-ng

# Baseline: Constant 40% CPU load (simulates always-on database)
# This represents critical infrastructure that runs 24/7
cat <<'SCRIPT' >/usr/local/bin/cpu-load.sh
#!/bin/bash
while true; do
  stress-ng --cpu 1 --cpu-load 40 --timeout 300s
  sleep 10
done
SCRIPT
chmod +x /usr/local/bin/cpu-load.sh

# Start CPU load in background
nohup /usr/local/bin/cpu-load.sh >/var/log/cpu-load.log 2>&1 &

echo "Baseline 24x7 instance configured: 40% CPU load"
