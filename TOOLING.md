# Tooling

What builds and publishes this site, where each piece lives and where it came from. The site was set up under
MetaFluent/IssueTracking#1230.

| Piece | Version | Where it lives | Where it comes from |
|---|---|---|---|
| Python | 3.12 (system `python3`) | `/usr/bin/python3`; the tools run in a virtual environment in `.venv/` (git-ignored) | The operating system |
| Zensical | 0.0.72 | `.venv/`, pinned in `requirements.txt` | PyPI (`zensical`); https://zensical.org. The successor to Material for MkDocs, by the same maintainers; it reads `mkdocs.yml` and provides the Material theme |
| mike | 2.2.0+zensical.0.1.0 (commit `2d4ad79`) | `.venv/`; `requirements.txt` installs it from git, unpinned | https://github.com/squidfunk/mike, the Zensical maintainers' fork of mike. Builds one version of the site per release on the `gh-pages` branch and maintains the version drop-down (`versions.json`) |
| Markdown extensions | Markdown 3.11.2, pymdown-extensions 12.3 | `.venv/`, installed as dependencies of Zensical | PyPI. Configured under `markdown_extensions:` in `mkdocs.yml` |
| Site configuration | - | `mkdocs.yml` | This repo. Theme, branding, extensions, link validation and the navigation (`nav:`, maintained by hand) |
| Pages | - | `docs/*.md` | This repo |
| Branding | - | `docs/assets/images/logo.svg`, `favicon.svg`; `docs/stylesheets/brand.css`; `docs/assets/fonts/AlteHaasGroteskBold.woff2` | MetaFluent's logo; the colors and heading face (Alte Haas Grotesk, bold only) as used on metafluent.com. The body face, Inter, is loaded by the theme from Google Fonts |
| Publishing script | - | `tools/publish.sh` | This repo. See [Publishing](README.md#publish-a-release) |
| Hosting | - | The `gh-pages` branch, served by GitHub Pages ("deploy from a branch", root of `gh-pages`) at https://metafluent.github.io/ElasticMDS-docs/ | GitHub repository settings (Settings > Pages). No build service runs on GitHub: the site is built locally and the built files are pushed |
| GitHub CLI | - | `gh` on PATH | https://cli.github.com. `tools/publish.sh` uses it to wait for the Pages build |

## Upgrading

- **Zensical:** change the pin in `requirements.txt`, run `.venv/bin/pip install -r requirements.txt`, run
  `zensical build --strict` and preview the result before committing. Zensical is pre-1.0; read its changelog for
  changes to `mkdocs.yml` handling.
- **mike:** `requirements.txt` takes the fork's latest commit. To pin it, use
  `mike @ git+https://github.com/squidfunk/mike.git@<commit>`.
- A new environment is set up as in [README.md](README.md#set-up).
