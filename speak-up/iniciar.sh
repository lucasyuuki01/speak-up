#!/usr/bin/env bash
# Speak Up - inicia o site no Linux/macOS:  bash iniciar.sh
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt && echo "Abra: http://127.0.0.1:5000" && python3 app.py
