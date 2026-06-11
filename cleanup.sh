#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=== Stopping Manim Server ==="

echo "Stopping containers..."
for c in $(docker ps --filter "name=student-" --format "{{.Names}}"); do
    docker stop "$c" >/dev/null && docker rm "$c" >/dev/null
    echo "  stopped $c"
done

if [ -f .auth_pid ]; then
    kill "$(cat .auth_pid)" 2>/dev/null && echo "Auth server stopped"
    rm -f .auth_pid
fi

if [ -f .tunnel_pid ]; then
    kill "$(cat .tunnel_pid)" 2>/dev/null && echo "Cloudflare tunnel stopped"
    rm -f .tunnel_pid
fi

nginx -c "$(pwd)/nginx.conf" -s stop 2>/dev/null && echo "Nginx stopped" || true

rm -rf workspaces/
echo "Workspaces removed"

echo "=== Done ==="
