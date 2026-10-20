#!/usr/bin/env bash
echo "Restarting Autonomous Stock Terminal..."
sudo systemctl daemon-reload
sudo systemctl restart stock-system.service
sudo systemctl reload nginx
echo "Service restarted."
sudo systemctl status stock-system.service --no-pager
