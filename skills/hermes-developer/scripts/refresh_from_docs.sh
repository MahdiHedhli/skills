#!/usr/bin/env bash
# Refresh hermes-developer skill references from local Hermes docs checkout.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/refresh_from_docs.py" "$@"
