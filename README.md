# HKU Manim Workshop Server

Each student gets their own isolated JupyterLab environment with Manim pre-installed. One button to join, auto-assigned room, IP-locked for the session.

## Architecture

```
Student Browser
    │
    ▼
 Nginx (:80)
    │
    ├── GET /            → Landing page (one button)
    ├── GET /assign       → Auto-assign room, redirect to Jupyter
    └── GET /s/{id}/**   → auth_request → proxy to student container
                                      │
                          Auth Server (:9000)
                          IP-lock: first IP to visit a room owns it
                                      │
                          student-01  :8001  (0.5 CPU / 1GB RAM)
                          student-02  :8002
                          ...
                          student-60  :8060
```

## Files

| File | Purpose |
|------|---------|
| `config.yml` | Number of students, resource limits, ports |
| `start.sh` | One-command startup (installs deps, pulls image, runs init, starts services) |
| `init.py` | Copies `data/` per student, spawns containers, generates nginx.conf |
| `auth_server.py` | Landing page, auto-assign room, IP-lock per room |
| `cleanup.sh` | Stops everything, removes workspaces |
| `data/` | Place your notebooks here — they get copied to each student |
| `workspaces/` | Per-student copies (created at runtime, gitignored) |

## EC2 Setup

### 1. Launch Instance

- **Type:** `m5.8xlarge` (32 vCPU, 128GB RAM)
- **OS:** Ubuntu 22.04 LTS
- **Disk:** 30GB gp3
- **Security Group:** Allow inbound TCP 80 from 0.0.0.0/0

### 2. SSH In & Install

```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>

sudo apt update && sudo apt install -y docker.io nginx python3-pip
sudo systemctl enable docker && sudo systemctl start docker
sudo usermod -aG docker ubuntu
pip3 install fastapi uvicorn pyyaml

# Log out and back in so docker group takes effect
exit
```

### 3. Upload Project

From your **local machine**:

```bash
scp -i your-key.pem -r /path/to/manim-server ubuntu@<EC2_PUBLIC_IP>:/home/ubuntu/manim-server
```

### 4. Configure

Edit `config.yml` on the server:

```yaml
num_students: 60        # adjust to your class size
cpu: "0.5"
memory: "1g"
base_port: 8001
auth_port: 9000
nginx_port: 80          # must be 80 on EC2 (1024+ on macOS)
image: "manimcommunity/manim:stable"
data_dir: "data"
workspaces_dir: "workspaces"
```

### 5. Place Notebooks

Upload your `.ipynb` files and any assets into the `data/` folder:

```bash
scp -i your-key.pem -r ./my-notebooks/ ubuntu@<EC2_PUBLIC_IP>:/home/ubuntu/manim-server/data/
```

Every file in `data/` gets copied into each student's workspace.

## When to Start

```
T-15 min   SSH in, run ./start.sh (image pull + 60 containers takes ~5-10 min)
T-5 min    Verify it works: curl http://localhost/ — should see landing page
T-0        Give students the URL: http://<EC2_PUBLIC_IP>/
T+3 hrs    Run ./cleanup.sh
            Terminate EC2 instance
```

## Starting the Workshop

```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
cd /home/ubuntu/manim-server
chmod +x start.sh cleanup.sh
./start.sh
```

You will see:

```
=== Manim Server ===
Pulling manimcommunity/manim:stable...
Initializing...
Creating 60 workspaces...
Starting 60 containers...
  student-01 -> :8001
  student-02 -> :8002
  ...
  student-60 -> :8060
Starting auth server on :9000...
Starting nginx...

=== Ready! ===
Open http://<YOUR_EC2_PUBLIC_IP>/ in a browser
Stop with: ./cleanup.sh
Reset a locked room: curl -X POST http://localhost:9000/reset/student-01
```

Students open `http://<EC2_PUBLIC_IP>/` and click **Get Started**.

## Student Flow

1. Student opens `http://<EC2_PUBLIC_IP>/`
2. Clicks **Get Started**
3. System auto-assigns the next free room
4. Room is locked to their IP — nobody else can access it
5. They get a full JupyterLab with Manim + LaTeX + ffmpeg
6. All changes are isolated to their own workspace

## Managing Rooms

```bash
# Reset a locked room (e.g. student's IP changed)
curl -X POST http://localhost:9000/reset/student-01

# Check container status
docker ps --filter "name=student-" --format "table {{.Names}}\t{{.Status}}"

# View logs for a specific student
docker logs student-01

# Restart a single container
docker restart student-01
```

## Ending the Workshop

```bash
./cleanup.sh
```

This stops all containers, kills auth server + nginx, and deletes all student workspaces.

Then terminate the EC2 instance to stop billing.

## Local Testing

On macOS (no sudo needed):

```yaml
# config.yml — use these for local testing
num_students: 3
nginx_port: 8080
```

```bash
# Make sure Docker Desktop is running
docker info

# Start everything
python3 -m uvicorn auth_server:app --host 127.0.0.1 --port 9000 &
python3 init.py
nginx -c $(pwd)/nginx.conf

# Open
open http://127.0.0.1:8080/

# Stop
./cleanup.sh
```

