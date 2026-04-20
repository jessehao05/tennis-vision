# Tennis Vision Frontend

React + TypeScript + Vite frontend for the Tennis Vision pipeline.

## Prerequisites

- Node.js 18+
- The FastAPI backend running on port 8080 (API calls are proxied to it during dev)

## Install

```bash
cd frontend
npm install
```

## Run locally for development

```bash
npm run dev
```

Opens at `http://localhost:5173`. API calls are automatically proxied to `http://localhost:8080`.

## Build for production

```bash
npm run build
```

Outputs to `frontend/dist/`. FastAPI serves this automatically when the folder exists — no separate frontend process needed.
