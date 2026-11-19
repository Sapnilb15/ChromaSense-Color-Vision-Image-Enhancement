# Increment 01: Project skeleton

**Status:** Standard
**Depends on:** none
**SRS IDs:** structure and stack (`dev/structure.md` directory tree, `dev/architecture.md` Stack); SRS-NFR-005 (`.gitignore` keeps session data out of the repository)

### Main rules

- Create folders, package markers, and project metadata only. Write no application behavior.
- Use only paths from the directory tree in **section 6 of `00-master-context.md`**.
- Do not touch `dev/`, `CHANGELOG.md`, `docs/ChromaSense_SRS.docx`, or `TEAM_ROLES.md`.

### Capability

The two Python packages exist and install: `color_engine` and `chromasense`.

### What may change

- New files: `.gitignore`, `.env.example`, `src/color_engine/pyproject.toml`, `src/portal/pyproject.toml`, and every `__init__.py` in the tree.
- New empty folders from the tree, each kept with a `.gitkeep` until a later increment puts a file in it. Remove `src/.gitkeep`.

### What must stay

- `README.md`, `CHANGELOG.md`, `TEAM_ROLES.md`, `dev/`, and `docs/ChromaSense_SRS.docx` are unchanged.

### Implementation notes

1. **`src/color_engine/pyproject.toml`**: setuptools build, name `color_engine`, `requires-python = ">=3.11"`, dependencies `numpy`, `Pillow`, `scikit-image`, `scikit-learn`. Optional `test` extra: `pytest`, `pytest-cov`, `daltonlens`. Package data: `data/*`. It must not list FastAPI or any web package.
2. **`src/portal/pyproject.toml`**: setuptools build, name `chromasense`, dependencies `color_engine`, `fastapi`, `uvicorn`, `python-multipart`, `jinja2`. Optional `test` extra: `pytest`, `httpx` (for FastAPI's `TestClient` only), `playwright`, `axe-playwright-python`, `ruff`, `import-linter`. Package data: `web_ui/**/*`. Do not add an AI, HTTP client, or database dependency to the runtime list.
3. **`.gitignore`**: `.env`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, `*.egg-info/`, `.venv/`, and a local `data/` folder for session images.
4. **`.env.example`**, names with defaults and no secrets:
   ```
   CHROMASENSE_DATA_DIR=/data
   CHROMASENSE_CONFUSION_THRESHOLD=10
   CHROMASENSE_PALETTE_COLORS=12
   CHROMASENSE_IDLE_MINUTES=30
   ```
   The palette color count of 12 is `derived` from release 0.5.
5. Add `__init__.py` to every package folder in the tree, including each `filter_<N>_<name>/` directory and `web_api/routers/`.

### Verification

- In a clean Python 3.11 virtual environment: `pip install -e "./src/color_engine[test]"` and then `pip install -e "./src/portal[test]"` both succeed.
- `python -c "import color_engine, chromasense"` exits 0.
- Every folder in the tree exists.

### Main rules (repeated)

- Create folders, package markers, and project metadata only. Write no application behavior.
- Use only paths from the directory tree.
- Do not touch `dev/`, `CHANGELOG.md`, `docs/ChromaSense_SRS.docx`, or `TEAM_ROLES.md`.