## How nginx.conf Works

The `nginx.conf` is **generated automatically** by `init.py` — you never edit it by hand. Here is how it works so you can debug if needed.

### Generated Structure

`init.py` reads `config.yml` and writes `nginx.conf` with one `location` block per student. For 60 students the file is ~150 lines. Here is the shape of it:

```nginx
worker_processes auto;
pid /tmp/manim-server-nginx.pid;
error_log /tmp/manim-server-nginx-error.log;

events { worker_connections 1024; }

http {
    access_log /tmp/manim-server-nginx-access.log;
    client_max_body_size 100M;          # allow large notebook uploads

    server {
        listen 80;

        # ── 1. Landing page ──────────────────────────────────
        location = / {
            proxy_pass http://127.0.0.1:9000/;
        }

        # ── 2. Room assignment (redirect) ────────────────────
        location = /assign {
            proxy_pass http://127.0.0.1:9000/assign;
        }

        # ── 3. Trailing-slash redirect ───────────────────────
        #   /s/student-01  →  /s/student-01/
        location ~ ^/s/(student-\d+)$ {
            return 301 /s/$1/;
        }

        # ── 4. Auth subrequest (internal, not public) ────────
        location /auth/ {
            internal;
            proxy_pass http://127.0.0.1:9000;
            proxy_pass_request_body off;
            proxy_set_header Content-Length "";
            proxy_set_header X-Real-IP $remote_addr;    # passes student IP
        }

        # ── 5. 403 error page ────────────────────────────────
        error_page 403 /locked.html;
        location = /locked.html {
            proxy_pass http://127.0.0.1:9000/locked;
        }

        # ── 6. Per-student proxy blocks (repeated ×60) ──────
        location /s/student-01/ {
            auth_request /auth/student-01;              # checks IP lock
            proxy_pass http://127.0.0.1:8001;           # student-01 container
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_http_version 1.1;                     # required for WebSocket
            proxy_set_header Upgrade $http_upgrade;     # Jupyter kernel WS
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400;                   # 24h timeout
        }

        location /s/student-02/ {
            auth_request /auth/student-02;
            proxy_pass http://127.0.0.1:8002;
            # ... same proxy headers ...
        }

        # ... student-03 through student-60 ...
    }
}
```

### Request Flow

```
1. Student opens GET /

   Browser ──► Nginx location = /
           ──► proxy_pass to auth_server :9000 /
           ──► Returns landing page HTML with "Get Started" button

2. Student clicks "Get Started" → GET /assign

   Browser ──► Nginx location = /assign
           ──► proxy_pass to auth_server :9000 /assign
           ──► Auth server picks next free room, locks IP
           ──► Returns 307 redirect to /s/student-XX/

3. Browser follows redirect → GET /s/student-01/lab

   Browser ──► Nginx location /s/student-01/
           ──► auth_request /auth/student-01   (internal subrequest)
               │
               └─► Nginx location /auth/
                   └─► proxy_pass to auth_server :9000 /auth/student-01
                       with X-Real-IP: <student IP>
                       └─► Auth server checks:
                           Room unclaimed? → lock to this IP → 200
                           Same IP?        → 200
                           Different IP?   → 403
           │
           ├─ 200 → proxy_pass to http://127.0.0.1:8001 (Jupyter)
           └─ 403 → error_page 403 → /locked.html page

4. Jupyter WebSocket connection → /s/student-01/api/kernels/...

   Same location block handles it via:
   proxy_http_version 1.1 + Upgrade headers → WebSocket upgrade
```

### Key Design Decisions

| Decision | Why |
|----------|-----|
| `auth_request` is `internal` | Students cannot bypass the IP check by calling `/auth/` directly |
| `proxy_pass` has no trailing `/` | Preserves the full `/s/student-01/...` path so Jupyter's `base_url` works |
| `X-Real-IP` header | Auth server sees the real student IP, not nginx's `127.0.0.1` |
| `proxy_read_timeout 86400` | Jupyter kernel WebSockets are long-lived; default 60s would kill them |
| `client_max_body_size 100M` | Students may upload notebooks or render large videos |
| `proxy_http_version 1.1` | Required for WebSocket upgrade to work |
| Container `base_url=/s/{id}` | Jupyter generates correct internal URLs when behind a path prefix |

### Troubleshooting

```bash
# Test nginx config syntax
nginx -t -c /path/to/nginx.conf

# Check if auth subrequest works
curl -v http://localhost:8080/s/student-01/

# View nginx error log
cat /tmp/manim-server-nginx-error.log

# Common issue: 502 Bad Gateway
#   → container not ready yet, check: docker ps --filter name=student-

# Common issue: 403 on refresh
#   → IP changed (e.g. mobile switched WiFi)
#   → Fix: curl -X POST http://localhost:9000/reset/student-XX
```

## Cost

| Item | Cost |
|------|------|
| m5.8xlarge for 3hrs (on-demand) | ~$4.50 |
| m5.8xlarge for 3hrs (spot, ~70% off) | ~$1.35 |
| EBS 30GB | ~$0.03 |
| **Total** | **~$1.40 - $4.50** |
