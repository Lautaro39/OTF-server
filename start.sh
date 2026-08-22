#!/bin/bash
set -e

echo "[INFO] Setting up Django Server (OTF-server)..."

# Find or create venv
if [ -d "venv" ]; then
    VENV_PATH="venv"
    echo "[INFO] Found virtual environment: 'venv'"
elif [ -d ".venv" ]; then
    VENV_PATH=".venv"
    echo "[INFO] Found virtual environment: '.venv'"
else
    echo "[INFO] Creating virtual environment 'venv'..."
    python3 -m venv venv
    VENV_PATH="venv"
fi

# Install requirements
echo "[INFO] Installing python requirements..."
"$VENV_PATH/bin/pip" install --upgrade pip
"$VENV_PATH/bin/pip" install -r requirements.txt

cd backend_otf

# Migrate and Seed
echo "[INFO] Running database migrations..."
"../$VENV_PATH/bin/python" manage.py migrate

echo "[INFO] Seeding database categories and states..."
"../$VENV_PATH/bin/python" manage.py seed

if [ -f "seed_comunidad.py" ]; then
    echo "[INFO] Seeding community notices and events..."
    "../$VENV_PATH/bin/python" seed_comunidad.py
fi

echo "[SUCCESS] Django Server setup complete!"
echo "[INFO] Starting Django Server on 0.0.0.0:8000..."

# Start Django development server
"../$VENV_PATH/bin/python" manage.py runserver 0.0.0.0:8000
