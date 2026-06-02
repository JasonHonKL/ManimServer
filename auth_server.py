from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
import yaml

app = FastAPI()

locks: dict[str, str] = {}
ip_to_room: dict[str, str] = {}

with open("config.yml") as f:
    config = yaml.safe_load(f)

num_students = config["num_students"]
all_rooms = [f"student-{i:02d}" for i in range(1, num_students + 1)]


@app.get("/")
async def landing(request: Request):
    ip = request.client.host
    assigned = ip_to_room.get(ip)
    available = len([r for r in all_rooms if r not in locks])
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>HKU Manim Workshop</title>
<style>
*, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{ height: 100%; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fbfbfd;
  color: #1d1d1f;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  overflow: hidden;
  position: relative;
}}
body::before {{
  content: '';
  position: fixed;
  top: -50%;
  right: -20%;
  width: 70%;
  height: 120%;
  background: radial-gradient(ellipse, rgba(0,113,227,0.03) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}}
.container {{
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 0 24px;
  max-width: 600px;
}}
.badge {{
  display: inline-block;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: -0.01em;
  color: #86868b;
  margin-bottom: 24px;
  opacity: 0;
  animation: reveal 0.8s cubic-bezier(0.25, 0.1, 0.25, 1) 0.1s forwards;
}}
h1 {{
  font-size: clamp(40px, 8vw, 56px);
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1.07;
  color: #1d1d1f;
  margin-bottom: 20px;
  opacity: 0;
  animation: reveal 1s cubic-bezier(0.25, 0.1, 0.25, 1) 0.2s forwards;
}}
.subtitle {{
  font-size: clamp(17px, 3vw, 21px);
  font-weight: 400;
  color: #86868b;
  line-height: 1.38;
  margin-bottom: 48px;
  letter-spacing: -0.01em;
  opacity: 0;
  animation: reveal 1s cubic-bezier(0.25, 0.1, 0.25, 1) 0.35s forwards;
}}
.spots {{
  font-size: 14px;
  font-weight: 400;
  color: #86868b;
  margin-bottom: 28px;
  letter-spacing: -0.01em;
  opacity: 0;
  animation: reveal 1s cubic-bezier(0.25, 0.1, 0.25, 1) 0.5s forwards;
}}
.cta {{
  opacity: 0;
  animation: reveal 1s cubic-bezier(0.25, 0.1, 0.25, 1) 0.6s forwards;
}}
button {{
  display: inline-block;
  padding: 12px 32px;
  font-family: inherit;
  font-size: 17px;
  font-weight: 400;
  letter-spacing: -0.01em;
  color: #fff;
  background: #0071e3;
  border: none;
  border-radius: 980px;
  cursor: pointer;
  transition: background 0.3s ease;
  -webkit-tap-highlight-color: transparent;
}}
button:hover {{ background: #0077ed; }}
button:active {{ background: #006edb; }}
.footer {{
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  text-align: center;
  padding: 20px;
  font-size: 11px;
  font-weight: 400;
  color: #aeaeb2;
  letter-spacing: 0.02em;
  opacity: 0;
  animation: reveal 1s cubic-bezier(0.25, 0.1, 0.25, 1) 0.8s forwards;
}}
@keyframes reveal {{
  from {{ opacity: 0; transform: translateY(12px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }}
}}
</style>
</head>
<body>
<div class="container">
  <p class="badge">The University of Hong Kong</p>
  <h1>Manim Workshop</h1>
  <p class="subtitle">{"Welcome back to your workspace." if assigned else "Create beautiful mathematical animations with code."}</p>
  <p class="spots">{"Your room is ready." if assigned else f"{available} seats remaining"}</p>
  <form action="/assign" method="get" class="cta">
    <button type="submit">{"Enter My Room" if assigned else "Get Started"}</button>
  </form>
</div>
<p class="footer">The University of Hong Kong &middot; Department of Mathematics</p>
</body>
</html>"""
    return HTMLResponse(html)


@app.get("/assign")
async def assign(request: Request):
    ip = request.client.host
    if ip in ip_to_room:
        return RedirectResponse(url=f"/s/{ip_to_room[ip]}/")
    available = [r for r in all_rooms if r not in locks]
    if not available:
        return HTMLResponse("<h1>All rooms are full</h1><p><a href='/'>Back</a></p>", status_code=503)
    room = available[0]
    locks[room] = ip
    ip_to_room[ip] = room
    return RedirectResponse(url=f"/s/{room}/")


@app.get("/auth/{room_id}")
async def auth(room_id: str, request: Request):
    ip = request.headers.get("x-real-ip", request.client.host)
    if room_id not in locks:
        locks[room_id] = ip
        return Response(status_code=200)
    if locks[room_id] == ip:
        return Response(status_code=200)
    return Response(status_code=403)


@app.get("/locked")
async def locked():
    return HTMLResponse("""<!DOCTYPE html>
<html><head><title>Room Locked</title>
<style>
body { font-family: system-ui, sans-serif; text-align: center; padding: 60px; background: #1a1a2e; color: #eee; }
h1 { color: #e94560; }
a { color: #4a90d9; }
</style></head>
<body>
<h1>Room Locked</h1>
<p>This room is already in use from another device.</p>
<p><a href="/">Go back</a></p>
</body></html>""")


@app.post("/reset/{room_id}")
async def reset(room_id: str, request: Request):
    if request.client.host not in ("127.0.0.1", "::1"):
        return Response(status_code=403)
    ip = locks.pop(room_id, None)
    if ip:
        ip_to_room.pop(ip, None)
    return {"status": "ok", "room": room_id}
