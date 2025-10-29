#!/bin/bash
set -xeuo pipefail

# Install stress-ng for reproducible CPU load
amazon-linux-extras install epel -y || true
yum install -y stress-ng

# Variable Load: Alternates between 30% and 70% CPU
# This simulates dev/test environments with fluctuating workloads
# Validates the power consumption model under variable conditions
cat <<'SCRIPT' >/usr/local/bin/cpu-load.sh
#!/bin/bash
while true; do
  # Low phase: 30% CPU for 10 minutes
  stress-ng --cpu 1 --cpu-load 30 --timeout 600s
  sleep 30

  # High phase: 70% CPU for 10 minutes
  stress-ng --cpu 1 --cpu-load 70 --timeout 600s
  sleep 30
done
SCRIPT
chmod +x /usr/local/bin/cpu-load.sh

# Start CPU load in background
nohup /usr/local/bin/cpu-load.sh >/var/log/cpu-load.log 2>&1 &

echo "Variable load instance configured: 30-70% CPU alternating (10min cycles)"
