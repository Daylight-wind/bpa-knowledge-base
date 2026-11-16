#!/usr/bin/env python3
"""Build the draft pilot and notes it links to for the local prototype."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/vendor'))
from markdown_it import MarkdownIt
from markdown_it.token import Token

VAULT = ROOT / '流程管理平台学习内容库'
SOURCE = VAULT / '01-流程管理平台系统操作培训/01-流程管理基础/01-制度流程规范指导书.md'
GENERATED = ROOT / '页面原型/generated'
ASSETS = GENERATED / 'pilot-assets'
OUTPUT = GENERATED / 'markdown-pilot.js'
WIKI = re.compile(r'(!?)\[\[([^\]\n]+)\]\]')
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.avif'}


def metadata_and_body(text):
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.S)
    if not match:
        raise ValueError('文章缺少 front matter 元数据')
    metadata, current = {}, None
    for line in match.group(1).splitlines():
        if line.startswith('  - ') and current:
            metadata.setdefault(current, []).append(line[4:].strip())
        elif ':' in line and not line.startswith(' '):
            key, value = line.split(':', 1)
            current = key.strip()
            metadata[current] = value.strip().strip('"\'') if value.strip() else []
    return metadata, text[match.end():]


def inside_vault(path):
    try:
        path.resolve().relative_to(VAULT.resolve())
        return True
    except ValueError:
        return False


def resolve_local(source, ref, note=False):
    ref = unquote(ref).strip().replace('\\', '/')
    if not ref or ref.startswith('/') or '://' in ref:
        raise ValueError(f'只支持内容库中的相对路径：{ref}')
    suffix = '.md' if note and not ref.lower().endswith('.md') else ''
    candidates = [source.parent / (ref + suffix), VAULT / (ref + suffix)]
    for item in candidates:
        if inside_vault(item) and item.is_file():
            return item.resolve()
    # Obsidian also permits linking by an unqualified filename anywhere in a vault.
    if '/' not in ref:
        matches = [p.resolve() for p in VAULT.rglob(ref + suffix) if p.is_file() and inside_vault(p)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(f'文件名不唯一，请改用内容库相对路径：{ref}')
    raise ValueError(f'找不到文件：{ref}（引用自 {source.relative_to(VAULT.resolve())}）')


def normalized_heading(value):
    return re.sub(r'\s+', ' ', unquote(value).strip()).casefold()


def obsidian_highlight(state, silent):
    if not state.src.startswith('==', state.pos):
        return False
    end = state.src.find('==', state.pos + 2, state.posMax)
    if end <= state.pos + 2 or '\n' in state.src[state.pos + 2:end]:
        return False
    if not silent:
        state.push('mark_open', 'mark', 1)
        nested = []
        state.md.inline.parse(state.src[state.pos + 2:end], state.md, state.env, nested)
        state.tokens.extend(nested)
        state.push('mark_close', 'mark', -1)
    state.pos = end + 2
    return True


class Builder:
    def __init__(self, allowed_statuses=None, asset_prefix='generated/pilot-assets/', attachments=False):
        self.md = MarkdownIt('commonmark', {'html': False}).enable('table').enable('strikethrough')
        self.md.inline.ruler.before('emphasis', 'obsidian_highlight', obsidian_highlight)
        self.docs = {}
        self.ids = {}
        self.assets = {}
        self.allowed_statuses = allowed_statuses or {'draft'}
        self.asset_prefix = asset_prefix
        self.attachments = attachments

    def load(self, path):
        path = path.resolve()
        if path in self.docs:
            return self.docs[path]
        meta, body = metadata_and_body(path.read_text(encoding='utf-8'))
        for field in ('id', 'title', 'category', 'audience', 'status'):
            if not isinstance(meta.get(field), str) or not meta[field]:
                raise ValueError(f'{path.name} 缺少必填元数据：{field}')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', meta['id']):
            raise ValueError(f'{path.name} 的 id 只能包含英文字母、数字、下划线或连字符')
        if meta['status'] not in self.allowed_statuses:
            raise ValueError(f'{path.name} 的状态 {meta["status"]} 不允许出现在当前构建中')
        if meta['id'] in self.ids:
            raise ValueError(f'文章 id 重复：{meta["id"]}')
        tokens = self.md.parse(body)
        doc = {'path': path, 'meta': meta, 'tokens': tokens, 'headings': {}, 'title': meta['title'], 'title_anchor': ''}
        self.docs[path] = doc
        self.ids[meta['id']] = path
        heading_count = 0
        for i, token in enumerate(tokens):
            if token.type == 'heading_open':
                heading_count += 1
                title = tokens[i + 1].content
                if token.tag == 'h1' and doc['title'] == meta['title']:
                    doc['title'] = title
                anchor = f'md-heading-{heading_count}'
                if token.tag == 'h1' and not doc['title_anchor']:
                    doc['title_anchor'] = anchor
                token.attrSet('id', 'section-' + anchor)
                key = normalized_heading(title)
                doc['headings'].setdefault(key, []).append(anchor)
        return doc

    def asset(self, source, ref, attachment=False):
        file = resolve_local(source, ref)
        allowed = {'.pdf', '.docx', '.xlsx', '.pptx', '.zip'} if attachment else IMAGE_EXTENSIONS
        if file.suffix.lower() not in allowed or file.suffix.lower() == '.svg':
            raise ValueError(f'不支持或不安全的资源类型：{ref}')
        name = hashlib.sha256(file.read_bytes()).hexdigest()[:20] + file.suffix.lower()
        self.assets[name] = file
        return self.asset_prefix + name

    def note_link(self, doc, target):
        filename, sep, heading = unquote(target).partition('#')
        linked = self.load(resolve_local(doc['path'], filename, True)) if filename else doc
        href = '#article/' + linked['meta']['id']
        if sep:
            if not heading or heading.startswith('^'):
                raise ValueError(f'暂不支持块引用或空标题链接：{target}')
            matches = linked['headings'].get(normalized_heading(heading), [])
            if len(matches) != 1:
                raise ValueError(f'链接标题不存在或不唯一：{target}')
            href += '?section=' + matches[0]
        return href

    def transform_inline(self, doc, token):
        children = token.children or []
        result = []
        for child in children:
            if child.type == 'text':
                remaining = child.content
                while True:
                    match = WIKI.search(remaining)
                    if not match:
                        if remaining:
                            t = Token('text', '', 0); t.content = remaining; result.append(t)
                        break
                    if match.start():
                        t = Token('text', '', 0); t.content = remaining[:match.start()]; result.append(t)
                    target, _, alias = match.group(2).partition('|')
                    if match.group(1):
                        if Path(target).suffix.lower() not in IMAGE_EXTENSIONS:
                            raise ValueError(f'暂不支持嵌入笔记或其他附件：![[{match.group(2)}]]')
                        t = Token('image', 'img', 0)
                        t.attrs = {'src': self.asset(doc['path'], target), 'alt': ''}
                        alt = alias if alias and not alias.isdigit() else Path(target).stem
                        t.content = alt
                        text = Token('text', '', 0); text.content = alt; t.children = [text]
                        if alias.isdigit(): t.attrSet('width', alias)
                        result.append(t)
                    else:
                        label = alias or target.split('#')[-1] or target
                        is_attachment = self.attachments and Path(target).suffix.lower() in {'.pdf', '.docx', '.xlsx', '.pptx', '.zip'}
                        opening = Token('link_open', 'a', 1); opening.attrs = {'href': self.asset(doc['path'], target, True) if is_attachment else self.note_link(doc, target)}
                        if is_attachment: opening.attrSet('download', '')
                        text = Token('text', '', 0); text.content = label
                        result.extend([opening, text, Token('link_close', 'a', -1)])
                    remaining = remaining[match.end():]
            elif child.type == 'image':
                src = child.attrGet('src') or ''
                child.attrSet('src', self.asset(doc['path'], src))
                result.append(child)
            elif child.type == 'link_open':
                href = child.attrGet('href') or ''
                parts = urlsplit(href)
                if not parts.scheme and not parts.netloc:
                    if not parts.path or unquote(parts.path).lower().endswith('.md'):
                        child.attrSet('href', self.note_link(doc, href))
                    elif self.attachments:
                        child.attrSet('href', self.asset(doc['path'], parts.path, True))
                        child.attrSet('download', '')
                    else:
                        raise ValueError(f'本地链接仅支持 Markdown 笔记：{href}')
                elif parts.scheme.lower() not in ('http', 'https', 'mailto'):
                    raise ValueError(f'不支持的链接协议：{href}')
                result.append(child)
            else:
                result.append(child)
        token.children = result

    def make_article(self, doc):
        tokens = doc['tokens']
        for t in tokens:
            if t.type == 'inline':
                self.transform_inline(doc, t)
        # Preserve complete Markdown blocks; h2 titles drive the existing page TOC.
        sections, current = [], None
        def ensure():
            nonlocal current
            if current is None:
                current = {'id': 'md-intro', 'title': '正文', 'tokens': []}; sections.append(current)
            return current
        i = 0
        skipped_title = False
        while i < len(tokens):
            t = tokens[i]
            if t.type == 'heading_open' and t.tag == 'h1' and not skipped_title:
                skipped_title = True
                i += 3
                continue
            if t.type == 'heading_open' and t.tag == 'h2':
                current = {'id': t.attrGet('id'), 'title': tokens[i+1].content, 'tokens': []}
                sections.append(current); i += 3; continue
            ensure()['tokens'].append(t); i += 1
        if not sections:
            raise ValueError(f'{doc["path"].name} 正文为空')
        out = []
        for section in sections:
            plain_parts = []
            for token in section['tokens']:
                if token.type == 'inline':
                    plain_parts.extend(child.content for child in token.children or []
                                       if child.type in ('text', 'code_inline'))
                elif token.type in ('fence', 'code_block'):
                    plain_parts.append(token.content)
            plain = ' '.join(plain_parts)
            out.append({'id': section['id'], 'title': section['title'], 'html': self.md.renderer.render(section['tokens'], self.md.options, {}), 'text': plain})
        m = doc['meta']; sources = m.get('source', [])
        return {'id': m['id'], 'titleAnchor': doc['title_anchor'], 'title': doc['title'], 'short': doc['title'], 'category': m['category'], 'audience': m['audience'], 'intro': '当前内容为学习草稿，正式使用前需核验。', 'source': '；'.join(sources) if isinstance(sources, list) else sources, 'sections': out}

    def build(self):
        self.load(SOURCE)
        articles = []
        done = set()
        while True:
            pending = next((doc for path, doc in self.docs.items() if path not in done), None)
            if pending is None: break
            done.add(pending['path'])
            articles.append(self.make_article(pending))
        # All parsing and validation happens before replacing the generated data.
        ASSETS.mkdir(parents=True, exist_ok=True)
        for name, path in self.assets.items():
            shutil.copyfile(path, ASSETS / name)
        content = '/* 自动生成：请编辑 Markdown 源文件。仅供草稿预览。 */\nwindow.BPA_MARKDOWN_ARTICLES = ' + json.dumps(articles, ensure_ascii=False, indent=2) + ';\n'
        temp = OUTPUT.with_suffix('.tmp')
        temp.write_text(content, encoding='utf-8')
        temp.replace(OUTPUT)
        # Remove obsolete generated images; source assets are never changed.
        for old in ASSETS.iterdir():
            if old.is_file() and old.name not in self.assets:
                old.unlink()
        print(f'已生成 {len(articles)} 篇文章、{len(self.assets)} 张图片（仅本地草稿）')


def build():
    Builder().build()


if __name__ == '__main__':
    try:
        build()
    except (ValueError, OSError) as exc:
        print(f'生成失败：{exc}', file=sys.stderr)
        sys.exit(1)
