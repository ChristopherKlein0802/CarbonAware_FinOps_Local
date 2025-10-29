#!/bin/bash
set -xeuo pipefail

# Install stress-ng for reproducible CPU load
amazon-linux-extras install epel -y || true
yum install -y stress-ng

# Office-Hours: Constant 60% CPU load (simulates business application)
# In production, this instance would be stopped outside Mo-Fr 8-18h
# For testing purposes, it runs 24/7 but with office-hours-typical load
cat <<'SCRIPT' >/usr/local/bin/cpu-load.sh
#!/bin/bash
while true; do
  stress-ng --cpu 1 --cpu-load 60 --timeout 300s
  sleep 10
done
SCRIPT
chmod +x /usr/local/bin/cpu-load.sh

# Start CPU load in background
nohup /usr/local/bin/cpu-load.sh >/var/log/cpu-load.log 2>&1 &

echo "Office-hours instance configured: 60% CPU load"
echo "Note: Manual start/stop or EventBridge rules needed for true office-hours schedule"
