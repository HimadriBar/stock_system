#!/usr/bin/env bash
# ==============================================================================
# Autonomous Stock Live Terminal - Ubuntu 1-Click Production Setup Script
# Domain: test-admin.housiey.com
# Internal Port: 9012
# SSL / HTTPS: OpenSSL & Let's Encrypt Support (Port 443)
# Reverse Proxy: Nginx
# ==============================================================================

set -e

# Terminal Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
echo "=========================================================================="
echo "    AUTONOMOUS STOCK QUANTITATIVE TERMINAL - UBUNTU ONE-CLICK SETUP       "
echo "             (With OpenSSL HTTPS & Nginx Reverse Proxy)                   "
echo "=========================================================================="
echo -e "${NC}"

# 1. Check Root Privileges
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Please run this script with sudo or as root:${NC}"
    echo "  sudo bash setup.sh"
    exit 1
fi

# Detect actual user and directory
ACTUAL_USER="${SUDO_USER:-$USER}"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOMAIN="test-admin.housiey.com"
PORT="9012"

echo -e "${BLUE}[*] Project Directory:${NC} $APP_DIR"
echo -e "${BLUE}[*] System User:${NC}       $ACTUAL_USER"
echo -e "${BLUE}[*] Target Domain:${NC}     $DOMAIN"
echo -e "${BLUE}[*] Internal Port:${NC}     $PORT"
echo -e "${BLUE}[*] HTTPS Port:${NC}        443 (SSL Enabled)"
echo ""

# 2. System Packages Update & Installation
echo -e "${YELLOW}[1/8] Updating apt package lists & installing system dependencies...${NC}"
apt-get update -y
apt-get install -y python3 python3-pip python3-venv python3-dev build-essential openssl nginx curl ufw certbot python3-certbot-nginx

# 3. Python Virtual Environment Setup
echo -e "${YELLOW}[2/8] Setting up Python virtual environment...${NC}"
if [ ! -d "$APP_DIR/venv" ]; then
    python3 -m venv "$APP_DIR/venv"
fi

