#!/bin/bash
set -xeuo pipefail

amazon-linux-extras install epel -y || true
yum install -y stress-ng

# High workload ≈80%
cat <<'SCRIPT' >/usr/local/bin/cpu-load.sh
#!/bin/bash
while true; do
  stress-ng --cpu 2 --cpu-load 80 --timeout 240s
  sleep 5
done
SCRIPT
chmod +x /usr/local/bin/cpu-load.sh

nohup /usr/local/bin/cpu-load.sh >/var/log/cpu-load.log 2>&1 &
