# Infra

Terraform for the Coolify setup: one project with a `dev` and a `production`
environment, each with its own Postgres and app.

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
| The app resource, its domain and env vars | Terraform `envs/*` | you add a setting |
| The migrations runner | Terraform `envs/*` | image bumps |
| `compose.prod.yml` | the repo | any merge |
| When to deploy | GitHub Actions | every push to main (dev) / release tag (prod) |

## Layout

```
infra/
├── modules/
│   ├── database/        # Postgres + backup schedule for one environment
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
     - `write`: create and update projects, environments, databases and
       applications
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

3. Shared:
   ```sh
   cd shared
   cp terraform.tfvars.example terraform.tfvars   # fill in
   terraform init && terraform apply
   ```

4. Each environment (database + app). See the next section for why the
   domain waits:
   ```sh
   cd ../envs/dev
   cp terraform.tfvars.example terraform.tfvars   # fill in, leave domain unset
   terraform init && terraform apply
   ```
   Same for `envs/prod` when you're ready for production.

## The app

`modules/app` creates the Coolify application with Docker Compose from
`/compose.prod.yml`, the predefined network on (so the stack reaches
Postgres by name) and auto deploy off (CI deploys through the webhook after
pushing images; auto deploy would ship the previous images on every push).

It also sets the app's env vars. The database values come straight from the
database module, and `SECRET_KEY` is generated. Add anything else with `app_env` in `terraform.tfvars` or
`app_secrets` in `secrets.auto.tfvars`. Terraform owns the whole set: a
variable added in the Coolify UI is removed on the next apply.

**The domain takes two applies.** Coolify won't accept a compose domain
until a deploy has read the compose file from the repo, so:

1. `terraform apply` with `domain` unset.
2. Deploy once, from the UI or with the webhook below.
3. Set `domain = "https://..."` in `terraform.tfvars` and apply again. It's
   attached to the `nginx` service.

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

## Deploying

| Environment | Coolify app tracks | Deploys when |
|---|---|---|
| dev | `main` | a push to `main` passes the tests |
| prod | `production` | a release tag (`x.y.z`) passes the tests |

Auto deploy is off, so pushes alone don't deploy. `.github/workflows/deploy.yml`
runs the tests, then calls the environment's deploy webhook:
```sh
curl -fsS "$COOLIFY_WEBHOOK" -H "Authorization: Bearer $COOLIFY_TOKEN"
```
Coolify then pulls the branch, builds and restarts the stack.

**Migrations** run first, in `deploy-db.yml`. If `alembic upgrade head`
fails, the deploy doesn't run and the current app stays up.

They run on the environment's own self-hosted runner (`modules/runner`), a
Coolify service on the Coolify network with labels `coolify` plus the
GitHub environment name. Terraform puts the DB settings in the runner's
env, so jobs reach Postgres by its internal hostname and GitHub holds no DB
credentials. The runner is ephemeral: it re-registers with a clean
workspace after every job.

It registers itself with `github_runner_token` in each env's
`secrets.auto.tfvars`: a fine-grained PAT for this repo only, with
**Administration: Read and write**. Every job on the runner can read the
DB settings, so only use it for deploy workflows, never pull requests.

**Releasing:** tag on `main` as usual (`git tag 1.2.0 && git push --tags`).
CI fast-forwards `production` to the tagged commit and deploys prod.
`production` is only a marker for what prod runs: never commit to it.

**Rolling back prod:** point `production` at an older tag and redeploy:
```sh
git push -f origin 1.1.0:production
curl -fsS "$COOLIFY_WEBHOOK" -H "Authorization: Bearer $COOLIFY_TOKEN"
```

**Setup, once:**
- Create the branch before applying `envs/prod`:
  `git push origin main:production`.
- Protect `production` so only GitHub Actions can push to it.
- Create GitHub environments named `development` and `production` (what
  `set-environment.yml` outputs). Each gets `COOLIFY_WEBHOOK`
  (`terraform output deploy_webhook`) and a `COOLIFY_TOKEN` with `deploy`
  permission.

## Things to know

- **State is a secret.** It holds the generated DB passwords in plain text.
  Keep the machine's disk encrypted and back the three `terraform.tfstate`
  files up somewhere safe; losing them means re-importing everything.
- **`prevent_destroy`** is on both databases and the dev environment.
  Comment it out deliberately if you ever want to tear something down.
- **Changing the DB password** (e.g. by tainting `random_password.db`)
  updates the app's env vars in the same apply, but the running app keeps
  the old one until you redeploy.
- **Admin database access:** both databases are public on the server's IP
  (dev `5433`, prod `5434`, see `terraform output public_port`) so admins
  can connect with psql or a GUI. Allow those ports only from known IPs in
  the firewall. The app never uses them; `DATABASE_URL` is always the
  internal URL. Set `is_public = false` in `envs/*/main.tf` to close them.
- **Postgres version:** the module defaults to `postgres:17`; local dev uses
  18. Bump `postgres_image` once you've confirmed Coolify's Postgres resource
  handles 18's new data directory layout.
- **Provider is pre-1.0.** Pinned to `0.1.26`; read the changelog before
  bumping.
- **Moving state later:** add a `backend` block to each root, run
  `terraform init -migrate-state`, and switch the `terraform_remote_state`
  blocks in `envs/*` from `local` to the new backend.
