#!/usr/bin/env bash
# Ensure an active AWS SSO session for a given profile; triggers login when expired.
set -euo pipefail

PROFILE="${1:-${AWS_PROFILE:-default}}"

if aws sts get-caller-identity --profile "${PROFILE}" >/dev/null 2>&1; then
  exit 0
fi

echo "AWS SSO session for profile '${PROFILE}' is expired. Running 'aws sso login'."
aws sso login --profile "${PROFILE}"

aws sts get-caller-identity --profile "${PROFILE}" >/dev/null
