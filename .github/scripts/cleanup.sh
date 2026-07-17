#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# cleanup.sh — Prune unused Docker images and build cache
# =============================================================================

echo "==> Pruning unused Docker images..."
docker image prune -f --filter "until=24h"

echo "==> Pruning build cache..."
docker builder prune -f --filter "until=24h" --keep-storage 5GB

echo "==> Cleanup complete."
