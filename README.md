# Elastic MDS documentation

Source for the Elastic MDS customer documentation, published at https://metafluent.github.io/ElasticMDS-docs/.
The site is built with [Zensical](https://zensical.org) from `mkdocs.yml` and `docs/`, with one version per
release (a version drop-down in the header).

## Set up

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    export PATH="$PWD/.venv/bin:$PATH"     # mike runs zensical from PATH

## Preview and check

    zensical serve              # live preview at http://localhost:8000
    zensical build --strict     # fails on a broken link or anchor

## Branches and versions

- `dev` holds the documentation for the next release. Edit it on `dev`, alongside the product change it documents;
  nothing on `dev` reaches readers until it is published.
- `master` holds the documentation of the current release, and every published version is built from it.

## Publish a release

1. Merge `dev` into `master` (`git merge --no-ff dev`) and push `master`.
2. On `master`, run:

       tools/publish.sh <version>               # e.g. 6.0, or a republish of a version already out
       tools/publish.sh <version> --default     # when it becomes the current release

The script refuses to publish unless `master` is checked out, clean and the same as `origin/master`, and the strict
build passes. It deploys the version with mike, pushes the `gh-pages` branch, waits for GitHub Pages to build it and
checks that the pages it published are served. `mike list` shows the published versions and their aliases.

`--default` also moves the **`latest`** alias to the version being published, and points the landing page at that
alias. So `.../latest/<Page>` always serves the current release, which is what metafluent.com links to: those links
need no attention at a release, and a reader's bookmark follows too. Publish without `--default` to correct a
version that is already out, which leaves `latest` where it is.

[TOOLING.md](TOOLING.md) lists the tools, their versions and where each comes from.
