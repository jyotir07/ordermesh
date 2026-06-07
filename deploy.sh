#!/usr/bin/env bash
# One-shot deploy/update script. Run from the repo root on the server:
#
#   ./deploy.sh
#
# It pulls the latest code, rebuilds images, and brings the stack up with the
# production overlay (Caddy + private data services). Re-run it any time you push
# new commits to redeploy.
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "ERROR: .env not found. Copy .env.example to .env and set production secrets first." >&2
  exit 1
fi

echo "==> Pulling latest code"
git pull --ff-only

echo "==> Building and starting the stack"
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "==> Pruning dangling images"
docker image prune -f >/dev/null 2>&1 || true

echo "==> Current status"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

echo "==> Done. Tail logs with:"
echo "    docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
