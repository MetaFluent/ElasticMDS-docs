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

- `dev` holds the documentation for the next release; changes go on a task branch off `dev`.
- Each published version is built from the commit that documents that release.

Publish a release's documentation (pushes the `gh-pages` branch, which GitHub Pages serves):

    mike deploy --push <version>             # e.g. 6.0
    mike set-default --push <version>        # when it becomes the version a reader lands on

`mike list` shows the published versions.

## Importing from the wiki

Until the GitHub wiki is retired, `tools/import-wiki.py` brings its pages across: it replaces the pages and images
in `docs/` and the `nav:` section of `mkdocs.yml` with those of one wiki ref.

    python3 tools/import-wiki.py <ElasticMDS.wiki clone> <git-ref>
