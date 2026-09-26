#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd -- "$script_dir/.." && pwd)"

if (( $# > 1 )); then
  printf 'Usage: %s [backup-directory]\n' "$0" >&2
  exit 2
fi

backup_dir="${1:-"$project_dir/backups"}"
mkdir -p -- "$backup_dir"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_file="$backup_dir/worksphere-$timestamp-$$.dump"
temporary_file="$(mktemp "$backup_dir/.worksphere-backup.XXXXXX")"

cleanup() {
  rm -f -- "$temporary_file"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

docker compose --project-directory "$project_dir" -f "$project_dir/docker-compose.yml" exec -T postgres \
  sh -ec 'exec pg_dump --format=custom --no-owner --no-acl --username "$POSTGRES_USER" --dbname "$POSTGRES_DB"' \
  > "$temporary_file"

if [[ ! -s "$temporary_file" ]]; then
  printf 'Database backup failed: pg_dump returned an empty file.\n' >&2
  exit 1
fi

if ! ln -- "$temporary_file" "$backup_file"; then
  printf 'Database backup failed: could not safely create %s.\n' "$backup_file" >&2
  exit 1
fi

printf 'Database backup created: %s\n' "$backup_file"
