# Keeping the client secret out of YAML

This collection uses the same OAuth2 client-credentials flow as
`my-collection`, but shows two ways to avoid putting the client secret directly
in an environment file.

## The two environments

| Environment | Where the secret comes from |
| --- | --- |
| `dotenv` | A `.env` file, read through `{{process.env.OAUTH_CLIENT_SECRET}}` |
| `secret-var` | Bruno's environment **Secrets** tab |

Both environments use the same collection-level OAuth2 settings and the same
`Get Users` request with `auth: inherit`.

## Files

| File | What it does |
| --- | --- |
| `opencollection.yml` | OAuth2 collection auth |
| `Get Users.yml` | Request with `auth: inherit` |
| `environments/dotenv.yml` | Reads the secret from a process environment variable |
| `environments/secret-var.yml` | Declares `clientSecret` as a secret, with no value in YAML |
| `.env` | Local secret value used by the demo |
| `.env.sample` | Example `.env` file |
| `generate_env.py` | Creates `.env` from an argument or environment variable |
| `.gitignore` | Keeps `.env` out of version control |

## Option 1: `.env` file

The `dotenv` environment contains:

```yaml
- name: clientSecret
  value: "{{process.env.OAUTH_CLIENT_SECRET}}"
```

Create the demo `.env` file with the Python helper:

```bash
python3 generate_env.py
```

The script chooses the secret in this order:

1. `--client-secret` argument
2. `OAUTH_CLIENT_SECRET` environment variable
3. the built-in demo value `foobar`

Examples:

```bash
python3 generate_env.py --client-secret foobar
```

```bash
OAUTH_CLIENT_SECRET=foobar python3 generate_env.py
```

If `.env` already exists, the script refuses to replace it unless you add
`--force`:

```bash
python3 generate_env.py --client-secret foobar --force
```

The generated file contains:

```dotenv
OAUTH_CLIENT_SECRET=foobar
```

The script sets the file permissions to owner-only (`0600`) where supported.

How it works:

1. The generator writes `.env` in the collection root.
2. Bruno loads `.env` from the collection root.
3. `{{process.env.OAUTH_CLIENT_SECRET}}` resolves to the generated value.
4. The OAuth2 collection auth uses that value as the client secret.
5. The secret is not written in `dotenv.yml`.

Keep `.env` out of Git. Share `.env.sample` and `generate_env.py` instead.

## Option 2: Bruno secret variable

The `secret-var` environment contains only the name and the secret marker:

```yaml
- secret: true
  name: clientSecret
```

The value is not stored in the YAML file. Set it in Bruno:

1. Import the collection.
2. Open **Environments** and select `secret-var`.
3. Find the `clientSecret` row.
4. Enter `foobar` in the **Secrets** tab or the secret value field.
5. Save the environment.

Bruno stores the value in its local encrypted secret store. It is available
when the collection runs, but it is not exported with the collection or written
back to `secret-var.yml`.

## Try it

1. Start the stack from the repository root:

   ```bash
   podman compose up -d
   ```

2. Generate the `.env` file:

   ```bash
   cd my-collection-secrets
   python3 generate_env.py
   ```

3. In Bruno, import the `my-collection-secrets` folder.
4. Select the `dotenv` environment.
5. Open `Get Users` and click **Send**. You should get `200 OK`.
6. Switch to `secret-var`, enter the secret, and send again.
7. Run:

   ```bash
   curl http://127.0.0.1:8788/stats
   ```

   The counters show that both runs reached the API.

## Run it with the CLI

The CLI cannot open Bruno's desktop secret store. Use `dotenv`, or pass the
secret explicitly for a test:

```bash
cd my-collection-secrets
bunx @usebruno/cli run -r . --env dotenv
```

```bash
bunx @usebruno/cli run -r . --env secret-var --env-var clientSecret=foobar
```

## What not to do

Do not put a real secret directly in an environment YAML file:

```yaml
# Avoid this in a real project
- name: clientSecret
  value: my-real-secret
```

That value would be easy to commit, share, or include in an export. For
production, use a real secret manager and inject the value at runtime.
