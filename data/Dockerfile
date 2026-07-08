FROM manimcommunity/manim:v0.17.3

USER root
RUN pip install notebook

# Tools needed by the opencode installer
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG NB_USER=manimuser
USER ${NB_USER}
ENV HOME=/home/${NB_USER}
ENV PATH=${HOME}/.opencode/bin:${PATH}

# Install opencode (the AI coding agent used in Chapter 5)
RUN curl -fsSL https://opencode.ai/install | bash

COPY --chown=manimuser:manimuser . /manim
