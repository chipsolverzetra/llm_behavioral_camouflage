#!/usr/bin/env bash
# Run the full pilot pipeline end to end.
# Usage:
#   ./run_all.sh          # real run (needs API keys in .env)
#   DRY_RUN=1 ./run_all.sh   # wiring test, no API calls, no keys needed
set -euo pipefail
cd "$(dirname "$0")"

# Load .env if present
if [ -f .env ]; then set -a; . ./.env; set +a; fi

echo "=== STEP 1: camouflage generation ==="
python src/camouflage.py

echo "=== STEP 2: monitor evaluation ==="
python src/monitor.py

echo "=== STEP 3: scoring ==="
python src/score.py

echo "=== DONE. See results/ ==="
