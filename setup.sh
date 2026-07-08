#!/usr/bin/env bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

echo ""
echo -e "${BOLD}═══════════════════════════════════════════${NC}"
echo -e "${BOLD}  HKU Manim Workshop — Setup${NC}"
echo -e "${BOLD}═══════════════════════════════════════════${NC}"
echo ""

# ── Detect OS ──────────────────────────────────────────────
if [ "$(uname)" = "Darwin" ]; then
    OS="macos"
    echo -e "  OS:        ${CYAN}macOS${NC}"
    DOCKER_CMD="docker"
    SUDO=""
else
    OS="linux"
    echo -e "  OS:        ${CYAN}Linux${NC}"
    DOCKER_CMD="sudo docker"
    SUDO="sudo"
    export DOCKER_CMD
fi

# ── [1/7] Python environment (uv + venv) ───────────────────
echo ""
echo -e "${BOLD}[1/7] Python environment${NC}"
if ! command -v uv >/dev/null 2>&1; then
    echo "  Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "  Creating virtual environment..."
uv venv "$BASE_DIR/.venv"
PY="$BASE_DIR/.venv/bin/python"
echo "  Installing Python packages..."
uv pip install --python "$PY" -r "$BASE_DIR/requirements.txt"
echo -e "  ${GREEN}✓${NC} Virtual environment ready"

# ── Read config ────────────────────────────────────────────
IMAGE=$($PY -c "import yaml; print(yaml.safe_load(open('config.yml'))['image'])")
AUTH_PORT=$($PY -c "import yaml; print(yaml.safe_load(open('config.yml'))['auth_port'])")
NGINX_PORT=$($PY -c "import yaml; print(yaml.safe_load(open('config.yml'))['nginx_port'])")
ADMIN_PW=$($PY -c "import yaml; print(yaml.safe_load(open('config.yml'))['admin_password'])")

# ── [2/7] Install Docker ───────────────────────────────────
echo ""
echo -e "${BOLD}[2/7] Docker${NC}"
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Docker is running"
elif [ "$OS" = "linux" ]; then
    echo "  Installing Docker..."
    $SUDO apt-get update -qq
    $SUDO apt-get install -y -qq docker.io
    $SUDO systemctl enable docker
    $SUDO systemctl start docker
    $SUDO usermod -aG docker "$USER"
    # docker won't work without sudo until next login, but sudo docker works
    DOCKER_CMD="sudo docker"
    echo -e "  ${GREEN}✓${NC} Docker installed (using sudo for this session)"
else
    echo -e "  ${RED}✗${NC} Please open Docker Desktop first, then re-run this script."
    exit 1
fi

# ── [3/7] Install Nginx ────────────────────────────────────
echo ""
echo -e "${BOLD}[3/7] Nginx${NC}"
if command -v nginx >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Nginx found"
else
    echo "  Installing nginx..."
    if [ "$OS" = "linux" ]; then
        $SUDO apt-get install -y -qq nginx
    else
        brew install nginx 2>/dev/null || true
    fi
    echo -e "  ${GREEN}✓${NC} Nginx installed"
fi

# ── [4/7] Install Cloudflared ──────────────────────────────
echo ""
echo -e "${BOLD}[4/7] Cloudflare Tunnel${NC}"
if command -v cloudflared >/dev/null 2>&1 && cloudflared --version >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} cloudflared found"
else
    if command -v cloudflared >/dev/null 2>&1; then
        echo "  Reinstalling cloudflared (existing binary is broken/wrong arch)..."
        $SUDO rm -f /usr/local/bin/cloudflared 2>/dev/null || true
    else
        echo "  Installing cloudflared..."
    fi
    case "$(uname -m)" in
        x86_64|amd64)  ARCH="amd64" ;;
        aarch64|arm64) ARCH="arm64" ;;
        armv7l)        ARCH="arm"   ;;
        *) echo -e "  ${RED}✗${NC} Unsupported architecture: $(uname -m)"; exit 1 ;;
    esac
    if [ "$OS" = "linux" ]; then
        CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}"
        $SUDO curl -fsSL "$CLOUDFLARED_URL" -o /usr/local/bin/cloudflared
        $SUDO chmod +x /usr/local/bin/cloudflared
    else
        brew install cloudflared 2>/dev/null || {
            CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-${ARCH}"
            $SUDO curl -fsSL "$CLOUDFLARED_URL" -o /usr/local/bin/cloudflared
            $SUDO chmod +x /usr/local/bin/cloudflared
        }
    fi
    echo -e "  ${GREEN}✓${NC} cloudflared installed"
