# Tech Stack

## Stack

- **Language**: Python 3
- **Framework**: FastAPI
- **Data validation**: Pydantic (models for request/response schemas)
- **Database**: Backend NoSQL store (accessed via data access layer)
- **Testing**: pytest (via venv)
- **Virtual environment**: `venv/`

## Dependencies

All dependencies are pinned with exact versions (`==`) in `requirements.txt`.

Install dependencies:
```
venv\Scripts\pip install -r requirements.txt
```

Never install packages into the global Python environment.

## Common Commands

```bash
# Install dependencies
venv\Scripts\pip install -r requirements.txt

# Run the development server
venv\Scripts\uvicorn app.main:app --reload

# Run tests
venv\Scripts\pytest

# Run a specific test file
venv\Scripts\pytest tests/test_cases.py
```

## API Documentation

FastAPI auto-generates interactive docs at runtime:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
