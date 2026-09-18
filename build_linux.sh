#!/usr/bin/env bash
# Build wrapper for J.A.R.V.I.S. on Linux
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$PROJECT_ROOT/jarvis.sh" build "$@"
