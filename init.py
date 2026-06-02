#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import yaml


def main():
    with open("config.yml") as f:
        config = yaml.safe_load(f)

    num = config["num_students"]
    cpu = config["cpu"]
    memory = config["memory"]
    base_port = config["base_port"]
    image = config["image"]
    data_dir = config["data_dir"]
    ws_dir = config["workspaces_dir"]

    if not os.path.isdir(data_dir) or not os.listdir(data_dir):
        print(f"Error: {data_dir}/ is empty or missing. Place notebooks there first.")
        sys.exit(1)

    os.makedirs(ws_dir, exist_ok=True)

    print(f"Creating {num} workspaces...")
    for i in range(1, num + 1):
        sid = f"student-{i:02d}"
        dst = os.path.join(ws_dir, sid)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(data_dir, dst)

    print(f"Starting {num} containers...")
    for i in range(1, num + 1):
        sid = f"student-{i:02d}"
        port = base_port + i - 1
        ws = os.path.abspath(os.path.join(ws_dir, sid))

        subprocess.run(["docker", "rm", "-f", sid], capture_output=True)

        cmd = [
            "docker", "run", "-d",
            "--name", sid,
            "--cpus", str(cpu),
            "--memory", memory,
            "-v", f"{ws}:/manim",
            "-p", f"127.0.0.1:{port}:8888",
            image,
            "jupyter", "lab",
            "--ip=0.0.0.0",
            "--port=8888",
            "--no-browser",
            f"--ServerApp.base_url=/s/{sid}",
            "--ServerApp.token=",
            "--ServerApp.password=",
            "--ServerApp.disable_check_xsrf=True",
            "--ServerApp.allow_root=True",
            "--ServerApp.allow_origin=*",
        ]

        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  FAIL {sid}: {r.stderr.strip()}")
        else:
            print(f"  {sid} -> :{port}")

    generate_nginx(config)
    print("Done.")


def generate_nginx(config):
    num = config["num_students"]
    base_port = config["base_port"]
    auth_port = config["auth_port"]
    port = config["nginx_port"]

    L = []
    L.append("worker_processes auto;")
    L.append("pid /tmp/manim-server-nginx.pid;")
    L.append("error_log /tmp/manim-server-nginx-error.log;")
    L.append("")
    L.append("events { worker_connections 1024; }")
    L.append("")
    L.append("http {")
    L.append("    access_log /tmp/manim-server-nginx-access.log;")
    L.append("    client_max_body_size 100M;")
    L.append("")
    L.append("    server {")
    L.append(f"        listen {port};")
    L.append("")
    L.append("        location = / {")
    L.append(f"            proxy_pass http://127.0.0.1:{auth_port}/;")
    L.append("        }")
    L.append("")
    L.append("        location = /assign {")
    L.append(f"            proxy_pass http://127.0.0.1:{auth_port}/assign;")
    L.append("        }")
    L.append("")
    L.append("        location ~ ^/s/(student-\\d+)$ {")
    L.append("            return 301 /s/$1/;")
    L.append("        }")
    L.append("")
    L.append("        location /auth/ {")
    L.append("            internal;")
    L.append(f"            proxy_pass http://127.0.0.1:{auth_port};")
    L.append("            proxy_pass_request_body off;")
    L.append('            proxy_set_header Content-Length "";')
    L.append("            proxy_set_header X-Real-IP $remote_addr;")
    L.append("        }")
    L.append("")
    L.append("        error_page 403 /locked.html;")
    L.append("        location = /locked.html {")
    L.append(f"            proxy_pass http://127.0.0.1:{auth_port}/locked;")
    L.append("        }")

    for i in range(1, num + 1):
        sid = f"student-{i:02d}"
        p = base_port + i - 1
        L.append("")
        L.append(f"        location /s/{sid}/ {{")
        L.append(f"            auth_request /auth/{sid};")
        L.append(f"            proxy_pass http://127.0.0.1:{p};")
        L.append("            proxy_set_header Host $host;")
        L.append("            proxy_set_header X-Real-IP $remote_addr;")
        L.append("            proxy_http_version 1.1;")
        L.append("            proxy_set_header Upgrade $http_upgrade;")
        L.append('            proxy_set_header Connection "upgrade";')
        L.append("            proxy_read_timeout 86400;")
        L.append("        }")

    L.append("    }")
    L.append("}")

    with open("nginx.conf", "w") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    main()