echo -e "${YELLOW}[3/8] Installing dependencies from requirements.txt...${NC}"
"$APP_DIR/venv/bin/pip" install --upgrade pip setuptools wheel
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# 4. Set Correct Ownership & Script Permissions
echo -e "${YELLOW}[4/8] Setting directory ownership and script permissions...${NC}"
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$APP_DIR"
chmod +x "$APP_DIR"/*.sh 2>/dev/null || true

# 5. OpenSSL Certificate Generation
echo -e "${YELLOW}[5/8] Generating OpenSSL certificates for $DOMAIN...${NC}"
mkdir -p /etc/ssl/certs /etc/ssl/private

CERT_FILE="/etc/ssl/certs/stock_system.crt"
KEY_FILE="/etc/ssl/private/stock_system.key"

if [ ! -f "$KEY_FILE" ] || [ ! -f "$CERT_FILE" ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "/C=IN/ST=Maharashtra/L=Mumbai/O=StockSystem/OU=Trading/CN=$DOMAIN"
    chmod 600 "$KEY_FILE"
    chmod 644 "$CERT_FILE"
    echo -e "${GREEN}[✓] OpenSSL Certificate successfully created at $CERT_FILE${NC}"
else
    echo -e "${BLUE}[*] SSL certificates already present. Skipping regeneration.${NC}"
fi

# 6. Systemd Background Service Setup
echo -e "${YELLOW}[6/8] Configuring and enabling systemd background service (stock-system)...${NC}"
SERVICE_DEST="/etc/systemd/system/stock-system.service"

if [ -f "$APP_DIR/systemd/stock-system.service" ]; then
    sed -e "s|__USER__|$ACTUAL_USER|g" \
        -e "s|__APP_DIR__|$APP_DIR|g" \
        "$APP_DIR/systemd/stock-system.service" > "$SERVICE_DEST"
else
    cat > "$SERVICE_DEST" <<EOF
[Unit]
Description=Autonomous Stock Quantitative Trading Terminal
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$APP_DIR
Environment="PORT=$PORT"
Environment="HOST=0.0.0.0"
Environment="PYTHONPATH=$APP_DIR:$APP_DIR/stock_system:$APP_DIR/web_app"
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/run_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
fi

systemctl daemon-reload
systemctl enable stock-system.service
systemctl restart stock-system.service

# 7. Nginx Reverse Proxy Setup (with OpenSSL HTTPS on 443 & HTTP on 80)
echo -e "${YELLOW}[7/8] Configuring Nginx reverse proxy with OpenSSL for $DOMAIN...${NC}"
NGINX_AVAILABLE="/etc/nginx/sites-available/$DOMAIN"
NGINX_ENABLED="/etc/nginx/sites-enabled/$DOMAIN"

if [ -f "$APP_DIR/nginx/test-admin.housiey.com.conf" ]; then
    cp "$APP_DIR/nginx/test-admin.housiey.com.conf" "$NGINX_AVAILABLE"
else
    cat > "$NGINX_AVAILABLE" <<EOF
upstream stock_backend_cluster {
    server 127.0.0.1:$PORT;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/ssl/certs/stock_system.crt;
    ssl_certificate_key /etc/ssl/private/stock_system.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 50M;

    access_log /var/log/nginx/stock_system_ssl_access.log;
    error_log /var/log/nginx/stock_system_ssl_error.log;

    location / {
        proxy_pass http://stock_backend_cluster;
        proxy_http_version 1.1;

        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;

        proxy_buffering off;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF
fi

# Enable site in Nginx
ln -sf "$NGINX_AVAILABLE" "$NGINX_ENABLED"

# Test Nginx syntax and reload
if nginx -t; then
    systemctl reload nginx
    echo -e "${GREEN}[✓] Nginx configuration verified and reloaded!${NC}"
else
    echo -e "${RED}[!] Nginx configuration error. Please inspect $NGINX_AVAILABLE${NC}"
fi

# 8. Configure Firewall (UFW)
echo -e "${YELLOW}[8/8] Checking firewall rules...${NC}"
if command -v ufw >/dev/null 2>&1; then
    ufw allow OpenSSH >/dev/null 2>&1 || true
    ufw allow 80/tcp >/dev/null 2>&1 || true
    ufw allow 443/tcp >/dev/null 2>&1 || true
    ufw allow "$PORT/tcp" >/dev/null 2>&1 || true
fi

# Verification & Health Check
echo ""
echo -e "${CYAN}[*] Waiting for backend service to initialize on port $PORT...${NC}"
sleep 3

if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/" | grep -q "200\|301\|302"; then
    echo -e "${GREEN}${BOLD}[✓] SUCCESS! Autonomous Stock Terminal is live on port $PORT!${NC}"
else
    echo -e "${YELLOW}[!] Service is initializing. Check live logs with: sudo journalctl -u stock-system -f${NC}"
fi

# Summary Banner
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo '<SERVER_PUBLIC_IP>')
echo ""
echo -e "${GREEN}${BOLD}==========================================================================${NC}"
echo -e "${GREEN}${BOLD}            🎉 ONE-CLICK SETUP WITH OPENSSL COMPLETED!                    ${NC}"
echo -e "${GREEN}${BOLD}==========================================================================${NC}"
echo -e "${BOLD}Secure HTTPS URL:${NC}  ${CYAN}${BOLD}https://$DOMAIN${NC}"
echo -e "${BOLD}HTTP URL:${NC}          http://$DOMAIN  (Auto-redirects to HTTPS)"
echo -e "${BOLD}Direct Port URL:${NC}   http://${SERVER_IP}:$PORT"
echo ""
echo -e "${BOLD}Useful Service Commands:${NC}"
echo -e "  • Check Status:     ${CYAN}sudo bash status.sh${NC}   (or: sudo systemctl status stock-system)"
echo -e "  • View Live Logs:   ${CYAN}sudo bash logs.sh${NC}     (or: sudo journalctl -u stock-system -f)"
echo -e "  • Restart Service:  ${CYAN}sudo bash restart.sh${NC}  (or: sudo systemctl restart stock-system)"
echo -e "  • Re-issue SSL:     ${CYAN}sudo bash generate_ssl.sh${NC}"
echo ""
echo -e "${BOLD}To Upgrade to Trusted Let's Encrypt CA Certificate:${NC}"
echo -e "  Once your DNS A-Record propagates, you can also run:"
echo -e "  ${GREEN}${BOLD}sudo certbot --nginx -d $DOMAIN${NC}"
echo -e "${GREEN}${BOLD}==========================================================================${NC}"
