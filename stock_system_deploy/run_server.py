"""
Root Entrypoint for Autonomous Stock System Web Terminal.
Sets up Python path and launches FastAPI with Uvicorn.
Default Port: 9012 (can be overridden by PORT environment variable)
"""

import os
import sys

# Ensure root, stock_system, and web_app are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

stock_system_dir = os.path.join(BASE_DIR, "stock_system")
if stock_system_dir not in sys.path:
    sys.path.insert(0, stock_system_dir)

web_app_dir = os.path.join(BASE_DIR, "web_app")
if web_app_dir not in sys.path:
    sys.path.insert(0, web_app_dir)

import uvicorn
from web_app.server import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9012))
    host = os.environ.get("HOST", "0.0.0.0")
    print("\n=======================================================")
    print("   AUTONOMOUS STOCK LIVE TERMINAL (UBUNTU HOSTED)     ")
    print(f"   Domain:  http://test-admin.housiey.com             ")
    print(f"   Listening on: http://{host}:{port}                 ")
    print("=======================================================\n")
    uvicorn.run("web_app.server:app", host=host, port=port, reload=False, log_level="info")
