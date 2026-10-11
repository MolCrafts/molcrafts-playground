#!/bin/sh
# Build the static JupyterLite site.
# Locally this uses .venv when it already exists. On Cloudflare Pages there
# is no venv, so the script installs requirements.txt and then builds.
set -eu
cd "$(dirname "$0")/.."
if [ -x .venv/bin/jupyter ]; then
  PY=.venv/bin/python
  JUPYTER=.venv/bin/jupyter
else
  python3 -m pip install -r requirements.txt
  PY=python3
  JUPYTER="python3 -m jupyter"
fi
$JUPYTER lite build
$PY scripts/extend_lock.py
cp _headers dist/_headers
