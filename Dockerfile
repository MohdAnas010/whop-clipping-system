# Whop Clipping Autonomous Agent System - Free/Open Source Docker Image
# Runs on any VPS (USA IP) with Docker. 100% free stack: Ollama + open source models.

FROM python:3.11-slim

# System deps: Node.js 20 (Remotion), ffmpeg (video), git, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg ffmpeg git \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY orchestrator/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Node deps for Remotion (Editor agent)
COPY agents/editor/package.json ./agents/editor/package.json
RUN cd agents/editor && npm install --omit=dev 2>/dev/null || cd agents/editor && npm install

# App code
COPY . .

# Env defaults (override in docker-compose or -e flags)
ENV OLLAMA_HOST=http://ollama:11434 \
    OLLAMA_MODEL=qwen2.5:7b \
    WHOP_API_KEY="" \
    RENDER_OUT=/app/out \
    PYTHONUNBUFFERED=1

VOLUME ["/app/out", "/app/data"]

CMD ["python", "-u", "orchestrator/main.py"]
