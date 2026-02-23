FROM ubuntu:24.04

# ── Environment ───────────────────────────────────────────────────────────────
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC \
    GOPATH=/go \
    IS_SANDBOX=1 \
    PATH="/usr/local/go/bin:/go/bin:/root/.local/bin:$PATH"

# ── Version pins (bump here to upgrade) ──────────────────────────────────────
ARG GO_VERSION=1.26.0
ARG YQ_VERSION=4.52.4
ARG HYPERFINE_VERSION=1.20.0
ARG NODE_MAJOR=24

# ── Base system packages ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash-completion \
    build-essential \
    ca-certificates \
    curl \
    git \
    gnupg \
    iproute2 \
    iputils-ping \
    jq \
    less \
    lsb-release \
    make \
    nano \
    openssh-client \
    procps \
    software-properties-common \
    sudo \
    tmux \
    tree \
    unzip \
    vim \
    wget \
    zip \
    && rm -rf /var/lib/apt/lists/*

# ── Python 3 (full stack) ────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    python3-full \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# ── Go ────────────────────────────────────────────────────────────────────────
RUN curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" \
    | tar -C /usr/local -xz \
    && mkdir -p /go/bin /go/src /go/pkg

# ── GitHub CLI ────────────────────────────────────────────────────────────────
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# ── Docker CLI (uses host Docker socket mounted at /var/run/docker.sock) ──────
RUN install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y \
        docker-buildx-plugin \
        docker-ce-cli \
        docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

# ── Node.js (LTS) ─────────────────────────────────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# ── Claude Code — native installer (standalone binary) ────────────────────────
RUN curl -fsSL https://claude.ai/install.sh | bash

# ── ripgrep + fd (used by Claude Code internals) ─────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ripgrep \
    fd-find \
    && ln -sf /usr/bin/fdfind /usr/local/bin/fd \
    && rm -rf /var/lib/apt/lists/*

# ── yq (YAML processor) ───────────────────────────────────────────────────────
RUN curl -fsSL "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64" \
    -o /usr/local/bin/yq \
    && chmod +x /usr/local/bin/yq

# ── hyperfine (benchmarking harness) ─────────────────────────────────────────
RUN curl -fsSL \
    "https://github.com/sharkdp/hyperfine/releases/download/v${HYPERFINE_VERSION}/hyperfine_${HYPERFINE_VERSION}_amd64.deb" \
    -o /tmp/hyperfine.deb \
    && dpkg -i /tmp/hyperfine.deb \
    && rm /tmp/hyperfine.deb

# ── Python global packages ────────────────────────────────────────────────────
RUN pip3 install --break-system-packages \
    httpx \
    pandas \
    pytest \
    pytest-asyncio \
    pyyaml \
    rich \
    ruff \
    typer

# ── Go toolchain ──────────────────────────────────────────────────────────────
RUN go install golang.org/x/tools/gopls@latest \
    && go install github.com/go-delve/delve/cmd/dlv@latest \
    && go install mvdan.cc/gofumpt@latest

# ── Shell config ──────────────────────────────────────────────────────────────
RUN echo 'export PATH="/usr/local/go/bin:/go/bin:/root/.local/bin:$PATH"' >> /root/.bashrc \
    && echo 'export GOPATH=/go' >> /root/.bashrc \
    && echo 'export IS_SANDBOX=1' >> /root/.bashrc \
    && echo '. /usr/share/bash-completion/bash_completion' >> /root/.bashrc

WORKDIR /workspace
CMD ["sleep", "infinity"]
