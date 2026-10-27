# Fetch an OAuth token in a pre-request script

This collection does not use Bruno's built-in OAuth2 auth. Instead, a
before-request script calls the token endpoint with `axios`, saves the token in
a runtime variable, and lets the request header use that variable.

## Files

| File | What it does |
| --- | --- |
| `opencollection.yml` | Basic collection metadata; no OAuth2 auth |
| `Get Users.yml` | Pre-request script, runtime token cache, and Authorization header |
| `environments/local.yml` | Token URL, client ID, client secret, and API URL |

## How it works

1. The request starts.
2. The pre-request script reads `tokenUrl`, `clientId`, and `clientSecret` from
   the active environment.
3. It checks for a cached token in the runtime variables `accessToken` and
   `accessTokenExpiresAt`.
4. If there is no valid token, it sends a client-credentials request to the
   token endpoint with `axios`.
5. It stores the new token and expiry with `bru.setVar()`.
6. The request URL and header are resolved:

   ```text
   GET {{baseUrl}}/users
   Authorization: Bearer {{accessToken}}
   ```

7. On the next send, the script finds the cached runtime token and skips the
   token request.

Runtime variables live in memory. They are shared by later requests in the
same session, but they are not written to collection YAML and disappear when
the session ends.

The script refreshes the token when it is within 60 seconds of expiry.

## Try it

1. Start the stack from the repository root:

   ```bash
   podman compose up -d
   ```

2. In Bruno, import the `my-collection-pre-request` folder.
3. Select the `local` environment.
4. Open `Get Users` and click **Send**.
5. The first send logs something like:

   ```text
   Fetched new OAuth token; expires in 21599 seconds
   ```

6. Send again in the same session. It logs:

   ```text
   Reusing cached OAuth token
   ```

7. Check the counters:

   ```bash
   curl http://127.0.0.1:8788/stats
   ```

   `api_requests` increases for each API call, but `unique_tokens_seen` stays
   at `1` while the runtime token is valid.

## Run it with the CLI

```bash
cd my-collection-pre-request
bunx @usebruno/cli run -r . --env local --iteration-count 2
```

Two iterations share the runtime variables, so the second iteration reuses the
token from the first.

## Notes for new users

- This collection puts the script on the request itself. In Bruno, select the
  request and open **Scripts** to see it.
- `require("axios")` is available in Bruno scripts for this demo.
- The header uses `{{accessToken}}` directly. The pre-request script only needs
  to set the variable; it does not need to call `req.setHeader()`.
- The client secret is plain text in this environment because the focus is the
  token flow. See `my-collection-secrets` for secret handling.
