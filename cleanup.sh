#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=== Stopping Manim Server ==="

# Detect sudo usage (mirror setup.sh: use sudo on Linux)
if [ "$(uname)" = "Darwin" ]; then
    DOCKER_CMD="docker"
    SUDO=""
else
    DOCKER_CMD="sudo docker"
    SUDO="sudo"
fi

# Use the venv python if present, else fall back to system python3
if [ -f ./.venv/bin/python ]; then
    PY="./.venv/bin/python"
else
    PY="python3"
fi

echo "Stopping containers..."
for c in $($DOCKER_CMD ps --filter "name=student-" --format "{{.Names}}"); do
    $DOCKER_CMD stop "$c" >/dev/null && $DOCKER_CMD rm "$c" >/dev/null
    echo "  stopped $c"
done

# Kill auth server by PID file or by port
if [ -f .auth_pid ]; then
    kill "$(cat .auth_pid)" 2>/dev/null && echo "Auth server stopped"
    rm -f .auth_pid
fi
# Also kill any lingering process on the auth port
AUTH_PORT=$($PY -c "import yaml; print(yaml.safe_load(open('config.yml'))['auth_port'])" 2>/dev/null || echo 9000)
lsof -ti :"$AUTH_PORT" 2>/dev/null | xargs kill 2>/dev/null || true

# Kill ALL cloudflared tunnel processes (orphaned tunnels cause Cloudflare 530)
pkill -f "cloudflared tunnel" 2>/dev/null && echo "Cloudflare tunnel(s) stopped" || true
rm -f .tunnel_pid

nginx -c "$(pwd)/nginx.conf" -s stop 2>/dev/null && echo "Nginx stopped" || true

# Workspaces contain files created by Docker (owned by root), so use sudo on Linux
$SUDO rm -rf workspaces/
echo "Workspaces removed"

echo "=== Done ==="
