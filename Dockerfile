FROM manimcommunity/manim:stable

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -fsSL https://opencode.ai/install | bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
