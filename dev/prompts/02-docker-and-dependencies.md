# Increment 02: Docker and dependencies

**Status:** Standard
**Depends on:** 01
**SRS IDs:** stack and structure (`dev/structure.md` Build and run); SRS-NFR-001 (reference test host of 4 CPU cores and 8 GB)

### Main rules

- Add only build and container files. Write no application behavior.
- The base image is Python 3.11. The portal listens on port 9090.
- `dev/`, `docs/`, and `.git/` never enter the Docker build context.

### Capability

`docker compose build` builds the project, and the `dev`, `engine-test`, `runtime`, and `diagrams` setups exist.

### What may change

- New files: `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.devcontainer/devcontainer.json`.

### What must stay

- Both `pyproject.toml` files from increment 01, apart from fixes needed to install them in the image.

### Implementation notes

1. **`Dockerfile`**, multi-stage on `python:3.11-slim-bookworm`:
   - `base`: sets `PIP_NO_CACHE_DIR=1` and `PYTHONDONTWRITEBYTECODE=1`, `WORKDIR /workspace`.
   - `engine-test`: copies only `src/color_engine`, installs `./src/color_engine[test]`, and runs `pytest src/color_engine/tests`. FastAPI must not be installed in this target.
   - `dev`: copies `src`, installs `-e ./src/color_engine[test]` and then `-e ./src/portal[test]`, and runs `playwright install --with-deps chromium`.
   - `runtime`: copies `src`, installs `./src/color_engine` and then `./src/portal`, and runs `CMD ["python", "-m", "chromasense.main"]`.
2. **`docker-compose.yml`**:
   - `portal`: target `runtime`, port `"9090:9090"`, optional `.env`, `CHROMASENSE_DATA_DIR=/data`, a named volume at `/data`, `cpus: 4`, `mem_limit: 8g`.
   - `dev`: target `dev`, `working_dir: /workspace`, the repository mounted at `/workspace`, `CHROMASENSE_DATA_DIR=/data`, and the same `cpus: 4` and `mem_limit: 8g` as `portal`, so timing tests run on the reference host.
   - `diagrams`: image `minlag/mermaid-cli:11.4.2`, `./docs/diagrams` mounted at `/data`, and an entrypoint that runs `mmdc -i <name>.mmd -o <name>.svg` for every `.mmd` file in `/data`. It builds nothing and is not a dependency of `portal`.
3. **`.dockerignore`**: `dev/`, `docs/`, `.git/`, `.env`, caches, and `data/`.
4. **`.devcontainer/devcontainer.json`**: uses `docker-compose.yml`, service `dev`, workspace folder `/workspace`, and the Python and Ruff extensions.
5. The `engine-test` target has no tests to collect until increment 04, and `pytest` exits with code 5. Do not add placeholder tests. Check this target in increment 04.

### Verification

- `docker compose build` succeeds.
- `docker compose run --rm dev python -c "import color_engine, chromasense"` exits 0.
- `docker compose run --rm dev python -c "import fastapi"` exits 0, and the `engine-test` stage installs no FastAPI (`pip show fastapi` fails there).
- `docker compose config` shows port 9090, 4 CPUs, and 8 GB for `portal`.

### Main rules (repeated)

- Add only build and container files. Write no application behavior.
- The base image is Python 3.11. The portal listens on port 9090.
- `dev/`, `docs/`, and `.git/` never enter the Docker build context.
