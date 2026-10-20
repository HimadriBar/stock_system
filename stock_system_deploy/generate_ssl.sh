#!/usr/bin/env bash
# ==============================================================================
# OpenSSL Certificate Generator for test-admin.housiey.com
# ==============================================================================

set -e

DOMAIN="test-admin.housiey.com"
CERT_DIR="/etc/ssl/certs"
KEY_DIR="/etc/ssl/private"
CERT_FILE="$CERT_DIR/stock_system.crt"
KEY_FILE="$KEY_DIR/stock_system.key"

if [ "$EUID" -ne 0 ]; then
    echo "[!] Please run with sudo: sudo bash generate_ssl.sh"
    exit 1
fi

echo "[*] Creating SSL directories..."
mkdir -p "$CERT_DIR" "$KEY_DIR"

echo "[*] Generating 2048-bit OpenSSL private key & certificate for $DOMAIN..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/C=IN/ST=Maharashtra/L=Mumbai/O=StockSystem/OU=Trading/CN=$DOMAIN"

chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

echo "[✓] OpenSSL certificate successfully created:"
echo "    Certificate: $CERT_FILE"
echo "    Private Key: $KEY_FILE"

if systemctl is-active --quiet nginx; then
    echo "[*] Testing Nginx syntax and reloading..."
    nginx -t && systemctl reload nginx
    echo "[✓] Nginx reloaded with OpenSSL on HTTPS (Port 443)!"
fi
