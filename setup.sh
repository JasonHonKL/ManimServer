#!/usr/bin/env bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}═══════════════════════════════════════════${NC}"
echo -e "${BOLD}  HKU Manim Workshop — Setup${NC}"
echo -e "${BOLD}═══════════════════════════════════════════${NC}"
echo ""

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

# ── Detect OS ──────────────────────────────────────────────
if [ "$(uname)" = "Darwin" ]; then
    OS="macos"
    echo -e "  OS:        ${CYAN}macOS${NC}"
else
    OS="linux"
    echo -e "  OS:        ${CYAN}Linux (EC2)${NC}"
fi

# ── Check / Install Docker ─────────────────────────────────
echo ""
echo -e "${BOLD}[1/6] Docker${NC}"
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Docker is running"
else
    echo -e "  Docker not found or not running. Installing..."
    if [ "$OS" = "linux" ]; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq docker.io >/dev/null
        sudo systemctl enable docker
        sudo systemctl start docker
        sudo usermod -aG docker "$USER"
        echo -e "  ${GREEN}✓${NC} Docker installed"
        echo ""
        echo -e "  ${RED}⚠  Docker added you to the docker group.${NC}"
        echo -e "  ${RED}   Run this command, then re-run ./setup.sh:${NC}"
        echo ""
        echo -e "     newgrp docker"
        echo ""
        echo -e "  Or log out and SSH back in."
        exit 0
    else
        echo -e "  ${RED}✗${NC} Please open Docker Desktop first, then re-run this script."
        exit 1
    fi
fi

# ── Check / Install Nginx ──────────────────────────────────
echo ""
echo -e "${BOLD}[2/6] Nginx${NC}"
if command -v nginx >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Nginx is installed"
else
    echo -e "  Installing nginx..."
    if [ "$OS" = "linux" ]; then
        sudo apt-get install -y -qq nginx >/dev/null
    else
        brew install nginx >/dev/null 2>&1
    fi
    echo -e "  ${GREEN}✓${NC} Nginx installed"
fi

# ── Check / Install Python packages ────────────────────────
echo ""
echo -e "${BOLD}[3/6] Python dependencies${NC}"
PIP_INSTALL="no"
for pkg in fastapi uvicorn pyyaml; do
    python3 -c "import $pkg" 2>/dev/null || PIP_INSTALL="yes"
done
if [ "$PIP_INSTALL" = "yes" ]; then
    echo -e "  Installing fastapi, uvicorn, pyyaml..."
    pip3 install -q fastapi uvicorn pyyaml 2>/dev/null || pip install -q fastapi uvicorn pyyaml
    echo -e "  ${GREEN}✓${NC} Python packages installed"
else
    echo -e "  ${GREEN}✓${NC} All Python packages present"
fi

# ── Pull Docker image ──────────────────────────────────────
IMAGE=$(python3 -c "import yaml; print(yaml.safe_load(open('config.yml'))['image'])")
echo ""
echo -e "${BOLD}[4/6] Pulling Docker image${NC}"
echo -e "  ${CYAN}${IMAGE}${NC}"
docker pull "$IMAGE"
echo -e "  ${GREEN}✓${NC} Image ready"

# ── Initialize ─────────────────────────────────────────────
echo ""
echo -e "${BOLD}[5/6] Creating workspaces & containers${NC}"
python3 init.py

# ── Start services ─────────────────────────────────────────
AUTH_PORT=$(python3 -c "import yaml; print(yaml.safe_load(open('config.yml'))['auth_port'])")
NGINX_PORT=$(python3 -c "import yaml; print(yaml.safe_load(open('config.yml'))['nginx_port'])")

if [ -f .auth_pid ]; then
    kill "$(cat .auth_pid)" 2>/dev/null || true
fi

echo ""
echo -e "${BOLD}[6/6] Starting services${NC}"
python3 -m uvicorn auth_server:app --host 127.0.0.1 --port "$AUTH_PORT" > /tmp/manim-auth.log 2>&1 &
echo $! > .auth_pid
sleep 1

nginx -s stop 2>/dev/null || true
sleep 0.5
nginx -c "$BASE_DIR/nginx.conf"
echo -e "  ${GREEN}✓${NC} Auth server + Nginx running"

# ── Get public IP ──────────────────────────────────────────
PUBLIC_IP=""
if [ "$OS" = "linux" ]; then
    PUBLIC_IP=$(curl -s --connect-timeout 3 http://checkip.amazonaws.com 2>/dev/null || true)
fi

# ── Done ───────────────────────────────────────────────────
echo ""
echo -e "${BOLD}═══════════════════════════════════════════${NC}"
echo -e "${BOLD}  Ready!${NC}"
echo -e "${BOLD}═══════════════════════════════════════════${NC}"
echo ""
if [ -n "$PUBLIC_IP" ]; then
    echo -e "  Students open:  ${GREEN}http://${PUBLIC_IP}/${NC}"
else
    echo -e "  Students open:  ${GREEN}http://localhost:${NGINX_PORT}/${NC}"
fi
echo ""
echo -e "  Stop:     ${CYAN}./cleanup.sh${NC}"
echo -e "  Reset:    ${CYAN}curl -X POST http://localhost:${AUTH_PORT}/reset/student-01${NC}"
echo ""
