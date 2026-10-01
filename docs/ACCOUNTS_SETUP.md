# External accounts checklist

Every account is owned by **admin@triverdant.ca**. Keys and secrets go in a password manager and the host's
environment/secret settings only, never in chat or git. Tick items off as they are created.

## Needed to start testing

- [ ] **SMTP / email provider** for `notifications@f1ndr.ca`: verification emails, password reset (A1), email codes (A4).
  - Produces: host, port, username, password -> `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM`.
- [ ] **Test-environment MongoDB** (e.g. Atlas), with its own database user.
  - Produces: connection string -> `MONGODB_URI`, `MONGODB_DB_NAME`.
- [ ] **Hosting** for the test backend (Render, Docker on a VPS, ...): somewhere to set the environment variables.
  - Also set: `ENVIRONMENT`, `JWT_SECRET_KEY` (48+ random chars), `CORS_ORIGINS`, `FLUTTERFLOW_API_KEY`, `ADMIN_EMAILS`.
- [ ] **Rotate the secrets** that were in the `.env` committed in `0756fc7`/`1de097f` (Mongo, JWT, SMTP, API keys).

## Social sign-in (roadmap A2, A5)

- [ ] **Google Cloud Console** (f1ndr + dealr): OAuth consent screen, OAuth client IDs for iOS, Android and Web.
  - Produces: client IDs per platform, web client secret.
- [ ] **Apple Developer Program** (f1ndr; paid yearly membership, approval can take time): Sign in with Apple.
  - Produces: Team ID, Services ID, Sign in with Apple key (Key ID + `.p8` file).
  - App Store rules generally require a privacy-focused sign-in option such as Apple when Google/Facebook login is offered; check the current guideline at submission.
- [ ] **Microsoft Entra ID** app registration (f1ndr + dealr), supporting work/school and personal Microsoft accounts.
  - Produces: Application (client) ID, client secret.
- [ ] **Meta for Developers** (f1ndr only). Public use needs Meta app review, which is slow; apply early.
  - Produces: App ID, App Secret.

## Two-step verification (roadmap A3-A5)

- [ ] **Twilio**, using the **Verify** product, for SMS codes (A5).
  - Upgrade from trial (trial can only text verified numbers); restrict to Canada/US; enable Fraud Guard.
  - Produces: Account SID, Auth Token, Verify Service SID.
  - SMS is never the only second factor; TOTP authenticator apps (A3) need no external account.
- Email codes (A4) reuse the SMTP account above.

## Optional / later

- [ ] **Canadian Black Book**: commercial agreement for book-value pricing in dealr (roadmap P3). Ask whether its specialty valuations cover RVs.
- [ ] **RV valuation guide** (e.g. J.D. Power RV values): needed for RV/towable pricing if CBB doesn't cover them (roadmap P3).
- [ ] **Sentry**: error reporting for testers' crashes.

## Suggested order

1. SMTP, Mongo, hosting, secret rotation (blocks testing).
2. Google, Microsoft, Apple.
3. Twilio.
4. Meta: build last, but start the app review early.
