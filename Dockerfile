FROM python:3.11-slim AS builder

LABEL org.opencontainers.image.source=https://github.com/doraemon-code/doraemon
LABEL org.opencontainers.image.description="Doraemon Code - AI Assistant powered by MCP"
LABEL org.opencontainers.image.licenses=MIT

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache-dir .

COPY src/ ./src/

RUN mkdir -p /app/.agent

RUN groupadd -r doraemon && useradd -r -g doraemon -m doraemon
RUN chown -R doraemon:doraemon /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

USER doraemon

ENTRYPOINT ["dora"]
CMD ["start"]
