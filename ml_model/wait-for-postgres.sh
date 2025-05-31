#!/bin/bash
set -e

host="$1"
shift
cmd="$@"

until pg_isready -h "$host" -p 5432 > /dev/null 2>&1; do
    echo "⏳ Waiting for PostgreSQL at $host:5432..."
    sleep 2
done

echo "✅ PostgreSQL is ready. Running: $cmd"
exec $cmd