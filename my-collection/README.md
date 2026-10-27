# Collection-level OAuth2 with `auth: inherit`

This collection shows the simplest Bruno OAuth2 setup: define the OAuth2
configuration once on the collection, then tell each request to inherit it.

## What to look at

| File | What it does |
| --- | --- |
| `opencollection.yml` | Holds the OAuth2 client-credentials configuration |
| `Get Users.yml` | Calls `GET /users` with `http.auth: inherit` |
| `environments/local.yml` | Stores the base URL, token URL, client ID, and secret |

## How it works

1. The collection defines an OAuth2 `client_credentials` flow in
   `opencollection.yml`.
2. The token URL and client credentials are filled from the active environment:
   `{{tokenUrl}}`, `{{clientId}}`, and `{{clientSecret}}`.
3. `Get Users.yml` contains `http.auth: inherit`.
4. When the request is sent, Bruno asks the OAuth server for a token.
5. Bruno caches the token and reuses it until it is close to expiry.
6. Bruno adds the token to the request as `Authorization: Bearer <token>`.

The important part is:

```yaml
http:
  auth: inherit
```

Without that line, the request does not use the collection OAuth2 settings.

## Try it

1. Start the local stack from the repository root:

   ```bash
   podman compose up -d
   ```

2. In Bruno, import the `my-collection` folder.
3. Select the `local` environment.
4. Open `Get Users` and click **Send**.
5. You should get `200 OK` with a list of users.
6. Send the request again in the same session. Bruno reuses the cached token
   instead of fetching a new one.
7. Check the API counters:

   ```bash
   curl http://127.0.0.1:8788/stats
   ```

   `api_requests` increases with each request. `unique_tokens_seen` stays at
   `1` while the token is cached.

## Run it with the CLI

```bash
cd my-collection
bunx @usebruno/cli run -r . --env local
```

## Common problems

- **401 Unauthorized**: confirm the `local` environment is selected and the
  OAuth server is running on port `8787`.
- **Connection refused**: start the stack with `podman compose up -d`.
- **A new token is fetched every time**: the cache may have been cleared, or
  the OAuth container was restarted.
- **OAuth settings are ignored**: check that the request still has
  `auth: inherit`.

The client secret is stored in plain text in `environments/local.yml` because
this collection is about inheritance, not secret handling. See the
`my-collection-secrets` collection for safer options.
