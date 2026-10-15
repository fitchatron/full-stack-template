# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.14.7
FROM python:${PYTHON_VERSION}-slim AS base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  ca-certificates \
  curl

# Install uv
# Download the installer
ADD https://astral.sh/uv/0.13.1/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
# ARG UID=10001
# RUN adduser \
#   --disabled-password \
#   --gecos "" \
#   --home "/nonexistent" \
#   --shell "/sbin/nologin" \
#   --no-create-home \
#   --uid "${UID}" \
#   appuser

# Copy alembic file separately to cache layer
COPY alembic.ini ./ 

# Copy dependency files first for better caching
COPY .python-version pyproject.toml ./

# Changing the UV_LINK_MODE silences warnings about not being able to link 
# files since the cache and sync target are on separate file systems.
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR="/tmp/.uv_cache"
ENV UV_PYTHON_CACHE_DIR="/tmp/.uv_cache/python"

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/uv to speed up subsequent builds.
# Install dependencies
RUN --mount=type=cache,target=/tmp/.uv_cache \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  uv sync --frozen --no-install-project

# Switch to the non-privileged user to run the application.
# USER appuser

# Copy the source code into the container.
COPY app/ ./app/

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application.
CMD ["uv", "run", "fastapi", "run"]
