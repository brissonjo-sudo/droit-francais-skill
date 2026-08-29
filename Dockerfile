FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_ENV=production \
    MCP_HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

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
