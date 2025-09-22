#!/bin/bash
set -xeuo pipefail

amazon-linux-extras install epel -y || true
yum install -y stress-ng

# Dynamic workload alternating between high and low load
cat <<'SCRIPT' >/usr/local/bin/cpu-load.sh
#!/bin/bash
while true; do
  # High burst ~70%
  stress-ng --cpu 1 --cpu-load 70 --timeout 120s
  sleep 30
  # Low phase ~20%
  stress-ng --cpu 1 --cpu-load 20 --timeout 180s
  sleep 15
done
SCRIPT
chmod +x /usr/local/bin/cpu-load.sh

nohup /usr/local/bin/cpu-load.sh >/var/log/cpu-load.log 2>&1 &
