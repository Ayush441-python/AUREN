# AUREN Risk Analytics Backend

Enterprise Python FastAPI backend powering the AUREN portfolio and risk intelligence platform.

## Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI app initialization, CORS, lifespan
│   ├── api/
│   │   ├── router.py        # Central API router
│   │   └── endpoints/       # Route handlers (/risk, /liquidity, /wallet, /report, etc.)
│   ├── core/
│   │   └── config.py        # Environment variables & Pydantic-settings
│   ├── schemas/             # Pydantic request & response models
│   ├── services/            # Quantitative analysis & business logic
│   └── utils/               # Numerical serializers & helpers
```

## Running the Backend

```bash
uvicorn backend.app.main:app --reload --port 8000
```

Interactive documentation is available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
