#!/bin/bash
echo "[Mahoraga] Starting simulated network..."
docker-compose up -d
echo "[Mahoraga] Network nodes online:"
echo "  web_server    → http://localhost:5001"
echo "  api_service   → http://localhost:5002"
echo "  database_node → http://localhost:5003"
echo "  admin_panel   → http://localhost:5004"
