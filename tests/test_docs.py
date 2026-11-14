import os
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPO_URL = re.compile(r'https://github\.com/SSyl/STALKER2-ZonePak/(?:blob|tree)/main/([^#]*)')
WIKI_URL = re.compile(r'https://github\.com/SSyl/STALKER2-ZonePak/wiki(?:/([^#]*))?')
LINK = re.compile(r'\]\(<?([^)>\s]+)>?\)')
CODE_SPAN = re.compile(r'(`+).+?\1')


def doc_files():
    return [REPO / 'README.md', *sorted((REPO / 'docs').glob('*.md'))]


def prose_lines(path):
    in_fence = False
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('```'):
            in_fence = not in_fence
        elif not in_fence:
            yield line


def anchors(path):
    """GitHub's heading anchors: lowercase, punctuation dropped, spaces to dashes, -1, -2 for repeats."""
    seen, result = {}, set()
    for line in prose_lines(path):
        heading = re.match(r'#{1,6} (.+)', line)
        if heading:
            slug = re.sub(r'[^\w\- ]', '', heading.group(1).strip().lower()).replace(' ', '-')
            count = seen.get(slug, 0)
            seen[slug] = count + 1
            result.add(slug if count == 0 else f'{slug}-{count}')
    return result


def wrong_case(linked, resolved):
    """Windows finds a file whatever the case, but GitHub and the wiki match case exactly."""
    return any(a != b and a.lower() == b.lower() for a, b in zip(linked.parts, resolved.parts))


class DocLinkTest(unittest.TestCase):
    def test_links_and_anchors_resolve(self):
        self.assertIn(REPO / 'docs' / 'Home.md', doc_files())
        broken = []
        for doc in doc_files():
            for line in prose_lines(doc):
                text = CODE_SPAN.sub('', line)
                targets = LINK.findall(text)
                if text.count('](') != len(targets):
                    broken.append(f'{doc.name}: unparsed link in {line.strip()!r}')
                for target in targets:
                    repo_url, wiki_url = REPO_URL.match(target), WIKI_URL.match(target)
                    if repo_url:
                        target = repo_url.group(1) + target[repo_url.end():]
                        base = REPO
                    elif wiki_url:
                        target = f'{wiki_url.group(1) or "Home"}.md' + target[wiki_url.end():]
                        base = REPO / 'docs'
                    elif re.match(r'[a-z]+:', target):
                        continue
                    else:
                        base = doc.parent
                    path_part, _, anchor = target.partition('#')
                    linked = Path(os.path.normpath(base / path_part)) if path_part else doc
                    path = linked.resolve()
                    # .github/workflows/sync-wiki.yml copies only docs/*.md to the wiki.
                    if (base == REPO / 'docs' and path_part
                            and (path.parent != (REPO / 'docs').resolve() or path.suffix != '.md')):
                        broken.append(f'{doc.name}: {target} (not a docs/*.md page, so the wiki has no copy)')
                    elif not path.exists():
                        broken.append(f'{doc.name}: {target} (no such file)')
                    elif wrong_case(linked, path):
                        on_disk = path.relative_to(REPO).as_posix()
                        broken.append(f'{doc.name}: {target} (on disk as {on_disk})')
                    elif anchor and anchor not in anchors(path):
                        broken.append(f'{doc.name}: {target} (no such anchor)')
        self.assertEqual(broken, [])


if __name__ == '__main__':
    unittest.main()
