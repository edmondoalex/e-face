
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.staticfiles import StaticFiles

# import routers and core helpers
from .routers import auth as auth_router
from .routers import config as config_router
from .routers import devices as devices_router
from .routers import admin as admin_router
from .routers import integration as integration_router
from .routers import rooms as rooms_router
from .routers import users as users_router
from .routers import webhook as webhook_router
from .core import BASE_DIR
from .ha_ws import clients, start_background, stop_background


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path, scope):  # type: ignore[override]
        response = await super().get_response(path, scope)
        content_type = response.headers.get("content-type", "")
        if response.status_code == 200 and "text/html" in content_type:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


app = FastAPI(title="e-face API")

# include routers under /api
app.include_router(auth_router.router, prefix="/api")
app.include_router(config_router.router, prefix="/api/config")
app.include_router(devices_router.router, prefix="/api/devices")
app.include_router(admin_router.router, prefix="/api/admin")
app.include_router(rooms_router.router, prefix="/api/rooms")
app.include_router(users_router.router, prefix="/api/users")
app.include_router(integration_router.router, prefix="/api/integration")
app.include_router(webhook_router.router)

# serve built frontend static files (mount after API routers so /api/* resolves to API)
frontend_candidates = [
    os.path.join(os.path.dirname(BASE_DIR), "frontend_dist"),
    os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "frontend_dist"),
    os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "frontend", "dist"),
    os.path.join(os.path.dirname(BASE_DIR), "..", "frontend", "dist"),
]
FRONTEND_DIST_PATH = None
for frontend_dist in frontend_candidates:
    if os.path.isdir(frontend_dist):
        FRONTEND_DIST_PATH = frontend_dist
        break


# start HA websocket watcher on startup
@app.on_event("startup")
async def _start_ha_ws():
    await start_background(app)


@app.on_event("shutdown")
async def _stop_ha_ws():
    await stop_background(app)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        try:
            clients.remove(websocket)
        except Exception:
            pass


frontend_static: Optional[NoCacheStaticFiles] = None
if FRONTEND_DIST_PATH:
    frontend_static = NoCacheStaticFiles(directory=FRONTEND_DIST_PATH, html=True)


async def _serve_frontend(path: str, request: Request):
    if not frontend_static:
        raise HTTPException(status_code=404, detail="frontend_unavailable")
    normalized = path.lstrip("/")
    if not normalized:
        normalized = "index.html"
    response = await frontend_static.get_response(normalized, request.scope)
    if response.status_code == 404 and "." not in normalized:
        return await frontend_static.get_response("index.html", request.scope)
    return response


if FRONTEND_DIST_PATH:
    @app.get("/", include_in_schema=False)
    async def frontend_root(request: Request):
        return await _serve_frontend("", request)


    @app.get("/{full_path:path}", include_in_schema=False)
    async def frontend_catch_all(full_path: str, request: Request):
        return await _serve_frontend(full_path, request)


# simple health endpoint
@app.get("/health")
def health():
    return {"status": "ok"}

