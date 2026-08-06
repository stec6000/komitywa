#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Deploying Kuchenna Komitywa ==="

# D-03: Create logs dir (idempotent, works on first and every deploy)
mkdir -p logs/

# Synchronize the production checkout with the exact commit from origin/main.
# The checkout may contain a local commit from a manual server-side deploy;
# keep a recoverable pointer to it before replacing the working tree.
echo "Synchronizing latest code..."
git fetch origin main

LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse origin/main)"

if [ "$LOCAL_SHA" != "$REMOTE_SHA" ]; then
  BACKUP_BRANCH="deploy-backup-$(date -u +%Y%m%d%H%M%S)-${LOCAL_SHA:0:12}"
  git branch "$BACKUP_BRANCH" "$LOCAL_SHA"
  echo "Saved previous production commit as $BACKUP_BRANCH ($LOCAL_SHA)."
fi

git reset --hard origin/main

# Activate virtualenv
source ~/.virtualenvs/komitywa/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# D-02: Clear stale bytecode (prevents Passenger from serving old .pyc)
echo "Clearing bytecode cache..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Restart application via MyDevil
echo "Restarting application..."
devil www restart kuchennakomitywa.pl

echo "=== Deploy complete ==="
