"""Imports one ref of the Elastic MDS GitHub wiki into this site: the pages into docs/, the navigation into mkdocs.yml.

Usage: python3 tools/import-wiki.py <wiki-clone> <git-ref>

Used while the wiki is still the live documentation, to bring its pages across. Every page and image the wiki holds
at <git-ref> replaces the one in docs/; pages the wiki no longer has are removed. The site's own files (docs/assets/
and docs/stylesheets/) are not touched.

Wiki links [[Text|Page#anchor]] and [[Page]], and bare links to wiki pages (Page or Page#anchor), become relative
.md links; Home becomes index.md; the navigation is built from _Sidebar.md (**Section** lines and [[Text|Page]]
items) and replaces everything after the "nav:" line of mkdocs.yml.
"""
import os, re, subprocess, sys

SITE_DIRS = {'assets', 'stylesheets'}

wiki, ref = sys.argv[1:3]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
docs = os.path.join(root, 'docs')
config_path = os.path.join(root, 'mkdocs.yml')

files = subprocess.check_output(['git', '-C', wiki, 'ls-tree', '--name-only', ref], text=True).split()
pages = {f[:-3] for f in files if f.endswith('.md') and not f.startswith('_')}


def target(page):
    return 'index.md' if page == 'Home' else page + '.md'


def link(page_and_anchor):
    page, _, anchor = page_and_anchor.partition('#')
    page = page.strip().replace(' ', '-')
    if page not in pages:
        return None
    return target(page) + ('#' + anchor if anchor else '')


def convert(text):
    def wiki_link(match):
        label, _, destination = match.group(1).partition('|')
        resolved = link(destination or label)
        return f'[{label}]({resolved})' if resolved else match.group(0)
    text = re.sub(r'\[\[([^\]]+)\]\]', wiki_link, text)

    def markdown_link(match):
        resolved = link(match.group(2))
        return f'[{match.group(1)}]({resolved})' if resolved else match.group(0)
    return re.sub(r'\[([^\]]*)\]\(([A-Za-z][A-Za-z0-9-]*(?:#[^)\s]*)?)\)', markdown_link, text)


for entry in os.listdir(docs):
    if entry not in SITE_DIRS:
        os.remove(os.path.join(docs, entry))

for name in files:
    if name.startswith('.') or name.startswith('_'):
        continue
    data = subprocess.check_output(['git', '-C', wiki, 'show', f'{ref}:{name}'])
    if name.endswith('.md'):
        with open(os.path.join(docs, target(name[:-3])), 'w') as page:
            page.write(convert(data.decode('utf-8')))
    else:
        with open(os.path.join(docs, name), 'wb') as asset:
            asset.write(data)

sidebar = subprocess.check_output(['git', '-C', wiki, 'show', f'{ref}:_Sidebar.md'], text=True)
nav, section = [], None
for line in sidebar.splitlines():
    heading = re.match(r'^\*\*(.+)\*\*\s*$', line.strip())
    items = re.findall(r'\[\[([^\]]+)\]\]', line)
    if heading:
        section = []
        nav.append((heading.group(1), section))
    elif items:
        label, _, destination = items[0].partition('|')
        entry = (label, target((destination or label).strip().replace(' ', '-')))
        (nav if section is None else section).append(entry)


def yaml_string(text):
    return '"' + text.replace('"', '\\"') + '"'


lines = []
for label, destination in nav:
    if isinstance(destination, list):
        lines.append(f'  - {yaml_string(label)}:')
        lines.extend(f'      - {yaml_string(item)}: {page}' for item, page in destination)
    else:
        lines.append(f'  - {yaml_string(label)}: {destination}')

config = open(config_path).read()
head, marker, _ = config.partition('\nnav:\n')
if not marker:
    sys.exit(f'{config_path} has no "nav:" line to replace')
with open(config_path, 'w') as out:
    out.write(head + marker + '\n'.join(lines) + '\n')
print(f'{ref}: {len(pages)} pages, {len(nav)} navigation entries')
