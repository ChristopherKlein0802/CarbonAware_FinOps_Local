#!/bin/bash
set -xeuo pipefail

# Ensure stress-ng is available
amazon-linux-extras install epel -y || true
yum install -y stress-ng

# Create low-load workload (≈10%)
cat <<'SCRIPT' >/usr/local/bin/cpu-load.sh
#!/bin/bash
while true; do
  stress-ng --cpu 1 --cpu-load 10 --timeout 120s
  sleep 15
done
SCRIPT
chmod +x /usr/local/bin/cpu-load.sh

nohup /usr/local/bin/cpu-load.sh >/var/log/cpu-load.log 2>&1 &
