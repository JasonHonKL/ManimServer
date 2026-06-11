# HKU Manim Workshop Server

Each student gets their own isolated JupyterLab environment with Manim + OpenCode pre-installed. Students enter their name, get routed to their personal workspace, and the room stays locked to them.

## Architecture

```
Student Browser
    │
    ▼
 Cloudflare Tunnel (free HTTPS)
    │
    ▼
 Nginx (:8080)
    │
    ├── GET /            → Landing page (name input)
    ├── GET /assign      → Name → room assignment, set cookie
    ├── GET /admin       → Admin dashboard (password protected)
    └── GET /s/{id}/**   → auth_request → proxy to student container
                              │
              Auth Server (:9000)
              Cookie-based room locking
                              │
              student-01  :8001  (0.5 CPU / 1GB RAM)
              student-02  :8002
              ...
              student-NN  :80NN
```

## How It Works

### Student Flow

1. Student opens the public URL (via Cloudflare Tunnel)
2. Enters their name on the landing page
3. System maps name → room (same name always gets same room)
4. A cookie `manim_name` is set in their browser
5. Every request is authenticated: cookie must match the room's owner
6. They get a full JupyterLab with Manim + LaTeX + ffmpeg + OpenCode
7. If they come back later, the landing page shows "Welcome back"

### Name-Based Room Assignment

- Names map to rooms deterministically — "Alice" always gets the same room
- First time: student enters name → gets next available room
- Returning: student enters name → gets their existing room
- "Not you?" button clears the cookie and frees the room

### Admin Dashboard

- Accessible at `/admin` with HTTP Basic Auth
- Password set in `config.yml` (`admin_password`)
- Shows all rooms, student names, and assignment times
- Auto-refreshes every 15 seconds

## Quick Start (Local Testing)

```bash
# Make sure Docker Desktop is running
docker info

# Run everything
./setup.sh

# Open
open http://localhost:8080/
# Admin dashboard
open http://localhost:8080/admin   (user: admin, password: workshop2024)

# Stop
./cleanup.sh
```

## EC2 Deployment

### 1. Launch Instance

- **Type:** m5.xlarge or larger (4+ vCPU, 16+ GB RAM)
- **OS:** Ubuntu 22.04 LTS
- **Disk:** 30GB gp3
- **Security Group:** Allow inbound TCP 22 (SSH) — port 80 not needed!

### 2. Upload & Run

```bash
scp -i your-key.pem -r ./manim-server ubuntu@<EC2_PUBLIC_IP>:/home/ubuntu/
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>

cd /home/ubuntu/manim-server
chmod +x setup.sh cleanup.sh

# Before running, edit config.yml:
#   num_students: 60
#   admin_password: "your-secure-password"

# Place your notebooks in data/

# One command to rule them all:
./setup.sh
```

The script installs Docker, Nginx, Python deps, Cloudflare Tunnel, builds the Docker image with OpenCode, creates workspaces, and starts everything. At the end it prints:
- **Public URL** (Cloudflare Tunnel)
- **Admin URL** + password

### 3. Give Students the URL

Just share the `https://xxx.trycloudflare.com` URL from the output.

## Managing the Workshop

```bash
# Reset a locked room
curl -X POST http://localhost:9000/reset/student-01

# Check container status
sudo docker ps --filter "name=student-" --format "table {{.Names}}\t{{.Status}}"

# View logs for a specific student
sudo docker logs student-01

# Restart a single container
sudo docker restart student-01
```

## Ending the Workshop

```bash
./cleanup.sh
```

This stops all containers, kills auth server + nginx + Cloudflare tunnel, and removes all student workspaces. Then terminate the EC2 instance.

## Configuration

```yaml
# config.yml
num_students: 60          # Number of student workspaces
cpu: "0.5"                # CPU per container
memory: "1g"              # RAM per container
base_port: 8001           # Starting port for containers
auth_port: 9000           # Auth server port
nginx_port: 8080          # Nginx port
image: "manim-server-student"  # Custom Docker image name
data_dir: "data"          # Notebooks to copy to each student
workspaces_dir: "workspaces"   # Runtime copies (gitignored)
admin_password: "workshop2024" # Admin dashboard password
```

## Files

| File | Purpose |
|------|---------|
| `config.yml` | Number of students, resource limits, ports, admin password |
| `setup.sh` | One-command setup from scratch (Ubuntu + AWS) |
| `Dockerfile` | Extends manim image with opencode CLI |
| `init.py` | Copies data, spawns containers, generates nginx.conf |
| `auth_server.py` | Landing page, name→room, cookie auth, admin dashboard |
| `cleanup.sh` | Stops everything, removes workspaces |
| `data/` | Place notebooks here — copied into each workspace |

## Troubleshooting

```bash
# Test nginx config
nginx -t -c $(pwd)/nginx.conf

# Test the auth endpoint directly
curl -v -b "manim_name=Alice" http://localhost:9000/auth/student-01

# Check nginx error log
cat /tmp/manim-server-nginx-error.log

# Check auth server output
cat /tmp/manim-auth.log

# Check tunnel log
cat /tmp/manim-tunnel.log
```
