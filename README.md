# Mahoraga — Adaptive Cyber-Immune System
> Adapts to every attack. Never defeated by the same technique twice.

## Quick Start

### 1. Start Ollama (local LLM)
```bash
ollama serve
ollama pull llama3.2
```

### 2. Start simulated network
```bash
cd simulation && docker-compose up -d
```

### 3. Start backend
```bash
cd backend && pip install -r requirements.txt
cp ../.env.example .env
python -m uvicorn main:sio_app --host 0.0.0.0 --port 8000 --reload
```

### 4. Start frontend
```bash
cd frontend && npm install && npm run dev
```

### 5. Open browser
```
http://localhost:3000
```

## Architecture

```
mahoraga/
├── simulation/     Docker nodes (web_server, api_service, database_node, admin_panel)
├── backend/        FastAPI + RL agents + anomaly detection + threat memory
└── frontend/       Next.js 14 + D3.js + Recharts + Socket.IO
```

## The Biological Parallel

Your immune system does not wait to get sick. It continuously stress-tests itself.
Mahoraga does the same — a Red Agent invents attacks, a Blue Agent closes every gap found,
an Anomaly Engine monitors live behaviour, and a Governor prevents the defence from harming
the host. The network hardens itself every single hour.


