# TradeBridge AI — frontend

React 19 + Vite + Tailwind 4 single-page app. It holds **no business logic**: it signs in against the backend, creates deals over HTTP, and polls `/api/deals/{id}` — the live underwriting screen renders exactly what the backend wrote to its audit log.

```bash
npm install
npm run dev        # http://localhost:5173 (expects the API on http://localhost:8000)
```

Point it at another API host with `VITE_API_URL`. Full setup, demo script and architecture: see the [root README](../Readme.md).
