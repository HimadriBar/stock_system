#!/usr/bin/env bash
echo "Displaying real-time logs for stock-system (Press Ctrl+C to exit)..."
sudo journalctl -u stock-system.service -f
