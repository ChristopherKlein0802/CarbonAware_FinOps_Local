#!/bin/bash
set -xeuo pipefail

amazon-linux-extras install epel -y || true
yum install -y stress-ng

# Medium workload ≈40%
cat <<'SCRIPT' >/usr/local/bin/cpu-load.sh
#!/bin/bash
while true; do
  stress-ng --cpu 1 --cpu-load 40 --timeout 180s
  sleep 10
done
SCRIPT
chmod +x /usr/local/bin/cpu-load.sh

nohup /usr/local/bin/cpu-load.sh >/var/log/cpu-load.log 2>&1 &
