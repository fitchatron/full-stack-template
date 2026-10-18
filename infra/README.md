# Infra

Terraform for the Coolify setup: one project with a `dev` and a `production`
environment, each with its own Postgres.

The app itself is **not** in Terraform. It's a git-based Docker Compose
application created once in the Coolify UI. On every deploy, Coolify reads
`compose.prod.yml` from the repo, so compose changes ship with the merge
that makes them.

## Who owns what

| Thing | Owner | Changes when |
|---|---|---|
| Project, environments | Terraform `shared/` | basically never |
| Postgres + backups per environment | Terraform `envs/*` | sizing or schedule changes |
| The app resource, its domain and env vars | Coolify UI (once per environment) | you add a setting |
| `compose.prod.yml` | the repo | any merge |
| Images and deploys | GitHub Actions | every push to main (dev) / tag (prod) |

## Layout

```
infra/
├── modules/
│   └── database/        # Postgres + backup schedule for one environment
├── shared/              # the Coolify project + dev environment
└── envs/
    ├── dev/             # calls the module for dev
    └── prod/            # calls the module for production
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
     - `write`: create and update projects, environments and databases
     - `read:sensitive`: lets the DB connection URL read back, which avoids
       spurious diffs

     `root` also works but grants more than this needs.
   - **Servers:** note your server's UUID.

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

4. Each environment's database:
   ```sh
   cd ../envs/dev
   cp terraform.tfvars.example terraform.tfvars   # fill in
   terraform init && terraform apply
   ```
   Same for `envs/prod` when you're ready for production.

5. Create the app in Coolify (once per environment). See the next section.

## Creating the app in Coolify

In the project, open the environment (`dev` or `production`), then:

1. **+ New → Private Repository (with GitHub App)**, pick the repo and
   branch `main`. (First time only: add the GitHub App under **Sources**
   and grant it access to this repo.)
   - **Build Pack:** Docker Compose
   - **Base Directory:** `/`
   - **Docker Compose Location:** `/compose.prod.yml`
   - **Advanced → Auto Deploy:** off. CI triggers deploys through the
     webhook after the images are pushed; leaving this on deploys stale
     images on every push.

2. **Domains:** set the domain on the `nginx` service only.
3. **Advanced → Docker Compose:** Set Predefined network to *Connect to predefined network*. Without it the stack can't reach the Postgres container by name.
4. **Environment Variables:** fill in what the compose file references.
   The database values come from Terraform:
   ```sh
   cd infra/envs/dev
   terraform output -raw database_url
   terraform output -raw postgres_password
   terraform output postgres_user postgres_db
   ```
   Also set `IMAGE_TAG` (`dev` for dev) and the backend's other required
   settings (`SECRET_KEY`, `PROJECT_NAME`, `FIRST_SUPERUSER`,
   `FIRST_SUPERUSER_PASSWORD`).
5. **Webhooks:** copy the **Deploy Webhook** URL. It goes into the GitHub
   environment as the `COOLIFY_WEBHOOK` secret, alongside a `COOLIFY_TOKEN`
   with `deploy` permission.

Don't deploy from the UI until the images exist in GHCR. The first push to
main builds them and triggers the deploy.

## What compose.prod.yml needs to look like

```yaml
services:
  nginx:
    image: ghcr.io/fitchatron/full-stack-template-nginx:${IMAGE_TAG}
    pull_policy: always
    depends_on: [frontend, backend]
    # no ports: Coolify's proxy (Traefik) routes the domain to this container

  frontend:
    image: ghcr.io/fitchatron/full-stack-template-frontend:${IMAGE_TAG}
    pull_policy: always

  backend:
    image: ghcr.io/fitchatron/full-stack-template-backend:${IMAGE_TAG}
    pull_policy: always
    environment:
      DATABASE_URL: ${DATABASE_URL}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      SECRET_KEY: ${SECRET_KEY}
      PROJECT_NAME: ${PROJECT_NAME}
      FIRST_SUPERUSER: ${FIRST_SUPERUSER}
      FIRST_SUPERUSER_PASSWORD: ${FIRST_SUPERUSER_PASSWORD}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
```

- No `build:` keys. Images come from GHCR, so Coolify only pulls.
- No Postgres service. Terraform's database runs separately.
- `pull_policy: always` matters. Dev reuses the `dev` tag, and without it
  Docker keeps the image it already has instead of pulling the new one.

## Deploying

On push to main, the workflow:
1. builds and pushes the images to GHCR tagged `dev`
2. calls the dev deploy webhook:
   ```sh
   curl -fsS "$COOLIFY_WEBHOOK" -H "Authorization: Bearer $COOLIFY_TOKEN"
   ```

Coolify then pulls the repo at the latest `main`, reads `compose.prod.yml`,
pulls the images and restarts the stack. Push the images before calling the
webhook, or Coolify deploys the previous build.

## Things to know

- **State is a secret.** It holds the generated DB passwords in plain text.
  Keep the machine's disk encrypted and back the three `terraform.tfstate`
  files up somewhere safe; losing them means re-importing everything.
- **`prevent_destroy`** is on both databases and the dev environment.
  Comment it out deliberately if you ever want to tear something down.
- **Changing the DB password** (e.g. by tainting `random_password.db`) does
  not update the app. Re-copy the outputs into Coolify afterwards.
- **Admin database access:** both databases are public on the server's IP
  (dev `5433`, prod `5434`, see `terraform output public_port`) so admins
  can connect with psql or a GUI. Allow those ports only from known IPs in
  the firewall. The app never uses them; `DATABASE_URL` is always the
  internal URL. Set `is_public = false` in `envs/*/main.tf` to close them.
- **Private GHCR images:** the Coolify server has to be able to pull them.
  Either make the packages public or `docker login ghcr.io` on the server
  with a read-only token.
- **Postgres version:** the module defaults to `postgres:17`; local dev uses
  18. Bump `postgres_image` once you've confirmed Coolify's Postgres resource
  handles 18's new data directory layout.
- **Provider is pre-1.0.** Pinned to `0.1.26`; read the changelog before
  bumping.
- **Moving state later:** add a `backend` block to each root, run
  `terraform init -migrate-state`, and switch the `terraform_remote_state`
  blocks in `envs/*` from `local` to the new backend.
