FROM python:3.14-alpine@sha256:05b2b8b732ecd268fee8727a369f936f022d1321b59befd13c30ede22769dcdc

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_ENV=production \
    MCP_HOST=0.0.0.0 \
    MCP_LOG_LEVEL=WARNING \
    PORT=8000

WORKDIR /app

# Le digest ci-dessus fige la base, mais il vieillit plus vite que les paquets
# Alpine : entre deux republications de l'image officielle, le digest épinglé
# traîne des CVE déjà corrigées en dépôt. Le pin sans cette montée a été essayé
# et rejeté par la porte Trivy (CVE-2026-14456, openssl 3.5.7-r0 → 3.5.8-r0).
# La couche est donc volontairement non reproductible bit à bit : c'est ce qui
# garantit qu'aucune CVE corrigeable ne survit à la construction. La porte
# Trivy de la CI reste l'autorité — elle scanne l'image après cette montée.
RUN apk upgrade --no-cache

RUN addgroup -S app && adduser -S -G app app

COPY requirements-mcp.txt ./
# pip et setuptools ne servent qu'à cette étape : l'image lancée n'exécute que
# `python mcp_server/server.py`, jamais pip. Les laisser en place laisse dans
# l'image un outillage que Trivy analyse — pip embarque ses propres dépendances
# vendorées — pour du code qui n'est jamais sur le chemin d'exécution. Les
# retirer supprime cette surface plutôt que d'avoir à en suivre les CVE. Pour
# déboguer dans le conteneur, reconstruire sans cette désinstallation.
RUN python -m pip install --no-cache-dir --requirement requirements-mcp.txt \
    && python -m pip uninstall --yes pip setuptools

COPY mcp_server/ ./mcp_server/
COPY skill/scripts/ ./skill/scripts/

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health', timeout=3).read()"]

CMD ["python", "mcp_server/server.py", "--transport", "streamable-http"]