fi

# ── [5/7] Build Docker image ───────────────────────────────
echo ""
echo -e "${BOLD}[5/7] Docker image${NC}"
echo -e "  Pulling base image and installing opencode..."
# Always rebuild to get the latest opencode
$DOCKER_CMD build -t "$IMAGE" -f "$BASE_DIR/Dockerfile" "$BASE_DIR"
echo -e "  ${GREEN}✓${NC} Image built: ${CYAN}${IMAGE}${NC}"

# ── [6/7] Initialize workspaces ────────────────────────────
echo ""
echo -e "${BOLD}[6/7] Initialize workspaces${NC}"
# Stop any existing containers first
for c in $($DOCKER_CMD ps --filter "name=student-" --format "{{.Names}}" 2>/dev/null); do
    $DOCKER_CMD stop "$c" >/dev/null 2>&1
    $DOCKER_CMD rm "$c" >/dev/null 2>&1
    echo "  cleaned up old container: $c"
done
$PY init.py

# ── [7/7] Start services ───────────────────────────────────
echo ""
echo -e "${BOLD}[7/7] Start services${NC}"

# Stop any prior instances
if [ -f .auth_pid ]; then
    kill "$(cat .auth_pid)" 2>/dev/null || true
fi
if [ -f .tunnel_pid ]; then
    kill "$(cat .tunnel_pid)" 2>/dev/null || true
    rm -f .tunnel_pid
fi
nginx -c "$BASE_DIR/nginx.conf" -s stop 2>/dev/null || true
# Fallback: kill anything still bound to the nginx port
lsof -ti :"$NGINX_PORT" 2>/dev/null | xargs kill 2>/dev/null || true
sleep 1

# Start auth server
echo "  Starting auth server on :$AUTH_PORT..."
$PY -m uvicorn auth_server:app --host 127.0.0.1 --port "$AUTH_PORT" > /tmp/manim-auth.log 2>&1 &
echo $! > .auth_pid
sleep 1
echo -e "  ${GREEN}✓${NC} Auth server running"

# Clear all room assignments from any previous session
curl -sf -X POST "http://localhost:$AUTH_PORT/reset-all" >/dev/null 2>&1 && echo "  ${GREEN}✓${NC} All rooms cleared" || true

# Start nginx
echo "  Starting nginx on :$NGINX_PORT..."
nginx -c "$BASE_DIR/nginx.conf"
echo -e "  ${GREEN}✓${NC} Nginx running"

# Start Cloudflare tunnel
echo "  Starting Cloudflare tunnel..."
cloudflared tunnel --protocol http2 --url "http://localhost:$NGINX_PORT" > /tmp/manim-tunnel.log 2>&1 &
echo $! > .tunnel_pid
echo "  Waiting for tunnel URL..."
TUNNEL_URL=""
for i in $(seq 1 15); do
    sleep 1
    TUNNEL_URL=$(grep -o 'https://[^ ]*trycloudflare\.com' /tmp/manim-tunnel.log 2>/dev/null | head -1) || true
    if [ -n "$TUNNEL_URL" ]; then
        break
    fi
done

# ── Done ───────────────────────────────────────────────────
echo ""
echo -e "${BOLD}═══════════════════════════════════════════${NC}"
echo -e "${BOLD}  Ready!${NC}"
echo -e "${BOLD}═══════════════════════════════════════════${NC}"
echo ""

if [ -n "$TUNNEL_URL" ]; then
    echo -e "  ${BOLD}Public URL:${NC}   ${GREEN}${TUNNEL_URL}/${NC}"
else
    echo -e "  Tunnel may still be initializing. Check:"
    echo -e "    ${CYAN}cat /tmp/manim-tunnel.log${NC}"
    echo ""
    echo -e "  ${BOLD}Local URL:${NC}    http://localhost:${NGINX_PORT}/"
fi

echo -e "  ${BOLD}Admin:${NC}        http://localhost:${NGINX_PORT}/admin"
echo -e "  ${BOLD}Password:${NC}     ${CYAN}${ADMIN_PW}${NC}"
echo ""
echo -e "  Stop:     ${CYAN}./cleanup.sh${NC}"
echo -e "  Reset:    ${CYAN}curl -X POST http://localhost:${AUTH_PORT}/reset/student-01${NC}"
echo ""
