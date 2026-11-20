# Increment 21: Professional documentation

**Status:** Standard
**Depends on:** 20
**SRS IDs:** SRS-NFR-008

### Main rules

- Change only docstrings, comments, the Ruff settings in the two `pyproject.toml` files, and documents. Change no behavior, signature, test, or template.
- Every public module, class, and function in `src/` gets a PEP 257 docstring in Google style. Ruff's pydocstyle `D` rules enforce it.
- Describe only behavior that exists. No document makes a medical or diagnostic claim (SRS-NFR-006).

### Capability

The code and the documentation set meet a named standard: Google-style docstrings checked by Ruff, and documents whose content follows ISO/IEC/IEEE 26514:2022 for audience, purpose, task steps, reference completeness, messages, and limits.

### What may change

- `src/portal/pyproject.toml` and `src/color_engine/pyproject.toml`: the `[tool.ruff.lint]` settings only.
- Docstrings and comments in `src/color_engine/color_engine/` and `src/portal/chromasense/`.
- `README.md`, `CHANGELOG.md`, `docs/user-guides/user-guide.md`, `docs/code/color-engine.md`, `docs/code/portal.md`, `docs/diagrams/README.md`.

### What must stay

- Every code line other than docstrings and comments, every test, the templates, CSS, and JavaScript code.
- `docs/ChromaSense_SRS.docx`, `docs/enhancement-evaluation-v0.5.md`, `docs/acceptance-results.md`, the diagram sources and SVGs, `TEAM_ROLES.md`, and `dev/`.

### Implementation notes

1. Make the same change in both `pyproject.toml` files:

   ```toml
   [tool.ruff.lint]
   select = ["E", "F", "W", "I", "B", "UP", "D"]
   ignore = ["D105", "D107"]

   [tool.ruff.lint.pydocstyle]
   convention = "google"

   [tool.ruff.lint.per-file-ignores]
   "tests/**" = ["D"]
   ```

   `D105` (magic methods) and `D107` (`__init__`) are ignored because Google style documents constructor arguments in the class docstring. If an empty `__init__.py` raises `D104`, give it a one-line package docstring rather than ignoring the rule.
2. List the findings with `docker compose run --rm dev ruff check . --select D` and fix them part by part:
   - **Color Engine** (`models.py`, `rules/`, `pipeline/`): every public function documents `Args`, `Returns`, and `Raises`, with array shapes and dtypes, and the `DecodeError` reasons for `decode_1`.
   - **Application Core** (`core/`): ports, models, and policy get docstrings. Each use case `execute` documents `Args`, `Returns`, and `Raises`, including `UploadRejected` and `NoImageInSession`.
   - **Storage Adapter, Web API, Server Main**: short docstrings that state the job.
   - Keep existing summary lines that already describe the code.
3. Review each document against the checklist below and fill only the gaps. Put a short "Who this is for" line at the top of the user guide, both developer notes, and the diagrams README. Add an audience column to the README document list. Under `CHANGELOG.md` › 1.0 › Added, add the docstring check.

### Documentation checklist

| Document | Must contain |
| --- | --- |
| Every document | The audience and purpose at the top; headings for navigation; terms that match the SRS (protan, deutan, severity, confusable pair); every link and anchor resolves; no medical or diagnostic claim |
| `README.md` | What the app does, requirements, build and run, the address for another device on the local network, the checks, and an index of the documents |
| User guide | Numbered task steps with the expected result of each; the input limits; every status message with its meaning and what to do next; keyboard and screen reader use; data retention |
| Developer notes | Every public filter, rule, use case, endpoint, and setting; the filter order; how to run the tests |
| Diagrams README | A text alternative for each SVG; the source link; the command that regenerates it |
| `CHANGELOG.md` | Each release with Added, Changed, and Removed entries |
| Code | Ruff `D` clean; `Args`, `Returns`, and `Raises` on the public Color Engine API and on each use case `execute`; a header comment on each JavaScript file |

### Verification

- `docker compose run --rm dev ruff check .` reports no findings, with the `D` rules on.
- `docker compose run --rm dev ruff format --check .` passes.
- Every other command in `structure.md` still passes, with the same test counts as increment 20.
- `git diff` on `src/` changes only docstrings, comments, and the Ruff settings.
- Each row of the documentation checklist is met. Record the review in `tracking.md`.

### Main rules (repeated)

- Change only docstrings, comments, the Ruff settings, and documents. Change no behavior, signature, test, or template.
- Every public module, class, and function in `src/` gets a Google-style docstring, enforced by Ruff.
- Describe only behavior that exists. No document makes a medical or diagnostic claim.
