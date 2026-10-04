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

## Auth
- Services live in `api/auth/` (`accounts`, `tokens`, `roles`, `audit`, `email`, `store`); `api/routes/auth_routes.py` is thin HTTP glue. `api/auth` must not import `api.routes`.
- JWTs are signed with `get_settings().JWT_SECRET_KEY` (not `auth_config.secret_key`, which only reads process env).
- Refresh tokens are persisted by `jti` and rotated on every `/auth/refresh`; replaying a used one revokes the whole session family. Access tokens are checked against a `jti` denylist in `require_user`.
- Guards in `api/dependencies/auth.py`: `require_user`, `require_scopes(...)` (roles -> scopes map in `api/auth/roles.py`), `require_verified_email`. Role changes apply on the next token refresh.
- Record security-relevant actions with `api.auth.audit.record_audit(event, request, user_id=..., actor_id=...)`.
- Auth by default: every `/api/v1` route needs `require_user`/`require_scopes` unless listed in `PUBLIC_ROUTES` in `tests/api/test_route_auth.py` (the test fails otherwise). Public = status/version, account entry points, anonymous browsing. Admin-only (`tasks:admin`) = trinn run/schedule/config, scraper search. Dealer (`inventory:*`) = dealr inventory, listr publishing.
- Ownership comes from the token, never the body: sellr `user_id`, dealr `owner_id`, watchr `user_id` (listed in the payload model's `server_fields`). Non-owners get 404, admins bypass (`owns()` in `api/dependencies/auth.py`); ownerless legacy documents are admin-only. Payload models with `server_fields` need a separate `Record` output model, since `OpenPayload` strips those fields on output too.
- Tests get tokens from the `headers_for(role, sub=...)` fixture in `tests/conftest.py`.
- Auth tests disable the slowapi limiter (`tests/api/test_auth.py`) and capture email by patching `api.routes.auth_routes.send_email`.

## Commands
- Python: `.venv/Scripts/python.exe`
- Run API: `.venv/Scripts/python.exe run_backend.py` (app lives in `api/main.py`; routers mounted in `api/router_api.py`)
- Module tests: `.venv/Scripts/python.exe -m pytest -q f1ndr/tests trinn/tests sellr/tests listr/tests dealr/tests`
- Root tests: `.venv/Scripts/python.exe -m pytest -q tests` (deployment tests need `MONGO_URI` etc.)
- Everything: `.venv/Scripts/python.exe -m pytest -q` (uses `pytest.ini` testpaths)
- The Docker image uses the same Python as `.venv` (3.14); keep them in sync, since the suite can't catch syntax the image's Python rejects. After Dockerfile changes, build and `docker run` it, then check `docker ps` shows `(healthy)`. In Git Bash prefix container paths with `MSYS_NO_PATHCONV=1`.

## Layout gotchas
- Root `core/`, `config/`, `data/`, `utils/`, `logs/*.py` look like duplicates but are imported by `scheduler/module.py` and `processors/module.py` via bare `from core...` imports. Don't delete; untangle by restructuring.
- Root `module.py` and `api_router.py` are entrypoints checked by `tests/api/test_module_links.py`.
- Route controllers live in `api/routes/controllers/`.

## API models
- Request/response models live in `api/schemas/` (`common.py` has the shared pieces). No `Dict[str, Any]` bodies.
- Success paths `return ok(data, message)` / `paged(...)` with `response_model=Envelope[X]` / `Page[X]` so FastAPI validates and documents them; error paths return `utils/response_builder.error_response` (a JSONResponse, which bypasses the response model) and are documented with `responses=error_responses(...)`.
- Open-ended documents (listings, inventory, alerts) subclass `OpenPayload`: declared fields validated, unknown keys pass through, `id`/`_id`/`created_at`/`updated_at` dropped, `$`/dotted keys rejected. Pass `model.to_data()` (exclude_unset) to modules. Output models subclass `Record` and carry no constraints so legacy documents still load.
- Operation IDs are `<tag>_<function name>` (used by generated FlutterFlow clients); keep function names stable. `tests/api/test_schemas.py` fails if any body or 2xx response is untyped.

## Versioning
- `api_router` (`api/router_api.py`) is mounted at `API_V1_PREFIX` (`/api/v1`) in `api/main.py`; health is mounted at the root only. Add new routers to `api_router`, never to `app` directly. Tests call `/api/v1/...`.
- The same router is also mounted unversioned with `include_in_schema=False` as deprecated aliases; `DeprecationMiddleware` adds `Deprecation`/`Link` headers and logs each legacy route once. Drop that `include_router` line in `api/main.py` when the logs show no legacy traffic.
- Breaking changes go in a new `/api/v2` router mounted alongside v1; don't change v1 contracts in place.
- slowapi uses `key_style="endpoint"` so limits are per view function; keep it, otherwise the aliases double the login/register quotas.

## Roadmap
Work one session per group; tick items off here as they land. Keep each group to its own commit(s).
Priority order of open groups: Before tester release -> Session 3+ (observability first, Sentry helps testers) -> dealr RVs & towables -> Pricing -> Auth expansion (A2-A5 wait on provider accounts).

### Before tester release (next)
- [x] Vehicle `category` on inventory, sellr/listr listings and search filters (`car`, `truck`, `motorcycle`, `motorhome_a`, `motorhome_b`, `motorhome_c`, `travel_trailer`, `fifth_wheel`, `toy_hauler`, `truck_camper`, `other`). Must land before testers create data; adding it later needs a data migration. Default existing docs to `car` in a migration.
- [ ] Replace placeholders testers will hit: watchr alerts/subscriptions persisted per user (list/delete real), f1ndr `/vehicles` and `/listings/*` querying stored listings, market value returns `null` (not `0`) until Pricing lands so clients don't show $0.
- [ ] Scheduled trinn tasks never run (see Session 2 note): decide on an in-process stopgap (start the scheduler in the lifespan while `WORKERS=1`) or wait for ARQ.
- [ ] A1 Password reset, pulled forward from Auth expansion: testers will forget passwords.

### Session 1 - Security fixes + wire existing code (Tier 0 + 1)
- [ ] `.env` was committed in `0756fc7`/`1de097f`: user rotates any real secrets (history rewrite only if user explicitly asks).
- [x] Replace unsalted SHA-256 `hash_password` in `api/routes/auth_routes.py` with bcrypt (already in requirements).
- [x] Move `users_db`/`sessions_db` in-memory dicts to `DocumentStore`, unique index on email.
- [x] Stop returning `str(e)` to clients; return generic message + request ID, log details server-side.
- [x] Auth by default: only dealr inventory routes use `require_user`; decide public routes, protect the rest at router level.
- [x] Register in `api/main.py`: `RequestIDMiddleware`, request timer, error-handler middleware, `apply_secure_headers`, global exception handlers from `api/errors/`.
- [x] Attach slowapi `limiter` (`app.state.limiter`, exception handler), strict limits on `/auth/login` and `/auth/register`.
- [x] Consolidate the remaining health endpoints to one.

### Session 2 - Deployment (Tier 2)
- [x] `run_backend.py`: host/port/reload/workers from settings (currently hard-coded `127.0.0.1`, `reload=True`, unreachable in Docker).
- [x] `DEBUG` default `False`; fail production startup on weak/missing `JWT_SECRET_KEY`.
- [x] Dockerfile: non-root user, `HEALTHCHECK`, multi-stage build.
- [x] docker-compose: pin `mongo:7`, move `admin/admin` credentials to env. (Compose pins `mongo:8.3`; integration tests use `mongo:7`. Align when choosing the production version.)
- [x] Split health into `/health/live` and `/health/ready` (Mongo ping, scheduler state). Liveness never checks dependencies; readiness returns 503 `NOT_READY`.
- Note: nothing starts the trinn scheduler (`api/startup.py` never calls `get_scheduler().start()`), so `/trinn/schedule` stores tasks that never run. Intended fix is the ARQ worker (Redis + background work item).

### Session 3+ - Enterprise features (Tier 3, one session each)
- [x] Pydantic request/response models instead of `Dict[str, Any]` bodies (`api/schemas/` exists, unused). `/health` still returns untyped data (waiting on the live/ready split).
- [x] API versioning under `/api/v1`. Legacy unversioned aliases still mounted (deprecated); remove once unused.
- [ ] Observability: structured JSON logs with request ID, Prometheus metrics, OpenTelemetry tracing, Sentry.
- [x] Auth maturity: refresh-token revocation via `jti`, roles/scopes, account lockout, email verification, audit log.
- [ ] Redis + background work (one session, decided: ARQ on Redis, no leader lock). Scrapers and the scheduler currently run inside the API process, so with multiple workers or replicas scheduled jobs run twice and in-memory slowapi limits don't hold. One Redis instance covers all of it:
  - ARQ worker as a separate process/compose service; `trinn/utils/scheduler.py` loop and scraper jobs become ARQ functions + `cron_jobs`. API only enqueues. ARQ is asyncio-native, so it fits the async `run()` contract (Celery doesn't).
  - slowapi `Limiter(storage_uri=settings.REDIS_URL)`; fall back to `memory://` when `REDIS_URL` is unset (tests, dev), same pattern as `DocumentStore`.
  - Scraper result cache in Redis with TTLs.
  - `/health/ready` also pings Redis; production fails startup if Redis is unreachable.
- [ ] Data layer: versioned index management, backups with tested restore, TTL indexes (check `db/ttl_db.py` usage).
- [ ] CI: ruff, mypy, pip-audit/bandit, coverage threshold, image build, pinned deps / lock file (`pyproject.toml` deps empty).
- [ ] Resilience: timeouts on all outbound calls, graceful shutdown draining scraper jobs.

### dealr: RVs & towables (needs `category` from Before tester release)
- [ ] R1 Category-specific typed fields, validated per category (discriminated on `category`): length, dry weight, GVWR, sleeps, slide-outs, hitch type, fresh/grey/black tank sizes; mileage, engine and chassis only for motorized units. Towables may have short/odd VINs (already allowed by `LooseVIN`). VIN decode gives the type/chassis only; floorplan details are entered manually.
- [ ] R2 Search/filter by category and RV attributes (f1ndr search, sellr listings, dealr inventory); regenerate the FlutterFlow client.
- [ ] R3 Marketplace categories in listr and scrapers (Kijiji/Facebook/AutoTrader RV sections; add RVTrader as a platform).

### Pricing (after R1: comps must match within a category)
- [ ] P1 One pricing provider interface in `f1ndr/intelligence/market.py` replacing both `compute_market_value` stubs (`f1ndr/intelligence/market.py` returns 0.0; `f1ndr/utils/utils.py` only discounts the listing's own price). dealr ingest and sellr auto-pricing use it.
- [ ] P2 Local market comps: persist scraped listings with location + category, add a location to dealer accounts, match year/make/model/trim within a mileage band and radius; return median, p25/p75, comp count, confidence. Asking prices, not sold prices; check marketplace terms before commercial use.
- [ ] P3 Book values behind config flags: Canadian Black Book for cars/trucks (confirm whether its specialty valuations cover RVs) and an RV guide (e.g. J.D. Power) for RVs. Needs commercial agreements (`docs/ACCOUNTS_SETUP.md`).
- [ ] P4 dealr pricing panel endpoint: book values + local comps + suggested price range.

### Auth expansion - social login + MFA (decided: FastAPI owns auth, not Firebase; one session each, in order)
Decisions: provider sign-in is trusted (no extra MFA after social login). SMS via Twilio (prefer Twilio Verify). Clients: FlutterFlow app ("Custom Authentication", social buttons as custom actions, app stores the rotated refresh token), f1ndr.ca and dealrlink.com web apps.
Per product (dealr proposed, confirm with user): f1ndr = email/password + Google, Apple, Microsoft, Facebook. dealr (business) = email/password + Google + Microsoft, MFA required for `dealer`/`admin` roles; per-dealership SSO later if asked.
Provider accounts are owned by admin@triverdant.ca; secrets go in env/secret manager, never in chat or git. Account checklist (what to create, what each produces): `docs/ACCOUNTS_SETUP.md`.
- [ ] A1 Password reset: emailed single-use token, revokes all sessions, must not bypass MFA once it exists.
- [ ] A2 Google + Apple + Microsoft: `auth_identities` collection (unique `provider`+`subject`), mobile posts provider ID token to `/auth/oauth/{provider}`, web uses authorization-code + PKCE redirect; verify via provider JWKS (`httpx`). Auto-link by email only when provider marks it verified (never for Microsoft; key on `tid`+`oid`). Apple: name only on first sign-in, private relay email, token revocation on account deletion.
- [ ] A3 MFA core: login returns `mfa_required` + short-lived `mfa_pending` token; TOTP (secret encrypted at rest, new key setting) + 10 hashed single-use recovery codes; per-token and per-user attempt limits; fresh login required to change MFA.
- [ ] A4 Email OTP as an MFA method (weak while reset goes to the same inbox; not allowed as the only factor for dealr).
- [ ] A5 Facebook (Graph `debug_token`; iOS Limited Login gives an OIDC token) + Twilio SMS OTP (country allowlist CA/US, Fraud Guard, never the only factor).
