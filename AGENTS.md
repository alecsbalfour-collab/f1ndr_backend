# f1ndr_backend

## Module contract (f1ndr, trinn, sellr, listr, dealr)
- Each package exports `async def run(action: str, data: dict) -> dict` and `get_<name>_config() -> dict`.
- Config dicts always include `feature_key`, `feature_version`, `enabled`.
- Dependency direction (no cycles): sellr/dealr -> trinn -> listr; f1ndr and listr depend on nothing else in this set.
- Never call `loop.run_until_complete` inside code reachable from FastAPI routes; make it `async` and `await` it.

## Storage
- One shared Mongo connection opened in the FastAPI lifespan (`api/app_lifecycles.py` -> `api/startup.py`), via `db/connection_db.py`.
- Settings: `api/config/settings_config.py` (`MONGODB_URI`, `MONGODB_DB_NAME`, `JWT_SECRET_KEY`, `MONGODB_REQUIRED`). Don't reintroduce `MONGO_URI`/`JWT_SECRET`.
- Modules persist through `db/document_store.py` `DocumentStore`: Mongo when connected, in-memory otherwise (tests, dev without Mongo). Production (`ENVIRONMENT=production`) fails startup if Mongo is unreachable.
- `TestClient(app)` without `with` skips the lifespan, so tests stay in-memory. Mongo integration tests only run when `MONGODB_URI` is set in the process env (never read from `.env`, which points at real data).
- Local throwaway Mongo for integration tests: `docker run -d --rm --name f1ndr-test-mongo -p 27099:27017 mongo:7`, then run pytest with `MONGODB_URI=mongodb://127.0.0.1:27099`. Ports 27017/27018 are the user's own containers.

## Commands
- Python: `.venv/Scripts/python.exe`
- Run API: `.venv/Scripts/python.exe run_backend.py` (app lives in `api/main.py`; routers mounted in `api/router_api.py`)
- Module tests: `.venv/Scripts/python.exe -m pytest -q f1ndr/tests trinn/tests sellr/tests listr/tests dealr/tests`
- Root tests: `.venv/Scripts/python.exe -m pytest -q tests` (deployment tests need `MONGO_URI` etc.)
