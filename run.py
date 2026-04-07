"""Run the API server. Use this instead of `python src/main.py` (relative imports require package context)."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
