#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-client.txt
python3 -m PyInstaller --noconfirm --clean --windowed --onedir --name Wasap --paths client --collect-all keyring client/main.py
mkdir -p dist/Wasap/config
cp config/client.env.example dist/Wasap/config/client.env.example
if [[ "$(uname -s)" == "Darwin" && -d "dist/Wasap.app" ]]; then
  mkdir -p "dist/Wasap.app/Contents/MacOS/config"
  cp config/client.env.example "dist/Wasap.app/Contents/MacOS/config/client.env.example"
  printf '\nCompilación terminada. Configura Wasap.app/Contents/MacOS/config/client.env.\n'
else
  printf '\nCompilación terminada. Configura dist/Wasap/config/client.env y ejecuta dist/Wasap/Wasap.\n'
fi
