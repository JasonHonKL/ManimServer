FROM manimcommunity/manim:stable

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    HOME=/root curl -fsSL https://opencode.ai/install | HOME=/root bash -s -- --no-modify-path && \
    mv /root/.opencode/bin/opencode /usr/local/bin/opencode && \
    rm -rf /root/.opencode && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
