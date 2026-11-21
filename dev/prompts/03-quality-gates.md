# Increment 03: Quality gates

**Status:** Standard
**Depends on:** 02
**SRS IDs:** structure and hard constraints (`dev/architecture.md` Hard constraints: inward dependencies, Color Engine without the web framework)

### Main rules

- Add lint, format, dependency-rule, and CI configuration only. Write no application behavior.
- Write each dependency rule from the hard constraints. Do not weaken a rule later to make code pass.

### Capability

Ruff, import-linter, and the GitHub Actions workflow check every later increment.

### What may change

- `src/portal/pyproject.toml`: add `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.importlinter]`, and the contracts below.
- `src/color_engine/pyproject.toml`: add `[tool.pytest.ini_options]` and `[tool.coverage]` settings.
- New file: `.github/workflows/ci.yml`.

### What must stay

- Dependencies and package data from increments 01 and 02.

### Implementation notes

1. Ruff: `target-version = "py311"`, `line-length = 100`, `src = [".", "../color_engine"]`, lint rules `E`, `F`, `W`, `I`, `B`, `UP`.
2. import-linter: `root_packages = ["chromasense", "color_engine"]`, `include_external_packages = true`. Contracts, all `forbidden` type:
   - `chromasense.core` must not import `chromasense.web_api`, `chromasense.storage`, `chromasense.main`, `fastapi`, `starlette`, or `uvicorn`.
   - `color_engine` must not import `chromasense`, `fastapi`, `starlette`, `uvicorn`, or `httpx`. import-linter can forbid only installed top-level packages, so the rule that Color Engine makes no network calls is checked by review and by its tests running without network access.
   - `chromasense.web_api` must not import `chromasense.storage`.
   - `chromasense.storage` must not import `chromasense.web_api`.
3. `.github/workflows/ci.yml`, on pull requests and pushes to `main`:
   - Build the `engine-test` target: `docker build --target engine-test .`
   - `docker compose build dev`
   - `docker compose run --rm dev ruff check .`
   - `docker compose run --rm dev ruff format --check .`
   - `docker compose run --rm dev lint-imports --config src/portal/pyproject.toml`
   - `docker compose run --rm dev pytest src/color_engine/tests --cov=color_engine --cov-fail-under=70`
   - `docker compose run --rm dev pytest src/portal/tests`
   CI is expected to fail on the test steps until those tests exist. That is not a failure of this increment.

### Verification

- `docker compose run --rm dev ruff check .` and `docker compose run --rm dev ruff format --check .` pass on the skeleton.
- `docker compose run --rm dev lint-imports --config src/portal/pyproject.toml` passes and lists four kept contracts.
- A temporary `import fastapi` added to `src/color_engine/color_engine/__init__.py` makes `lint-imports` fail. Remove it afterward.

### Main rules (repeated)

- Add lint, format, dependency-rule, and CI configuration only. Write no application behavior.
- Write each dependency rule from the hard constraints. Do not weaken a rule later to make code pass.
