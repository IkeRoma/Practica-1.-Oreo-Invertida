#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .build-venv
source .build-venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-client.txt pyinstaller
pyinstaller --noconfirm --clean Wasap.spec
mkdir -p dist/Wasap/config
[ -f dist/Wasap/config/client.env ] || cp config/client.env.example dist/Wasap/config/client.env
echo "Aplicacion generada en dist/Wasap/Wasap"
