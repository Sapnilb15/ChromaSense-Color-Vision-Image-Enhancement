# Release 1.0 build. Targets: engine-test, dev, runtime (see dev/structure.md).
FROM python:3.11-slim-bookworm AS base
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /workspace

# Color Engine tests run with no web framework installed.
FROM base AS engine-test
COPY src/color_engine src/color_engine
RUN pip install "./src/color_engine[test]"
RUN pytest src/color_engine/tests

FROM base AS dev
# Playwright's bundled Node needs libatomic, which the slim image lacks on arm64.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libatomic1 \
    && rm -rf /var/lib/apt/lists/*
COPY src src
RUN pip install -e "./src/color_engine[test]" \
    && pip install -e "./src/portal[test]"
RUN playwright install --with-deps chromium firefox webkit

FROM base AS runtime
COPY src src
RUN pip install ./src/color_engine \
    && pip install ./src/portal
CMD ["python", "-m", "chromasense.main"]
