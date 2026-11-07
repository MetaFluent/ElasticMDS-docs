#!/usr/bin/env bash
# Publishes the documentation for one release to GitHub Pages.
#
# Usage: tools/publish.sh <version> [--default]
#
#   <version>   the docs version to publish, e.g. 6.0 (a new version, or a republish of an existing one)
#   --default   also make it the version a reader lands on
#
# Publishes the tip of master, which holds the documentation of the current release. It stops, changing nothing,
# unless master is checked out, clean and the same as origin/master, the local gh-pages is the same as (or behind)
# origin/gh-pages, and the strict build passes. Then it deploys with mike, pushes gh-pages, waits for GitHub Pages
# to build it and checks that the version's page is served.
set -euo pipefail

repo=$(cd "$(dirname "$0")/.." && pwd)
pages_url=https://metafluent.github.io/ElasticMDS-docs
gh_repo=MetaFluent/ElasticMDS-docs

fail() {
	echo "publish: $*" >&2
	exit 1
}

version=${1:-}
default=no
case ${2:-} in
	'') ;;
	--default) default=yes ;;
	*) fail "unknown option '$2' (usage: tools/publish.sh <version> [--default])" ;;
esac
[[ $version =~ ^[0-9]+\.[0-9]+$ ]] || fail "give the version as <major>.<minor>, e.g. 6.0 (usage: tools/publish.sh <version> [--default])"

cd "$repo"
[[ -x .venv/bin/zensical && -x .venv/bin/mike ]] ||
	fail "no tool environment in .venv: set it up as README.md says (python3 -m venv .venv; .venv/bin/pip install -r requirements.txt)"
export PATH="$repo/.venv/bin:$PATH" # mike runs zensical from PATH

branch=$(git branch --show-current)
[[ $branch == master ]] || fail "check out master to publish (on '$branch'); master holds the documentation of the current release"
[[ -z $(git status --porcelain) ]] || fail "the working tree has changes; commit or remove them first"

git fetch -q origin master gh-pages
[[ $(git rev-parse HEAD) == $(git rev-parse origin/master) ]] ||
	fail "master is not the same as origin/master; pull or push first"
git rev-parse -q --verify gh-pages >/dev/null || git branch -q gh-pages origin/gh-pages
git merge-base --is-ancestor gh-pages origin/gh-pages ||
	fail "the local gh-pages has commits origin/gh-pages does not; look at them (git log origin/gh-pages..gh-pages) before publishing"
git update-ref refs/heads/gh-pages origin/gh-pages

echo "publish: strict build of master $(git rev-parse --short HEAD)"
zensical build --strict

echo "publish: deploying version $version"
mike deploy --push "$version"
if [[ $default == yes ]]; then
	mike set-default --push "$version"
fi

published=$(git rev-parse gh-pages)
echo "publish: waiting for GitHub Pages to build gh-pages $(git rev-parse --short "$published")"
for attempt in $(seq 60); do
	read -r status commit < <(gh api "repos/$gh_repo/pages/builds/latest" -q '.status + " " + .commit')
	if [[ $commit == "$published" && $status == built ]]; then
		break
	fi
	[[ $commit == "$published" && $status == errored ]] && fail "GitHub Pages failed to build gh-pages $published"
	(( attempt == 60 )) && fail "GitHub Pages had not built gh-pages $published after 5 minutes (latest build: $status, $commit)"
	sleep 5
done

code=$(curl -s -o /dev/null -w '%{http_code}' "$pages_url/$version/")
[[ $code == 200 ]] || fail "$pages_url/$version/ answered $code"
echo "publish: version $version is live at $pages_url/$version/"
mike list
