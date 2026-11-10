#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

die() {
  echo "error: $*" >&2
  exit 1
}

# --- Preflight: nothing below this block runs unless the repo is releasable ---

branch=$(git rev-parse --abbrev-ref HEAD)
[ "$branch" = "main" ] || die "releases are cut from main (currently on '${branch}')"

[ -z "$(git status --porcelain --untracked-files=no)" ] ||
  die "working tree has uncommitted changes; commit or stash them first"

git fetch --quiet origin main
git merge-base --is-ancestor origin/main HEAD ||
  die "local main is behind or has diverged from origin/main; pull first"

uv lock --check >/dev/null 2>&1 || die "uv.lock is out of date; run 'uv lock' and commit it first"

uv run ruff check
uv run ruff format --check
uv run pytest -q

# --- Compute the new version (CalVer: YYYY.MM.patch) ---

current=$(grep -oP '(?<=^version = ")[^"]+' pyproject.toml)
IFS='.' read -r year month patch <<< "$current"

now_year=$(date +%Y)
now_month=$(date +%m)

# If year or month changed, reset patch to 0; otherwise bump patch
if [ "$year" != "$now_year" ] || [ "$month" != "$now_month" ]; then
  new_version="${now_year}.${now_month}.0"
else
  new_version="${year}.${month}.$((10#$patch + 1))"
fi
tag="${new_version}"

if git rev-parse -q --verify "refs/tags/${tag}" >/dev/null ||
  [ -n "$(git ls-remote --tags origin "refs/tags/${tag}")" ]; then
  die "tag ${tag} already exists"
fi

echo "Bumping version: ${current} -> ${new_version}"

# --- Bump, commit, tag, push ---

sed -i "s/^version = \"${current}\"/version = \"${new_version}\"/" pyproject.toml
uv lock

git commit -m "release ${new_version}" -- pyproject.toml uv.lock
git tag "$tag"

# Atomic: main and the tag land together or not at all. Only this tag is pushed.
git push --atomic origin main "$tag"
