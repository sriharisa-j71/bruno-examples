# Bruno OAuth2 Demo

A small local OAuth2 stack plus four Bruno collections for learning different
ways to get and reuse an access token.

Everything runs on your machine. No external OAuth provider is required.

## What is in this directory

| Path | Purpose |
| --- | --- |
| `compose.yaml` | Starts the OAuth server and demo API |
| `oauth-test-src/` | Source for the OAuth server image |
| `server.py` | Small demo API that validates bearer tokens |
| `my-collection/` | Collection-level OAuth2 auth with `auth: inherit` |
| `my-collection-secrets/` | Secret credentials from `.env` and Bruno secrets |
| `my-collection-pre-request/` | Token fetched by a pre-request script |
| `my-collection-run-request/` | Token request run from another request's script |

## Prerequisites

- Docker or Podman with Compose
- Bruno desktop app
- Python 3 for the local `.env` generator
- Optional: Bun or Node.js if you want to use the Bruno CLI

## Start the stack

```bash
podman compose up -d --build
```

Or with Docker:

```bash
docker compose up -d --build
```

Check that both services are running:

```bash
curl http://127.0.0.1:8788/health
curl -X POST http://127.0.0.1:8787/token \
  -u admin:foobar \
  -d grant_type=client_credentials \
  -d scope=fosite
```

The second command should return JSON containing an `access_token`.

## The Docker image

The OAuth server runs from the local image:

```text
localhost/oauth-test:6h
```

It is built from `oauth-test-src/Dockerfile.6h`. That Dockerfile uses a Go
builder stage, builds the `oauth-test` server, and runs the binary as a
non-root user in a small Alpine image.

The image is a local patch of the upstream `breathbath/oauth-test` project.
The important change is that access tokens live for **6 hours** instead of the
original short lifetime. The value is set in two places in
`oauth-test-src/internal/pkg/auth/provider.go`:

- `accessTokenLifespan`
- `compose.Config.AccessTokenLifespan`

Build it manually if needed:

```bash
podman build -t localhost/oauth-test:6h \
  -f oauth-test-src/Dockerfile.6h \
  oauth-test-src
```

The image has no persistent volume. Its clients, tokens, and signing keys are
kept in memory, so restarting the OAuth container invalidates existing tokens.

The demo client credentials are hardcoded in the image:

```text
client ID:     admin
client secret: foobar
```

This is intentional for the tutorial. Do not use this image or its credentials
in production.

## The OAuth server

The container listens on port `8000`. Compose publishes it on the host as:

```text
http://127.0.0.1:8787
```

Token endpoint:

```text
POST http://127.0.0.1:8787/token
```

Request:

```bash
curl -X POST http://127.0.0.1:8787/token \
  -u admin:foobar \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d grant_type=client_credentials \
  -d scope=fosite
```

Optional audience parameter:

```text
-d audience=admins
```

The response has the usual OAuth2 fields:

```json
{
  "access_token": "...",
  "expires_in": 21599,
  "scope": "fosite",
  "token_type": "bearer"
}
```

`21599` seconds is approximately six hours. The access token is a signed JWT
with issuer `breathbath-test-app` and the `fosite` scope.

There is no discovery endpoint. Configure the token URL directly in Bruno:

```text
http://127.0.0.1:8787/token
```

All collections here use the client-credentials grant.

## The demo API

The API is a Python service from `server.py`. It is published on:

```text
http://127.0.0.1:8788
```

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/health` | No | Health check |
| `GET` | `/users` | Bearer token | Returns demo users |
| `GET` | `/orders` | Bearer token | Returns in-memory orders |
| `POST` | `/orders` | Bearer token | Creates an order |
| `GET` | `/token-info` | Bearer token | Decodes the token claims |
| `GET` | `/stats` | No | API request and unique-token counters |
| `POST` | `/reset` | No | Clears orders and stats |

Create an order:

```bash
curl -X POST http://127.0.0.1:8788/orders \
  -H "Authorization: Bearer <access_token>" \
  -H 'Content-Type: application/json' \
  -d '{"item":"coffee","quantity":1}'
```

The API decodes the JWT and checks:

- the token has not expired
- the token contains the `fosite` scope

It does **not** verify the JWT signature. That keeps the demo simple but means
this API is also for local learning only, not production.

To force a token refresh, restart the OAuth container and reset the API stats:

```bash
podman restart bruno-oauth-demo_oauth_1
curl -X POST http://127.0.0.1:8788/reset
```

If you edit `server.py`, restart the API container:

```bash
podman restart bruno-oauth-demo_api_1
```

## Collections

Import each collection folder separately into Bruno. Each one has its own
`README.md` with step-by-step instructions.

| Collection | What it teaches |
| --- | --- |
| `my-collection` | Define OAuth2 once at collection level and inherit it in requests |
| `my-collection-secrets` | Generate `.env` with Python, or use Bruno's secret store |
| `my-collection-pre-request` | Fetch a token with an `axios` pre-request script and cache it in a runtime variable |
| `my-collection-run-request` | Call a named token request with `bru.runRequest()` and share runtime variables |

Start with `my-collection`, then move to the others in the order above.

### Generate the `.env` file

The `my-collection-secrets` collection includes a small Python generator. It
writes a gitignored `.env` file instead of keeping the secret in YAML:

```bash
cd my-collection-secrets
python3 generate_env.py
```

The secret is chosen from `--client-secret`, then the
`OAUTH_CLIENT_SECRET` environment variable, then the demo default `foobar`:

```bash
OAUTH_CLIENT_SECRET=foobar python3 generate_env.py --force
```

The file is written with owner-only permissions where supported. See
`my-collection-secrets/README.md` for the full walkthrough.

## Run with the Bruno CLI

Run a collection from its own directory:

```bash
cd my-collection
bunx @usebruno/cli run -r . --env local
```

The `.env` example needs the generated file:

```bash
cd my-collection-secrets
python3 generate_env.py
bunx @usebruno/cli run -r . --env dotenv
```

For collections that use the secret environment, the CLI cannot open Bruno's
desktop secret store. Pass the demo value explicitly:

```bash
cd my-collection-run-request
bunx @usebruno/cli run -r . --env local --env-var clientSecret=foobar
```

CLI invocation details are in each collection's README.

## Stop the stack

```bash
podman compose down
```

Or with Docker:

```bash
docker compose down
```

## Security notes

This project is a local teaching demo.

- Credentials are hardcoded and public.
- Traffic uses plain HTTP.
- The demo API checks token claims but not the signature.
- The OAuth server stores state in memory.
- Tokens and client secrets should never be committed to a real repository.

For a real application, use HTTPS, a real authorization server, verified JWT
signatures, and a proper secret manager.
