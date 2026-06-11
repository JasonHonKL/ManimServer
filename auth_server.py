from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from settings import load_config
from room_manager import RoomManager
from templates import landing_page, admin_page, locked_page, full_page
from auth_utils import verify_basic

config = load_config()
rooms = RoomManager(config.num_students)
app = FastAPI()


@app.get("/")
async def landing(request: Request):
    name = request.cookies.get("manim_name")
    html = landing_page(name, rooms)
    return HTMLResponse(html)


@app.get("/assign")
async def assign(request: Request, name: str = ""):
    name = name.strip()
    if not name:
        return RedirectResponse(url="/")

    room = rooms.assign(name)
    if room is None:
        return HTMLResponse(full_page(), status_code=503)

    resp = RedirectResponse(url=f"/s/{room}/", status_code=302)
    resp.set_cookie(key="manim_name", value=name, path="/", samesite="lax", httponly=True)
    return resp


@app.post("/leave")
async def leave(request: Request):
    name = request.cookies.get("manim_name", "")
    rooms.leave(name)
    resp = RedirectResponse(url="/", status_code=302)
    resp.delete_cookie("manim_name", path="/")
    return resp


@app.get("/auth/{room_id}")
async def auth(room_id: str, request: Request):
    name = request.cookies.get("manim_name", "")
    if rooms.auth(room_id, name):
        return Response(status_code=200)
    return Response(status_code=403)


@app.get("/locked")
async def locked():
    return HTMLResponse(locked_page())


@app.get("/admin")
async def admin(request: Request):
    auth_header = request.headers.get("authorization", "")
    if not verify_basic(auth_header, config.admin_password):
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Manim Admin"'},
            content="Unauthorized",
        )
    return HTMLResponse(admin_page(rooms))


@app.post("/reset/{room_id}")
async def reset(room_id: str, request: Request):
    if request.client.host not in ("127.0.0.1", "::1", "testclient"):
        return Response(status_code=403)
    rooms.reset(room_id)
    return {"status": "ok", "room": room_id}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "rooms_occupied": rooms.occupied,
        "rooms_total": rooms.total,
    }
