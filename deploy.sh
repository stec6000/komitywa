#!/bin/bash
set -e

echo "=== Deploying Kuchenna Komitywa ==="

# D-03: Create logs dir (idempotent, works on first and every deploy)
mkdir -p logs/

# Pull latest code
echo "Pulling latest code..."
git pull origin main

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
