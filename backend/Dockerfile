ARG PYTHON_VERSION=3.14.7
FROM python:${PYTHON_VERSION}-slim AS base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl && \
  rm -rf /var/lib/apt/lists/*

# Install uv from the official image into /bin so it's usable by any user
# (the install script puts it in /root/.local/bin, which appuser can't read).
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /uvx /bin/

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
  --disabled-password \
  --gecos "" \
  --home "/nonexistent" \
  --shell "/sbin/nologin" \
  --no-create-home \
  --uid "${UID}" \
  appuser

# Copy dependency files first for better caching
COPY .python-version pyproject.toml ./

# Changing the UV_LINK_MODE silences warnings about not being able to link 
# files since the cache and sync target are on separate file systems.
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR="/tmp/.uv_cache"
ENV UV_PYTHON_CACHE_DIR="/tmp/.uv_cache/python"
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_COMPILE_BYTECODE=1

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /tmp/.uv_cache to speed up subsequent builds.
# Install dependencies
RUN --mount=type=cache,target=/tmp/.uv_cache \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  uv sync --frozen --no-install-project --no-dev

# Put the venv on PATH so the app runs without `uv run`, which would try to
# re-lock/sync into the root-owned /app at startup.
ENV PATH="/app/.venv/bin:$PATH"

# Copy alembic file separately to cache layer
COPY alembic.ini ./ 

# Copy the source code into the container.
COPY app/ ./app/

# Switch to the non-privileged user to run the application.
USER appuser

# Trust X-Forwarded-* headers from the reverse proxy so client
# IPs and https scheme are correct. 
# Safe only while the container is reachable solely through the proxy.
ENV FORWARDED_ALLOW_IPS="*"

# Expose the port that the application listens on.
EXPOSE 8000

# Let Docker know when the app is actually serving requests.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://localhost:8000/docs > /dev/null || exit 1

# Run the application.
CMD ["fastapi", "run"]
