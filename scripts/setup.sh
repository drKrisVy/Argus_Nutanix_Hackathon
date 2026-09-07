#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env -- add your GROQ_API_KEY to it before running the dashboard."
fi

echo "Setup complete. Next: ./scripts/seed_demo.sh"
