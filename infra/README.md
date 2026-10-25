# Infra

Terraform for the Coolify setup: one project with a `dev` and a `production`
environment, each with its own Postgres, app and migrations runner.

The app is a git-based Docker Compose application cloned through a GitHub
App. Terraform manages the Coolify resource and its env vars; on every
deploy, Coolify reads `compose.prod.yml` from the repo, so compose changes
ship with the merge that makes them.

## Who owns what

| Thing | Owner | Changes when |
|---|---|---|
| GitHub App source | Coolify UI (once per Coolify instance) | basically never |
| Project, environments | Terraform `shared/` | basically never |
| Postgres + backups per environment | Terraform `envs/*` | sizing or schedule changes |
| Postgres roles and grants | Terraform `envs/*` (`modules/db-roles`) | rarely |
| The app resource, its domain and env vars | Terraform `envs/*` | you add a setting |
| The migrations runner | Terraform `envs/*` | image bumps |
| `compose.prod.yml` | the repo | any merge |
| When to deploy | GitHub Actions | every push to main (dev) / release tag (prod) |

## Layout

```
infra/
├── modules/
│   ├── database/        # Postgres + backup schedule for one environment
│   ├── db-roles/        # migrator / backend / readonly Postgres roles
│   ├── app/             # the compose app + its env vars for one environment
│   └── runner/          # self-hosted Actions runner for one environment
├── shared/              # the Coolify project + dev environment
└── envs/
    ├── dev/             # calls the modules for dev
    └── prod/            # calls the modules for production
```

Three roots, three state files. `envs/dev` and `envs/prod` read `shared`'s
state for the project and environment IDs, so a prod apply can never touch
dev and vice versa.

## First run

1. In Coolify:
   - **Settings → Advanced:** enable API access.
   - **Security → API Tokens:** create a token for Terraform with these
     permissions:
     - `read`
     - `write`: create and update projects, environments, databases,
       applications and services (the runner)
     - `read:sensitive`: lets the DB connection URL read back, which avoids
       spurious diffs

     `root` also works but grants more than this needs.
   - **Servers:** note your server's UUID.
   - **Sources → + Add → GitHub App:** create the app, install it on this
     repo, and note the source's UUID. Terraform doesn't manage this.

   GitHub Actions gets its own token later, with `deploy` only.

