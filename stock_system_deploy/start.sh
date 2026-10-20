#!/usr/bin/env bash
echo "Starting Autonomous Stock Terminal & Nginx..."
sudo systemctl start stock-system.service
sudo systemctl reload nginx
echo "Status:"
sudo systemctl status stock-system.service --no-pager
