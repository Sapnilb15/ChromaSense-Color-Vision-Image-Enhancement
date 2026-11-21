"""Entry point: ``python -m chromasense.main``."""

import uvicorn

from chromasense.main.settings import Settings
from chromasense.main.wiring import build_app


def main() -> None:
    """Read settings from the environment and serve the portal on 0.0.0.0, port 9090."""
    uvicorn.run(build_app(Settings.from_env()), host="0.0.0.0", port=9090)


if __name__ == "__main__":
    main()
