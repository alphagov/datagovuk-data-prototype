#!/bin/sh
set -e
uv run flask db upgrade
exec "$@"
