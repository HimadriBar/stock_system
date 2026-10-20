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
    raw_path = request.scope.get("path", "")
    clean = raw_path

    # Strip /api/index or /api/index.py prefix if Vercel prepends it
    for prefix in ["/api/index.py", "/api/index"]:
        if clean == prefix or clean == prefix + "/":
            clean = "/"
            break
        elif clean.startswith(prefix + "/"):
            clean = clean[len(prefix):]
            break

    request.scope["path"] = clean
    return await call_next(request)