2. Give Terraform the token. Pick one option:

   **Option A: in `secrets.auto.tfvars`** (fine for a single local machine)

   In each root (`shared`, `envs/dev`, `envs/prod`), create
   `secrets.auto.tfvars` alongside `terraform.tfvars`:
   ```hcl
   coolify_token = "1|abc123..."
   ```
   Terraform loads `*.auto.tfvars` automatically. Keep secrets there and
   plain config in `terraform.tfvars`. Both are gitignored.

   **Option B: environment variable** (for a dedicated machine or CI)

   Leave `coolify_token` out of every tfvars file and set:
   ```sh
   export COOLIFY_TOKEN=...
   ```
   Put it in your shell profile or inject it from a password manager. If you
   type it inline, the value ends up in your shell history.

   How the provider picks a token:
   - `coolify_token` in a tfvars file wins.
   - If it's unset, the provider falls back to `COOLIFY_TOKEN`.
   - Don't use `TF_VAR_coolify_token` as well, or you can't tell which token
     is in use.
   - To switch from A to B, delete the `coolify_token` line from each
     `secrets.auto.tfvars`.

   Each env's `secrets.auto.tfvars` also needs `github_runner_token` (see
   [The migrations runner](#the-migrations-runner)).

3. Shared:
   ```sh
   cd shared
   cp terraform.tfvars.example terraform.tfvars   # fill in
   terraform init && terraform apply
   ```
   `project_id` (kebab-case, e.g. `full-stack-template`) names every Coolify
   resource, so keep it stable: changing it renames them all. The
   human-friendly name is `app_name` in `envs/*/terraform.tfvars`, passed to
   the app as `PROJECT_NAME`.

4. Each environment (database, roles, app and runner). See
   [The app](#the-app) for why the domain waits:
   ```sh
   cd ../envs/dev
   cp terraform.tfvars.example terraform.tfvars   # fill in, leave domain unset
   terraform init && terraform apply
   ```
   One apply creates the database, its roles, the app and the runner, and
   hands each the credentials it needs. Terraform creates the roles by
   logging in to Postgres through an SSH tunnel, so open it first (see
   [Database access](#database-access)); it can be open before the database
   exists. Before creating the roles it checks every 2s, for up to 45s
   (`ready_timeout`), that a real Postgres answers through the tunnel: a new
   database's public port opens a little after Coolify reports it running.
   That needs only `bash`.
   Same for `envs/prod` when you're ready for production; the `production`
   branch must exist first (see [Setup, once](#setup-once)).

## The app

`modules/app` creates the Coolify application with Docker Compose from
`/compose.prod.yml`, the predefined network on (so the stack reaches
Postgres by name) and auto deploy off (CI deploys through the webhook once
tests and migrations pass; auto deploy would ship every push untested).
`terraform apply` doesn't deploy it.

It also sets the app's env vars: `DATABASE_URL` and the `POSTGRES_*` values
for the `backend` database role, a generated `SECRET_KEY`, and `app_name`
as `PROJECT_NAME`. Add anything else with `app_env` in `terraform.tfvars` or
`app_secrets` in `secrets.auto.tfvars`. Terraform owns the whole set: a
variable added or changed in the Coolify UI is reverted on the next apply,
so change them here.

**The domain takes two applies.** Coolify won't accept a compose domain
until a deploy has read the compose file from the repo, so:

1. Point a DNS record for the domain at the server.
2. `terraform apply` with `domain` unset.
3. Deploy once, from the UI or with the webhook below.
4. Set `domain = "https://..."` in `terraform.tfvars` and apply again. It's
   attached to the `nginx` service.

Traefik then gets a Let's Encrypt certificate, usually within a minute.
Until it does, it serves its own untrusted "TRAEFIK DEFAULT CERT", and
browsers may keep showing that warning until restarted. If it persists,
check **Servers → Proxy → Logs** for ACME errors (DNS not resolving yet, or
port 80 blocked).

**Deploy webhook:** `terraform output deploy_webhook` is the
`COOLIFY_WEBHOOK` secret for the GitHub environment, alongside a
`COOLIFY_TOKEN` with `deploy` permission.

## What compose.prod.yml needs to look like

Coolify clones the branch and builds the images on the server, so the
compose file keeps its `build:` keys and there's no registry.

- No `ports:` on nginx. Coolify's proxy (Traefik) routes the domain to it.
- No Postgres service. Terraform's database runs separately.
- No `container_name:`. Coolify names containers itself.
- No database settings. Terraform sets `DATABASE_URL` and the `POSTGRES_*`
  values as the app's env vars, and `env_file: .env` passes them through.
- A healthcheck on every service, or Coolify's status badge reads "Running
  (no healthcheck)". The Dockerfile `HEALTHCHECK`s count: the backend checks
  `/health` (process up, no DB), nginx checks `/nginx-health`. nginx waits
  for a healthy backend (`condition: service_healthy`).
- `/health/ready` (backend up and DB reachable) isn't routed by nginx yet;
  add a `location` for it before pointing an external monitor or CI at it.

## Deploying

| Environment | Coolify app tracks | Deploys when |
|---|---|---|
| dev | `main` | a push to `main` passes the tests |
| prod | `production` | a release tag (`x.y.z`) passes the tests |

Auto deploy is off, so pushes alone don't deploy. `.github/workflows/deploy.yml`
runs, one deploy per environment at a time (a newer run waits; a running
one is never cancelled, as it may be mid-migration):

1. `set-environment.yml`: a tag means `production`, anything else
   `development`. This picks the GitHub environment and the runner.
2. `test-backend.yml`: lint and tests against a throwaway Postgres. Its
   settings are hardcoded test values, so it needs no secrets.
3. `deploy-db.yml`: `alembic upgrade head`. If it fails, nothing is
   deployed and the current app stays up.
4. `deploy-app.yml`: for prod, fast-forwards `production` to the tag; then
   calls the environment's deploy webhook:
   ```sh
   curl -fsS -X POST "$COOLIFY_WEBHOOK" -H "Authorization: Bearer $COOLIFY_TOKEN"
   ```

Coolify then clones the head of the tracked branch at that moment, builds
the images on the server and restarts the stack. The workflow finishes when
Coolify accepts the request, not when the deploy does: watch the deploy in
Coolify, or turn on its failed-deployment notifications.

On `main`, only changes under `backend/`, `nginx/`, `.github/` or to
`compose.prod.yml` trigger a deploy; tag pushes always do.

Everything runs on GitHub-hosted runners except migrations.

### The migrations runner

Migrations run on the environment's own self-hosted runner
(`modules/runner`), a Coolify service that joins the `coolify` Docker
network through its compose file, with labels `coolify` plus the GitHub
environment name. Terraform puts the DB settings in the runner's env, so
jobs reach Postgres by its internal hostname and GitHub holds no DB
credentials. The runner is ephemeral: it re-registers with a clean
workspace after every job.

It registers itself with `github_runner_token` in each env's
`secrets.auto.tfvars`: a fine-grained PAT for this repo only, with
**Administration: Read and write**. Fine-grained PATs expire; when it
does, the runner goes offline and `deploy-db` jobs queue indefinitely, so
set a reminder. Pin `runner_image` to a specific tag.

Every job on the runner can read the DB settings, so only use it for
deploy workflows, never pull requests.

### Releasing and rolling back

**Releasing:** tag on `main` as usual (`git tag 1.2.0 && git push --tags`).
CI fast-forwards `production` to the tagged commit and deploys prod.
`production` is only a marker for what prod runs: never commit to it. If it
has diverged from `main`, the fast-forward fails and nothing deploys.
`create-release.yml` runs separately on the same tag and needs
`release_notes/<tag>.md`.

**Rolling back prod:** point `production` at an older tag and redeploy:
```sh
git push -f origin 1.1.0:production
curl -fsS -X POST "$COOLIFY_WEBHOOK" -H "Authorization: Bearer $COOLIFY_TOKEN"
```

### Setup, once

- Create the branch before applying `envs/prod`:
  `git push origin main:production`.
- Protect `production` so only GitHub Actions can push to it.
- **Settings → Actions → General → Workflow permissions:** read and write,
  or CI can't move `production`.
- Create GitHub environments named `development` and `production` (what
  `set-environment.yml` outputs). Each gets `COOLIFY_WEBHOOK`
  (`terraform output deploy_webhook`) and a `COOLIFY_TOKEN` (created in
  Coolify under **Security → API Tokens**) with `deploy` permission.

## Things to know

- **State is a secret.** It holds the generated DB passwords, `SECRET_KEY`
  and the runner's PAT in plain text.
  Keep the machine's disk encrypted and back the three `terraform.tfstate`
  files up somewhere safe; losing them means re-importing everything.
- **`prevent_destroy`** is on both databases and the dev environment.
  Comment it out deliberately if you ever want to tear something down.
- **Changing the DB password** (e.g. by tainting `random_password.db`)
  updates the app's and runner's env vars in the same apply, but the
  running app keeps the old one until you redeploy.
- **Database roles** (`modules/db-roles`):

  | Role | Used by | Can |
  |---|---|---|
  | `migrator` | the runner (migrations) | owns the schema: DDL and DML |
  | `backend` | the backend | read and write rows; no DDL |
  | `readonly` | admins | `SELECT` only (`terraform output -raw readonly_password`) |
  | superuser (`postgres_user`, default `app`) | Terraform, break-glass | everything; nothing automatic uses it |

  `backend` and `readonly` reach tables migrator creates later through default
  privileges, which only cover objects **migrator** owns. Never run
  migrations by hand as the superuser: tables it creates stay invisible to
  `backend`.

  **Moving an existing environment onto the roles** (one that ran as the
  superuser before): anything the superuser created still belongs to it, so
  after the apply and before the next deploy, hand it to migrator, e.g.
  `ALTER TABLE alembic_version OWNER TO migrator;` (or drop it while there
  are no migrations). Don't use `REASSIGN OWNED BY postgres`: it owns system
  objects too.
- <a id="database-access"></a>**Database access (Terraform and admins):**
  each database is published on the server (dev `5433`, prod `5434`, see
  `terraform output public_port`), and Terraform assumes it's only
  reachable through SSH:
  - **Block those ports from the internet in the VPS provider's firewall.**
    `ufw` isn't enough: Docker publishes ports through its own iptables
    rules, which bypass `ufw`.
  - Tunnel to them:
    ```sh
    ssh -N -L 5433:127.0.0.1:5433 <user>@<server>   # dev; 5434 for prod
    ```
    Terraform always connects through the tunnel, to `127.0.0.1` on the
    public port (`db_admin_port` if your tunnel's local port differs). Admin GUIs (DBeaver,
    TablePlus, pgAdmin) have SSH tunnel settings built in; connect as
    `readonly`.
  - Postgres TLS isn't used: Coolify's API can't enable it, and SSH
    already encrypts the connection.

  The app never uses these ports; `DATABASE_URL` is always the internal
  URL.
- **Postgres version:** the module defaults to `postgres:18`, matching local
  dev. Override `postgres_image` per environment if you need to pin.
- **Provider is pre-1.0.** Pinned to `0.1.26`; read the changelog before
  bumping.
- **Moving state later:** add a `backend` block to each root, run
  `terraform init -migrate-state`, and switch the `terraform_remote_state`
  blocks in `envs/*` from `local` to the new backend.
