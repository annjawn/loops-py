#!/usr/bin/env bash
set -euo pipefail

uv sync --extra dev
uv run ruff check .
uv run pytest
uv build

if [[ "${1:-}" == "--publish" ]]; then
  uv publish
fi
