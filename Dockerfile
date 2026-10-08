# Whop-first preparation with Remotion source video editing.

FROM python:3.11-slim

# System deps: Node.js 22 (Remotion), ffmpeg (video), git, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg ffmpeg git libnss3 libatk-bridge2.0-0 libgbm1 libasound2 libxrandr2 libxcomposite1 libxdamage1 libxfixes3 libcups2 fonts-liberation \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY orchestrator/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Node deps for Remotion (Editor agent)
COPY agents/editor/package*.json agents/editor/tsconfig.json ./agents/editor/
RUN cd agents/editor && npm ci --omit=dev && npx remotion browser ensure

# App code
COPY . .

# Env defaults (override in docker-compose or -e flags)
ENV PIPELINE_MODE=whop_first \
    RENDER_OUT=/app/out \
    PYTHONUNBUFFERED=1

VOLUME ["/app/out", "/app/data"]

CMD ["python", "-u", "orchestrator/main.py"]
