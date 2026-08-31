FROM python:3.12-slim@sha256:09f7da3bc104798d0afb40bc08d23ab2da20a76130cec1f2ef170848f5d85217

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_ENV=production \
    MCP_HOST=0.0.0.0 \
    MCP_LOG_LEVEL=WARNING \
    PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get upgrade --yes \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements-mcp.txt ./
RUN python -m pip install --no-cache-dir --requirement requirements-mcp.txt

COPY mcp_server/ ./mcp_server/
COPY skill/scripts/ ./skill/scripts/

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health', timeout=3).read()"]

CMD ["python", "mcp_server/server.py", "--transport", "streamable-http"]
