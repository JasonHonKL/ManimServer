#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=== Manim Server ==="

command -v docker >/dev/null 2>&1 || { echo "Error: docker is required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is required"; exit 1; }
command -v nginx >/dev/null 2>&1 || { echo "Error: nginx is required"; exit 1; }

pip3 install -q fastapi uvicorn pyyaml httpx 2>/dev/null || true

IMAGE=$(python3 -c "import yaml; print(yaml.safe_load(open('config.yml'))['image'])")
AUTH_PORT=$(python3 -c "import yaml; print(yaml.safe_load(open('config.yml'))['auth_port'])")

echo "Pulling $IMAGE..."
docker pull "$IMAGE"

echo "Initializing..."
python3 init.py

if [ -f .auth_pid ]; then
    kill "$(cat .auth_pid)" 2>/dev/null || true
fi

echo "Starting auth server on :$AUTH_PORT..."
uvicorn auth_server:app --host 127.0.0.1 --port "$AUTH_PORT" &
echo $! > .auth_pid
sleep 1

echo "Starting nginx..."
nginx -s stop 2>/dev/null || true
sleep 0.5
nginx -c "$(pwd)/nginx.conf"

echo ""
echo "=== Ready! ==="
echo "Open http://<YOUR_EC2_PUBLIC_IP>/ in a browser"
echo "Stop with: ./cleanup.sh"
echo "Reset a locked room: curl -X POST http://localhost:$AUTH_PORT/reset/student-01"
