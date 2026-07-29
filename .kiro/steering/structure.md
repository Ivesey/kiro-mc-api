# Project Structure

## Layout

```
kiro-api/
├── api/
|   ├── app/
|   │   ├── main.py           # FastAPI app instance and router registration
|   │   ├── routers/          # Route handlers (one file per resource, e.g. cases.py)
|   │   ├── models/           # Pydantic request/response models
|   │   ├── dal/              # Data access layer — all database interaction lives here
|   │   └── config.py         # App configuration and environment variables
|   ├── tests/                # pytest test files, mirroring app/ structure
|   └── requirements.txt      # Pinned dependencies
├── venv/                     # Python virtual environment (not committed)
├── webui/
|   ├── index.html            # Entry point, HTML structure, script/style references
|   ├── package.json
|   ├── styles.css            # All styling including severity colours, form states
|   ├── js/
│   |    ├── app.js          # Application controller — init, state, event wiring
│   |    ├── api.js          # HTTP client — all fetch calls to Cases API
│   |    ├── ui.js           # DOM manipulation — rendering lists, forms, messages
│   |    └── validation.js   # Pure validation functions — URL, email, form fields
|   ├── tests/               # JS test files
|   ├── node_modules/         # Node modules for testing (not committed)
└── .kiro/                    # Kiro steering and agent config
```

## Conventions

- **Routers**: One file per resource in `app/routers/`. Register routers in `app/main.py`.
- **Models**: Pydantic models in `app/models/`. Separate request and response models where shapes differ.
- **Data access layer**: All database calls go in `app/dal/`. Routers and services never query the database directly.
- **Documentation**: Every public FastAPI endpoint must have a `summary` and `description` in its decorator or docstring.
- **Config**: Environment variables are declared and validated in `app/config.py` using Pydantic `BaseSettings`.
- **Tests**: Mirror the `app/` structure under `tests/`. Mock DAL dependencies with `unittest.mock.patch`.
