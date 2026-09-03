#!/bin/bash
set -euo pipefail

# N'installe rien hors de Claude Code sur le web : en local, le
# développeur gère son propre environnement Python.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# --ignore-installed contourne le conflit avec PyJWT posé par le paquet
# système Debian (sans métadonnées pip récupérables) : `pip install` seul
# échoue en tentant de le désinstaller. Voir requirements-mcp.txt pour le
# détail des versions figées.
python -m pip install --ignore-installed -r requirements-mcp.txt
