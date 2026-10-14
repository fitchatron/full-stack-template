# Infra

Terraform for the Coolify setup: one project, a `dev` and a `production`
environment, each with its own Postgres and its own copy of the app stack.

Terraform owns the long-lived shape. GitHub Actions owns deploys.

## Layout

```
infra/
├── modules/
│   └── app-environment/      # everything one environment needs
│       ├── main.tf           # Postgres, backups, app stack, env vars
│       ├── variables.tf
│       ├── outputs.tf
│       └── versions.tf
├── shared/                   # the Coolify project + dev environment
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── versions.tf
│   └── terraform.tfvars.example
├── envs/
│   ├── dev/                  # calls the module for dev
│   └── prod/                 # calls the module for production
└── .gitignore
```

Three roots, three state files. `envs/dev` and `envs/prod` read `shared`'s
state for the project and environment IDs, so a prod apply can never touch
dev and vice versa.

## Who owns what

| Thing | Owner | Changes when |
|---|---|---|
| Project, environments | `shared/` | basically never |
| Postgres, backups | `envs/*` | sizing or schedule changes |
| Compose structure, domain, env vars | `envs/*` | you add a service or a setting |
| `IMAGE_TAG` and the running version | GitHub Actions | every push to main / every tag |

Terraform sets `IMAGE_TAG` once on create and then ignores it, so an apply
never rolls back what Actions deployed.

Note that `compose.prod.yaml` is read by Terraform: a change to its structure
(new service, new port) reaches Coolify on the next `terraform apply` for
each environment, not on a deploy.

## What compose.prod.yaml needs to look like

Coolify substitutes `${...}` from the env vars Terraform sets on the service.

```yaml
services:
  nginx:
    image: ghcr.io/OWNER/REPO-nginx:${IMAGE_TAG}
    depends_on: [frontend, backend]
    # no ports: Coolify's proxy (Traefik) routes the domain to this container

  frontend:
    image: ghcr.io/OWNER/REPO-frontend:${IMAGE_TAG}

  backend:
    image: ghcr.io/OWNER/REPO-backend:${IMAGE_TAG}
    environment:
      DATABASE_URL: ${DATABASE_URL}
      ENVIRONMENT: ${ENVIRONMENT}
      LOG_LEVEL: ${LOG_LEVEL}
```

No `build:` keys, no Postgres service (Coolify runs it separately).

## First run

1. In Coolify:
   - **Settings → Advanced:** enable API access.
   - **Security → API Tokens:** create a token for Terraform with these
     permissions:
     - `read`
     - `write`: create and update projects, databases, services and env vars
     - `deploy`
     - `read:sensitive`: lets compose files and DB URLs read back, which
       avoids spurious diffs

     `root` also works but grants more than this needs.
   - **Servers:** note your server's UUID.

   Give GitHub Actions its own token: `deploy` to trigger deployments, plus
   `write` if the workflow updates `IMAGE_TAG` through the API.

2. Give Terraform the token. Pick one option:

      **Option A: in `secrets.auto.tfvars`** (fine for a single local machine)

   In each root (`shared`, `envs/dev`, `envs/prod`), create
   `secrets.auto.tfvars` alongside `terraform.tfvars`:
   ```hcl
     coolify_token = "1|abc123..."
   ```
   Terraform loads `*.auto.tfvars` automatically. Keep secrets here and plain
   config in `terraform.tfvars`. The file is gitignored.

   **Option B: environment variable** (for a dedicated machine or CI)

   Leave `coolify_token` out of every `terraform.tfvars` and set:
   ```sh
     export COOLIFY_TOKEN=...
   ```
   
   Put it in your shell profile or inject it from a password manager. If you
   type it inline, the value ends up in your shell history.

   How the provider picks a token:
   - `coolify_token` in `terraform.tfvars` wins.
   - If it's unset, the provider falls back to `COOLIFY_TOKEN`.
   - Don't use `TF_VAR_coolify_token` as well, or you can't tell which token
     is in use.
   - To switch from A to B, delete the `coolify_token` line from all three
     `terraform.tfvars` files.

3. Shared:
```sh
   cd shared
   cp terraform.tfvars.example terraform.tfvars   # fill in
   terraform init && terraform apply
```

4. Each environment:
```sh
   cd ../envs/dev
   cp terraform.tfvars.example terraform.tfvars   # fill in
   terraform init && terraform apply
   terraform output -raw deploy_webhook           # → GitHub dev environment secret
```
   Same for `envs/prod`.

5. Push to main (or tag) so Actions builds the images and triggers the first
   deploy. The stack stays stopped until then.

## Things to know

- **State is a secret.** It holds the generated DB passwords and anything in
  `app_secrets`, in plain text. Keep the machine's disk encrypted and back
  the three `terraform.tfstate` files up somewhere safe; losing them means
  re-importing everything.
- **`prevent_destroy`** is on both databases and the dev environment.
  Comment it out deliberately if you ever want to tear something down.
- **Private GHCR images:** the Coolify server has to be able to pull them.
  Either make the packages public or `docker login ghcr.io` on the server
  with a read-only token.
- **Provider is pre-1.0.** Pinned to `0.1.26`; read the changelog before
  bumping.
- **Moving state later:** add a `backend` block to each root, run
  `terraform init -migrate-state`, and switch the `terraform_remote_state`
  blocks in `envs/*` from `local` to the new backend.
