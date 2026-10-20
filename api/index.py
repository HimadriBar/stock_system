import os
import sys

# Ensure root, stock_system, and web_app are in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STOCK_SYSTEM_DIR = os.path.join(BASE_DIR, "stock_system")
WEB_APP_DIR = os.path.join(BASE_DIR, "web_app")

for d in [BASE_DIR, STOCK_SYSTEM_DIR, WEB_APP_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)

from fastapi.responses import HTMLResponse
from web_app.server import app, get_dashboard

# Fallback route in case direct file is accessed
@app.get("/api/index", response_class=HTMLResponse)
@app.get("/api/index/", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
def index_fallback():
    return get_dashboard()
