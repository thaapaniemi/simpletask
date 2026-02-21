VERSION 0.8

# Base image with Python 3.11 (minimum supported version) and uv for fast package management
python-base:
    FROM python:3.11-slim
    WORKDIR /app
    # Install git (required by GitPython in tests) and uv
    RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
    RUN pip install uv

# Dependencies layer (cached for fast rebuilds)
deps:
    FROM +python-base
    COPY pyproject.toml .
    COPY --dir cli .
    RUN uv pip install --system -e ".[dev]"
    # Install type stubs for mypy
    RUN uv pip install --system types-PyYAML types-jsonschema
    SAVE IMAGE --cache-hint

# Run all tests with coverage (reports coverage, doesn't fail on threshold)
test:
    FROM +deps
    COPY --dir cli tests .
    # Initialize git for tests that need git repository context
    RUN git config --global user.email "test@example.com" && \
        git config --global user.name "Test User" && \
        git init && \
        git add . && \
        git commit -m "Initial commit"
    RUN pytest --cov=cli/simpletask --cov-report=term-missing

# Run linting (ruff)
lint:
    FROM +deps  
    COPY --dir cli tests .
    RUN ruff check .

# Check code formatting (ruff format) - fails if not formatted
format-check:
    FROM +deps
    COPY --dir cli tests .
    RUN ruff format --check .

# Fix formatting and auto-fixable lint issues - writes back to local filesystem
format:
    FROM +deps
    COPY --dir cli tests .
    RUN ruff format .
    RUN ruff check --fix . || true
    SAVE ARTIFACT cli AS LOCAL cli
    SAVE ARTIFACT tests AS LOCAL tests

# Run type checking (mypy)
type-check:
    FROM +deps
    COPY --dir cli tests .
    RUN mypy cli/simpletask

# Run all quality checks (lint + format + types)
check:
    BUILD +lint
    BUILD +format-check
    BUILD +type-check

# Run everything (tests + all quality checks)
all:
    BUILD +test
    BUILD +check

# Interactive development shell
dev:
    FROM +deps
    COPY --dir cli tests .
    RUN echo "simpletask development environment ready"
    RUN echo "Try: simpletask --help, pytest, ruff format ., ruff check ."
    # Use: earthly -i +dev
