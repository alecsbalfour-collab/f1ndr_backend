# FlutterFlow integration notes

State of the FlutterFlow frontend wiring — what's entered, what works, and the gotchas that cost time.

## API groups (as configured in FlutterFlow)

| Group | Base URL | Headers | Variables |
|---|---|---|---|
| `health` | `https://f1ndr-backend-docker.onrender.com` | none | none |
| `f1ndr-api` | `https://f1ndr-backend-docker.onrender.com/api/v1` | `Content-Type: application/json`, `Authorization: Bearer [accessToken]` | `region` (String, `calgary`), `pageSize` (Int, `20`) |
| `dealr` | `https://f1ndr-backend-docker.onrender.com/api/v1` | same | `pageSize` |

dealr stays separate: different audience (dealer app), all calls need `inventory:*` scopes (dealer/admin token — a regular user gets 403).

## App State variables (persisted)

`accessToken`, `refreshToken`, `userId`, `userEmail`.

Auth calls: `POST /auth/register` `{email, password, name}` and `POST /auth/login` `{email, password}` → save `data.access_token`, `data.refresh_token`, `data.user.user_id`, `data.user.email`. `POST /auth/refresh` `{refresh_token}` rotates BOTH tokens — save both (old refresh token is dead after). On 401: refresh, retry once, then bounce to login.

## Calls entered so far

- `health`: `liveCheck` (`GET /health/live`), `readyCheck` (`GET /health/ready`) — paths `$.data.checks.mongo.ok`, `$.data.checks.scheduler.status`.
- `dealr`: `dealrStatus`, `getInventory`, `createInventory`, `updateInventory`, `deleteInventory`.
- `f1ndr-api` sellr + listr: `sellrStatus`, `getSellrListings` (public; `user_id` param filters to "my listings"), `getSellrListing`, `createSellrListing`, `updateSellrListing`, `deleteSellrListing`; `listrStatus`, `getPlatforms` (`data.platforms` drives the push-platform checkbox list), `pushListing`, `updateListrListing`.
- Still to enter: auth calls (register/login/refresh/reset), `unifiedListings`, `compareGroups`, `raw{Platform}`, `search`, `f1ndrVehicles`, watchr alerts/matches/subscriptions.
- Admin-only (skip for the consumer app): `/scrapers/search`, `/trinn/*`.

## Response envelope — THE pattern

Every response: `{success, message, data, timestamp}`; paged lists add `pagination: {total, page, page_size, total_pages, has_next}`. All JSON paths start with `data.` / `$.data.`. Errors: `{success:false, message, error_code, details.validation_errors, request_id}` — surface `message` in a snackbar.

`price` can be null → fall back to `price_text`, then "Contact". `image` can be null → placeholder.

## Gotchas already hit (don't re-step on these)

1. **Blank params** — FlutterFlow sends `?category=` (empty string) for unbound params. Backend now coerces `""`→unset for `category`/`subcategory`/`region`-style Literal params (commit 50a7dec), so blanks are safe — but still leave filters unbound until a dropdown drives them.
2. **`platform` is a QUERY param** on listr push/update: `?platform=kijiji`. Easiest is literally in the path (`/listr/listings?platform=kijiji`); a Parameters row only sends when it has a non-empty bound value.
3. **`[var]` placeholders in JSON bodies send literally** unless declared in the call's Variables section — `[price]` arrives as the string "[price]" → parse errors. Declare variables first, or test with `{"title":"Test","category":"vehicles","price":15000}`.
4. **Body type must be JSON**, not form/multipart — else `body: Input should be a valid dictionary`.
5. **`/api/v1` once** — in the group base OR the path, never both (`/api/v1/api/v1/...` → 404).
6. **Deploy lag** — local commits only reach the API after `git push` + Render rebuild (~3-5 min); a 422 right after a fix usually means the old build is still serving. Check Render → Events.
7. **Null values hide from FlutterFlow's path picker** — type the path manually (`$.data.status`) and mark nullable, or pick it up from a GET response instead.

## Known gap

`POST /listr/listings` (push to platform) requires `inventory:write` (dealer/admin) — regular users get 403, so consumer "post once, push everywhere" needs an owner-scoped push endpoint (e.g. `POST /listr/push` taking a sellr `listing_id` + platform, ownership-checked). Flagged, not yet built.
