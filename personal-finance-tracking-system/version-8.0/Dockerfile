# The browser client, built first so its output is a plain directory to copy.
#
# Separate stage, so the 300 MB of node_modules and the toolchain never reach
# the runtime image — only frontend/dist/ does.
FROM node:22-alpine AS frontend

WORKDIR /frontend

# The manifests before the source, so editing a component does not re-install
# the dependency tree on the next build.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# The service itself.
FROM python:3.12

WORKDIR /app

# Again: requirements before the source. A code edit now rebuilds from the pip
# layer instead of downloading wheels again.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./
COPY --from=frontend /frontend/dist ./frontend/dist

# .dockerignore keeps the local database and log out of the image, so the
# directories they live in have to be recreated.
RUN mkdir -p data logs

ENV DB_PATH=data/expense.db \
    LOG_LEVEL=INFO \
    LOG_TO_STDOUT=true \
    SESSION_TTL_HOURS=12

# The database lives on a volume so a rebuild does not take the data with it.
#
# The log deliberately does not. It goes to stdout, which is what `docker logs`
# and every log collector built on top read; the file handler is only there for
# the case where someone runs the image without one. Persisting it would mean
# preserving the half of the record that is *allowed* to be lossy, while the
# audit trail — the half that is not — is already in this volume.
VOLUME ["/app/data"]

EXPOSE 8000

# Checking the port rather than a health route: this answers whether the
# process is serving, which is exactly what the orchestrator needs to know.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json').read()"

# The API *is* the service. It also serves the built SPA at /app/, so a single
# container behind a single port is the whole deployed artifact.
#
# JWT_SECRET_KEY and COOKIE_SECURE are deliberately not defaulted here — a
# signing key baked into an image is not a secret, and the app fails loudly at
# the first login rather than silently minting tokens anyone can forge. Pass
# them at run time:
#   docker run -e JWT_SECRET_KEY=... -e COOKIE_SECURE=true -p 8000:8000 ...
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
