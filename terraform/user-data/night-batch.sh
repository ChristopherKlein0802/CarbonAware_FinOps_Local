#!/bin/bash
set -xeuo pipefail

# Install stress-ng for reproducible CPU load
amazon-linux-extras install epel -y || true
yum install -y stress-ng

# Night Batch: High 80% CPU load (simulates batch processing)
# This represents compute-intensive jobs that can be scheduled
# during low-carbon grid times (Solar/Wind peaks: 22-6h)
# Uses 2 CPU workers for xlarge instance
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

echo "Night batch instance configured: 80% CPU load (2 workers)"
echo "Note: Manual start/stop or EventBridge rules needed for night-only schedule (22-6h)"
