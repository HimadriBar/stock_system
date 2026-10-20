import os
import sys

# Ensure root, stock_system, and web_app are in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STOCK_SYSTEM_DIR = os.path.join(BASE_DIR, "stock_system")
WEB_APP_DIR = os.path.join(BASE_DIR, "web_app")

for d in [BASE_DIR, STOCK_SYSTEM_DIR, WEB_APP_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)

from fastapi import Request
from fastapi.responses import HTMLResponse
from web_app.server import app, get_dashboard

# Normalize Vercel rewritten paths so all routes (/ , /api/live-data, etc.) resolve cleanly
@app.middleware("http")
async def vercel_path_normalizer(request: Request, call_next):
    matched_path = request.headers.get("x-matched-path")
    original_path = request.scope.get("path", "")
    
    if matched_path and matched_path != original_path:
        # Restore actual user-requested path from Vercel header
        request.scope["path"] = matched_path
    elif original_path == "/api/index" or original_path == "/api/index/":
        request.scope["path"] = "/"
    elif original_path.startswith("/api/index/"):
        request.scope["path"] = original_path[len("/api/index"):]

    return await call_next(request)

# Explicit fallback handlers for Vercel default function paths
@app.get("/api/index", response_class=HTMLResponse)
@app.get("/api/index/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/api/", response_class=HTMLResponse)
def get_dashboard_fallback():
    return get_dashboard()
