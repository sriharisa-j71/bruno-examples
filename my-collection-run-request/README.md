# Run a named token request from another request

This collection shows how to call one Bruno request from another request's
script with `bru.runRequest()`. The token request is a normal request in the
collection, and the token is stored only in runtime variables.

## Files

| File | What it does |
| --- | --- |
| `opencollection.yml` | Basic collection metadata; no token values stored |
| `Fetch Token.yml` | Posts the client credentials and saves the token in runtime variables |
| `Get Users.yml` | Before-request script calls `Fetch Token`, then sends the bearer token |
| `environments/local.yml` | API URL, token URL, client ID, secret, grant type, and scope |

## Request order

`Fetch Token` has sequence `1`. `Get Users` has sequence `2`.

When the whole collection runs:

1. `Fetch Token` sends `POST {{tokenUrl}}` using the client credentials.
2. Its after-response script stores `accessToken` and `accessTokenExpiresAt`
   with `bru.setVar()`.
3. `Get Users` runs.
4. Its before-request script finds the runtime token and reuses it.
5. `Get Users` sends `Authorization: Bearer {{accessToken}}`.

When `Get Users` runs by itself:

1. Its before-request script checks the runtime token and expiry.
2. If there is no valid token, it calls the named request:

   ```javascript
   const response = await bru.runRequest("Fetch Token");
   ```

3. `Fetch Token` runs and its after-response script saves the token.
4. The before-request script also reads the response directly and ensures the
   runtime variables are set.
5. `Get Users` continues with the token.

The runtime token is reused until it is within 60 seconds of expiry. At that
point the script calls `Fetch Token` again.

## No token in YAML

The token is stored with:

```javascript
bru.setVar("accessToken", response.data.access_token);
```

Runtime variables are in memory only. They are not written to
`opencollection.yml` or the environment file, and they disappear when the
session ends.

Do not use `bru.setCollectionVar()` for a token. Collection variables are
persisted to `opencollection.yml`, which would put the bearer token on disk.

## Try it

1. Start the stack from the repository root:

   ```bash
   podman compose up -d
   ```

2. In Bruno, import the `my-collection-run-request` folder.
3. Select the `local` environment.
4. Set `clientSecret` in the environment's **Secrets** tab. The demo value is
   `foobar`.
5. Open `Get Users` and click **Send**.
6. The console shows `Fetch Token` being called, then `Get Users` returning
   `200 OK`.
7. Send again. The script reuses the runtime token and does not call the token
   endpoint.
8. Optionally, run the whole collection. `Fetch Token` runs first, then
   `Get Users` reuses its token.

Check the counters:

```bash
curl http://127.0.0.1:8788/stats
```

`unique_tokens_seen` shows how many different tokens the API has seen.

## Run it with the CLI

The CLI cannot read Bruno's desktop secret store, so pass the demo secret:

```bash
cd my-collection-run-request
bunx @usebruno/cli run -r . --env local --env-var clientSecret=foobar
```

Run only `Get Users`:

```bash
bunx @usebruno/cli run "Get Users.yml" --env local --env-var clientSecret=foobar
```

## Notes for new users

- `bru.runRequest("Fetch Token")` uses the exact request name from
  `Fetch Token.yml`.
- The response from `bru.runRequest()` has `status` and `data`, similar to
  `res` in a normal script. This example uses `response.data.access_token`.
- The token request uses `{{grantType}}`, `{{scope}}`, `{{clientId}}`, and the
  secret `{{clientSecret}}` from the environment.
- Runtime variables are the right choice for short-lived credentials. They keep
  tokens out of YAML and out of exports.
