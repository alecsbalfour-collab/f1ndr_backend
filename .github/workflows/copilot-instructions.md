# Triverdant Engineering Instructions (f1ndr / DealrLink / Trinn)

## Owner & Licensing
- Owner: Alec Balfour — Triverdant (`admin@triverdant.ca`).
- All repositories (`f1ndr_backend`, `f1ndr_ui`, `dealr`) are proprietary ("All Rights Reserved"). Never add open-source licenses (MIT/Apache/GPL) or commit secrets/keys.

## Architecture & Conventions
1. **Backend (`D:\f1ndr\DEV\f1ndr_backend` — FastAPI + Python 3.14 + MongoDB)**:
   - Follow `AGENTS.md` strictly.
   - Module contract (`f1ndr`, `trinn`, `sellr`, `listr`, `dealr`, `watchr`): each exports `async def run(action: str, data: dict) -> dict` and `get_<name>_config() -> dict`. Dependency direction: `sellr`/`dealr` -> `trinn` -> `listr`.
   - Storage: always use `DocumentStore` (`db/document_store.py`), never raw Motor clients or module-level in-memory lists. Use `datetime.now(timezone.utc).replace(tzinfo=None)` (never deprecated `datetime.utcnow()`).
   - API routes live under `/api/v1` (`api/router_api.py`). Every route must use `require_user` or `require_scopes(...)` unless explicitly listed in `PUBLIC_ROUTES` in `tests/api/test_route_auth.py`.
   - Ownership (`user_id`, `owner_id`) comes from JWT claims (`server_fields` on `OpenPayload`), never request bodies. Non-owners get `404` (`owns()` in `api/dependencies/auth.py`).
   - Schemas (`api/schemas/`): success responses use `return ok(data, msg)` / `paged(...)` with `response_model=Envelope[X]` / `Page[X]`; errors use `error_response(...)` with `responses=error_responses(...)`. Keep `<tag>_<function>` operation IDs stable and refresh `openapi_f1ndr.json` when routes/schemas change.
   - Verify backend changes with: `.venv/Scripts/python.exe -m pytest -q`.

2. **Frontends (`D:\f1ndr\DEV\f1ndr_ui\f1ndr_frontend` & `D:\dealr\DEV\dealr_frontend` — Next.js 16 + React 19 + Tailwind v4)**:
   - Next.js 16 conventions: `proxy.ts` replaces `middleware.ts`; `params` and `searchParams` are Promises and must be `await`ed.
   - API calls go exclusively through `lib/api/client.ts` (attaches `Authorization: Bearer`, shares one in-flight `POST /api/v1/auth/refresh` promise across concurrent 401s, rotates both tokens).
   - Never hand-edit `lib/api/types.ts`; regenerate it from the backend OpenAPI spec with `node scripts/generate-api-types.mjs`.
   - Styling uses Tailwind v4 `@theme inline` CSS variables backed by `lib/theme.ts` (`lightTheme` / `darkTheme`, primary `#3a8dff` / `#4aa8ff`, dark surfaces `#0d1117` / `#1a1f27`). Note: web CSS 8-digit hex is `#RRGGBBAA` (not Flutter's `#AARRGGBB`).
   - Verify frontend changes with: `npx tsc --noEmit`, `npm run lint`, and `npm run build`.