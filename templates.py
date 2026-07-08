from __future__ import annotations

from room_manager import RoomManager

_LANDING_CSS = """\
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
html { height: 100%; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fbfbfd;
  color: #1d1d1f;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
  position: relative;
}
body::before {
  content: '';
  position: fixed;
  top: -50%;
  right: -20%;
  width: 70%;
  height: 120%;
  background: radial-gradient(ellipse, rgba(0,113,227,0.03) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}
.container {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 0 24px;
  max-width: 520px;
}
.badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: -0.01em;
  color: #86868b;
  margin-bottom: 24px;
}
h1 {
  font-size: clamp(40px, 8vw, 56px);
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1.07;
  color: #1d1d1f;
  margin-bottom: 20px;
}
.subtitle {
  font-size: clamp(17px, 3vw, 21px);
  font-weight: 400;
  color: #86868b;
  line-height: 1.38;
  margin-bottom: 48px;
  letter-spacing: -0.01em;
}
.spots {
  font-size: 14px;
  font-weight: 400;
  color: #86868b;
  margin-bottom: 28px;
  letter-spacing: -0.01em;
}
.cta {
  opacity: 1;
}
.field { margin-bottom: 16px; }
.field-row {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 16px;
}
.field-row .field { margin-bottom: 0; }
.field input {
  width: 100%;
  max-width: 280px;
  padding: 12px 20px;
  font-family: inherit;
  font-size: 17px;
  letter-spacing: -0.01em;
  color: #1d1d1f;
  background: #fff;
  border: 1px solid #d2d2d7;
  border-radius: 12px;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.field input:focus {
  border-color: #0071e3;
  box-shadow: 0 0 0 3px rgba(0,113,227,0.15);
}
.field input::placeholder { color: #aeaeb2; }
button, .btn {
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
  text-decoration: none;
  transition: background 0.3s ease;
  -webkit-tap-highlight-color: transparent;
}
button:hover, .btn:hover { background: #0077ed; }
button:active, .btn:active { background: #006edb; }
.notyou {
  background: none;
  border: none;
  color: #86868b;
  font-family: inherit;
  font-size: 14px;
  cursor: pointer;
  text-decoration: underline;
  -webkit-tap-highlight-color: transparent;
}
.notyou:hover { color: #1d1d1f; }
.footer {
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
}"""

_ADMIN_CSS = """\
*, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  background: #f5f5f7;
  color: #1d1d1f;
  padding: 40px 24px;
  min-height: 100vh;
  display: flex;
  justify-content: center;
}
.container { max-width: 640px; width: 100%; }
h1 { font-size: 28px; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 8px; }
.stats { font-size: 15px; color: #86868b; margin-bottom: 32px; }
table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid #e5e5e5;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
}
th {
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #86868b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e5e5;
  background: #fafafa;
}
td {
  padding: 12px 16px;
  font-size: 15px;
  border-bottom: 1px solid #f0f0f0;
}
tr:last-child td { border-bottom: none; }
tr.empty td { color: #c7c7cc; }
td.name { font-weight: 500; }
.footer { margin-top: 24px; font-size: 12px; color: #aeaeb2; }"""


def landing_page(cookie_name: str | None, rooms: RoomManager) -> str:
    assigned = cookie_name is not None and rooms.is_assigned(cookie_name) if cookie_name else False

    if assigned:
        room = rooms.room_for_name(cookie_name)
        cta = f"""\
  <div style="display:flex; flex-direction:column; align-items:center; gap:12px;">
    <a href="/s/{room}/" class="btn">Enter Your Room</a>
    <form action="/leave" method="post" style="margin-top:8px;">
      <button type="submit" class="notyou">Not {cookie_name}? Start over</button>
    </form>
  </div>"""
        subtitle = "Welcome back to your workspace."
        spots = "Your room is ready."
    else:
        cta = """\
  <form action="/assign" method="get" class="cta">
    <div class="field-row">
      <div class="field">
        <input type="text" id="first_name" name="first_name" placeholder="First name" autocomplete="off" autofocus required>
      </div>
      <div class="field">
        <input type="text" id="last_name" name="last_name" placeholder="Last name" autocomplete="off" required>
      </div>
    </div>
    <button type="submit">Get Started</button>
  </form>"""
        subtitle = "Create beautiful mathematical animations with code."
        spots = f"{rooms.available} seats remaining"

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>HKU Manim Workshop</title>
<style>{_LANDING_CSS}</style>
</head>
<body>
<div class="container">
  <p class="badge">The University of Hong Kong</p>
  <h1>Manim Workshop</h1>
  <p class="subtitle">{subtitle}</p>
  <p class="spots">{spots}</p>
  {cta}
</div>
<p class="footer">The University of Hong Kong &middot; Department of Mathematics</p>
</body>
</html>"""


def admin_page(rooms: RoomManager) -> str:
    rows: list[str] = []
    for snap in rooms.snapshot():
        if snap.name:
            rows.append(
                f'<tr><td>{snap.room_id}</td><td class="name">{snap.name}</td><td>{snap.assigned_at}</td></tr>'
            )
        else:
            rows.append(
                f'<tr class="empty"><td>{snap.room_id}</td><td>-</td><td>-</td></tr>'
            )

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Manim Workshop — Admin</title>
<style>{_ADMIN_CSS}</style>
<meta http-equiv="refresh" content="15">
</head>
<body>
<div class="container">
<h1>Manim Workshop</h1>
<p class="stats">{rooms.occupied} occupied / {rooms.total} total</p>
<table>
<thead><tr><th>Room</th><th>Student</th><th>Since</th></tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
<p class="footer">Auto-refreshes every 15 seconds</p>
</div>
</body>
</html>"""


def locked_page() -> str:
    return """\
<!DOCTYPE html>
<html><head><title>Room Locked</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { font-family: system-ui, sans-serif; text-align: center; padding: 60px; background: #1a1a2e; color: #eee; }
h1 { color: #e94560; }
a { color: #4a90d9; }
</style></head>
<body>
<h1>Room Locked</h1>
<p>This room belongs to someone else.</p>
<p><a href="/">Enter your first and last name to join</a></p>
</body></html>"""


def full_page() -> str:
    return """\
<!DOCTYPE html>
<html><head><title>All Rooms Full</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { font-family: system-ui, sans-serif; text-align: center; padding: 60px; background: #1a1a2e; color: #eee; }
h1 { color: #e94560; }
a { color: #4a90d9; }
</style></head>
<body>
<h1>All rooms are full</h1>
<p>Please try again later.</p>
<p><a href="/">Back</a></p>
</body></html>"""
