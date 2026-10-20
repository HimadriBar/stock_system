# 🚀 Autonomous Stock Quantitative System — Ubuntu Server Deployment

This package contains the complete **Autonomous Stock Quantitative Screener & Live Terminal**, pre-configured for one-click hosting on an **Ubuntu Server** with **Nginx** reverse proxy on **port 9012** for domain **`test-admin.housiey.com`**.

---

## 📁 Package Directory Structure

```text
stock_system_deploy/
├── setup.sh                  # ⭐ 1-Click Automated Setup Script for Ubuntu
├── start.sh                  # Start systemd service and Nginx
├── stop.sh                   # Stop systemd service
├── restart.sh                # Restart service and reload Nginx
├── status.sh                 # Inspect status, port 9012, and health check
├── logs.sh                   # Follow live logs (journalctl)
├── run_server.py             # Root production runner (Port 9012)
├── requirements.txt          # Python dependencies
├── nginx/
│   └── test-admin.housiey.com.conf  # Nginx reverse-proxy configuration
├── systemd/
│   └── stock-system.service         # Systemd service unit template
├── stock_system/             # Quantitative analysis & risk engine
│   ├── analyzer.py           # Multi-factor technical scanning & scoring
│   ├── backtester.py         # Strategy backtesting engine
│   ├── config.py             # Watchlist, criteria, and capital limit (₹5,000)
│   ├── main.py               # CLI runner
│   ├── report_generator.py   # HTML and terminal report generator
│   ├── risk_manager.py       # Position sizing and risk bracket calculator
│   └── report.html           # Sample report output
├── web_app/                  # FastAPI Web Terminal
│   ├── server.py             # Live backend API & background market scanner
│   └── templates/
│       └── index.html        # Interactive quant terminal UI
├── groww_extension/          # Chrome Extension for 1-Click order execution on Groww
│   ├── manifest.json
│   └── content.js
├── groww_auto_order.user.js  # Tampermonkey Userscript alternative
└── README.md                 # Complete documentation
```

---

## ⚡ 1-Click Quick Start on Ubuntu

### Step 1: Copy this folder to your Ubuntu Server
You can copy this folder or the single `stock_system_deploy.tar.gz` file using `scp`:

```bash
# From your local machine:
scp -r stock_system_deploy.tar.gz username@YOUR_SERVER_IP:/home/username/
```

### Step 2: Extract & Enter Directory
SSH into your Ubuntu server:

```bash
ssh username@YOUR_SERVER_IP
tar -xzvf stock_system_deploy.tar.gz
cd stock_system_deploy
```

*(Or if you copied the uncompressed folder directly: `cd stock_system_deploy`)*

### Step 3: Run the One-Click Setup Script
Make the scripts executable and run `setup.sh` with `sudo`:

```bash
chmod +x *.sh
sudo bash setup.sh
```

### That's it! 🎯
The setup script will automatically:
1. Update apt repositories and install `python3`, `python3-venv`, `nginx`, `curl`, and `ufw`.
2. Create an isolated Python virtual environment (`venv`) and install all dependencies.
3. Configure and activate the **`stock-system`** systemd background service (auto-starts on boot and restarts on crash).
4. Configure the **Nginx** reverse proxy for domain **`test-admin.housiey.com`** routing to internal port **`9012`**.
5. Configure the UFW firewall for HTTP, HTTPS, and port 9012.
6. Verify service health and display your connection URLs.

---

## 🌐 DNS & Domain Setup

Ensure your domain **`test-admin.housiey.com`** points to your Ubuntu server:
1. Go to your DNS provider (Cloudflare, GoDaddy, Namecheap, AWS Route53, etc.).
2. Add an **A Record**:
   - **Type**: `A`
   - **Name / Host**: `test-admin`
   - **Target / Value**: `YOUR_UBUNTU_SERVER_PUBLIC_IP`
   - **TTL**: Auto or 300 seconds

---

## 🔒 Free SSL / HTTPS Setup (Let's Encrypt)

Once your DNS A-record has propagated to your server's IP, install a free SSL certificate using Certbot:

```bash
sudo certbot --nginx -d test-admin.housiey.com
```

Certbot will automatically modify the Nginx configuration, issue the SSL certificate, and enable HTTPS redirection. It also configures automatic certificate renewals.

---

## 🛠️ Management & Monitoring Commands

Inside `stock_system_deploy/`:

| Action | Command | Systemd Alternative |
| :--- | :--- | :--- |
| **Check Health & Status** | `sudo bash status.sh` | `sudo systemctl status stock-system` |
| **View Live Real-Time Logs** | `sudo bash logs.sh` | `sudo journalctl -u stock-system -f` |
| **Restart Application** | `sudo bash restart.sh` | `sudo systemctl restart stock-system` |
| **Stop Application** | `sudo bash stop.sh` | `sudo systemctl stop stock-system` |
| **Start Application** | `sudo bash start.sh` | `sudo systemctl start stock-system` |
| **Reload Nginx Only** | `sudo nginx -t && sudo systemctl reload nginx` | — |

---

## 🔌 Groww Auto-Order Extension / Userscript

The project includes an automatic order bridge for **Groww**:
1. When you click **"⚡ Auto-Set Order in Groww"** on the dashboard, it opens the stock in Groww with pre-calculated quantities and stop-loss.
2. To enable auto-population inside Groww:
   - **Option A (Chrome Extension)**:
     - Open Chrome and navigate to `chrome://extensions/`.
     - Enable **Developer mode** (top-right toggle).
     - Click **Load unpacked** and select the `groww_extension/` folder.
   - **Option B (Tampermonkey)**:
     - Install the Tampermonkey browser extension.
     - Create a new script and paste the contents of `groww_auto_order.user.js`.
   - **Option C (Bookmarklet)**:
     - On the web dashboard, drag the blue **"📌 1-Click Bookmarklet"** button to your browser bookmarks bar!

---

## ⚙️ Configuration & Environment Variables

- **Port**: Configured in `run_server.py` and `/etc/systemd/system/stock-system.service` as `PORT=9012`.
- **Host**: `0.0.0.0` (accessible locally and over the network).
- **Capital Cap**: Configurable in `stock_system/config.py` (`MAX_DAILY_INVESTMENT = 5000.0`).
- **Watchlist**: Configurable in `stock_system/config.py` (`WATCHLIST`).
