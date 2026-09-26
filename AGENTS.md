# f1ndr_backend

## Module contract (f1ndr, trinn, sellr, listr, dealr)
- Each package exports `async def run(action: str, data: dict) -> dict` and `get_<name>_config() -> dict`.
- Config dicts always include `feature_key`, `feature_version`, `enabled`.
- Dependency direction (no cycles): sellr/dealr -> trinn -> listr; f1ndr and listr depend on nothing else in this set.
- Never call `loop.run_until_complete` inside code reachable from FastAPI routes; make it `async` and `await` it.

## Commands
- Python: `.venv/Scripts/python.exe`
- Run API: `.venv/Scripts/python.exe run_backend.py` (app lives in `api/main.py`; routers mounted in `api/router_api.py`)
- Module tests: `.venv/Scripts/python.exe -m pytest -q f1ndr/tests trinn/tests sellr/tests listr/tests dealr/tests`
- Root tests: `.venv/Scripts/python.exe -m pytest -q tests` (deployment tests need `MONGO_URI` etc.)
