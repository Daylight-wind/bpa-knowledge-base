#!/usr/bin/env python3
"""Generate separate local preview and publishable static sites from the vault."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

import build_markdown_pilot as markdown

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / '流程管理平台学习内容库'
OUTPUT_ROOT = ROOT / '构建结果'
TEMPLATE = ROOT / 'scripts/site_template'
NAVIGATION = Path('02-操作指南/00-操作指南导航.md')
NAV_START = '<!-- BPA-GUIDES:START -->'
NAV_END = '<!-- BPA-GUIDES:END -->'


def status_of(path):
    text = path.read_text(encoding='utf-8')
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.S)
    if not match:
        return None
    lines = re.findall(r'^status\s*:\s*(.*?)\s*$', match.group(1), re.M)
    if len(lines) > 1:
        raise ValueError(f'{path.name} 有多个 status 属性')
    if not lines:
        return None
    value = lines[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]
    return value


def navigation_content(vault, selected, builder):
    path = vault / NAVIGATION
    if path.is_symlink() or (path.parent.exists() and not markdown.inside_vault(path.parent)):
        raise ValueError('操作指南导航路径不在内容库内')
    if path.exists():
        existing = path.read_text(encoding='utf-8')
        if existing.count(NAV_START) != 1 or existing.count(NAV_END) != 1 or existing.index(NAV_START) >= existing.index(NAV_END):
            raise ValueError(f'{NAVIGATION} 不是可更新的自动导航，请检查并保留原文件')
        before, tail = existing.split(NAV_START, 1)
        _, after = tail.split(NAV_END, 1)
    else:
        before = '# 操作指南导航\n\n本地预览导航，包含草稿；请在文章属性中维护 guide_group。\n\n'
        after = '\n'
    groups = {}
    for note in selected:
        doc = builder.docs[note.resolve()]
        group = doc['meta'].get('guide_group')
        if group:
            groups.setdefault(group, []).append(doc)
    lines = []
    for group, docs in groups.items():
        lines.append(f'## {group}')
        lines.append('')
        for doc in docs:
            ref = doc['path'].relative_to(vault).with_suffix('').as_posix()
            title = doc['title']
            if any(c in ref or c in title for c in ('[', ']', '|', '\n', '\r')):
                raise ValueError(f'{doc["path"].name} 的名称或标题不能用于 Obsidian 导航链接')
            lines.append(f'- [[{ref}|{title}]]')
        lines.append('')
    if not lines:
        lines = ['暂无操作指南。', '']
    return path, before + NAV_START + '\n' + '\n'.join(lines) + NAV_END + after


def build_site(mode, vault=VAULT, output_root=OUTPUT_ROOT):
    vault, output_root = Path(vault).resolve(), Path(output_root).resolve()
    markdown.VAULT = vault
    statuses = {'draft', 'review', 'published'} if mode == 'preview' else {'published'}
    builder = markdown.Builder(allowed_statuses=statuses, asset_prefix='assets/', attachments=True)
    selected = []
    for path in sorted(vault.rglob('*.md')):
        if any(part.startswith('.') for part in path.relative_to(vault).parts):
            continue
        if path.name in ('README.md', '内容维护规则.md'):
            continue
        if not markdown.inside_vault(path):
            raise ValueError(f'文章位于内容库之外：{path}')
        status = status_of(path)
        if status in statuses:
            selected.append(path)
    for path in selected:
        builder.load(path)
        group = builder.docs[path.resolve()]['meta'].get('guide_group', '')
        if group and (not isinstance(group, str) or any(c in group for c in '\n\r[]|')):
            raise ValueError(f'{path.name} 的 guide_group 必须是单行分类名称')
    articles = []
    for path in selected:
        article = builder.make_article(builder.docs[path.resolve()])
        article['status'] = builder.docs[path.resolve()]['meta']['status']
        article['guideGroup'] = builder.docs[path.resolve()]['meta'].get('guide_group') or ''
        articles.append(article)
    # Linking a note not in the selected set must never introduce it into output.
    if set(builder.docs) != {path.resolve() for path in selected}:
        raise ValueError('内部链接指向了未纳入本次构建的文章')

    nav = navigation_content(vault, selected, builder) if mode == 'preview' else None

    output_root.mkdir(parents=True, exist_ok=True)
    destination = output_root / ('本地预览' if mode == 'preview' else '发布包')
    staging = Path(tempfile.mkdtemp(prefix='.site-build-', dir=output_root))
    backup = output_root / ('.previous-preview' if mode == 'preview' else '.previous-publish')
    try:
        shutil.copytree(TEMPLATE, staging, dirs_exist_ok=True)
        # Reuse the approved prototype's visual styles, never its demo content.
        for name in ('styles.css', 'homepage.css'):
            shutil.copyfile(ROOT / '页面原型' / name, staging / name)
        assets = staging / 'assets'
        assets.mkdir()
        for name, source in builder.assets.items():
            shutil.copyfile(source, assets / name)
        (staging / 'articles.js').write_text(
            'window.BPA_SITE_MODE = ' + json.dumps(mode) + ';\nwindow.BPA_SITE_ARTICLES = '
            + json.dumps(articles, ensure_ascii=False).replace('</', '<\\/') + ';\n', encoding='utf-8')
        # Backups are outside the served output directory, and never silently removed.
        if backup.exists():
            raise ValueError(f'发现未清理的上次构建备份，请先检查：{backup}')
        if destination.exists():
            os.replace(destination, backup)
        try:
            os.replace(staging, destination)
        except OSError:
            if backup.exists():
                os.replace(backup, destination)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    if nav:
        path, content = nav
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text(encoding='utf-8') != content:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as temp:
                temporary = Path(temp.name)
                try:
                    temp.write(content)
                except BaseException:
                    temporary.unlink(missing_ok=True)
                    raise
            try:
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
    print(f'{mode}: {len(articles)} 篇文章，{len(builder.assets)} 个资源 -> {destination}')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('preview', 'publish'))
    args = parser.parse_args()
    try:
        build_site(args.mode)
    except (ValueError, OSError) as exc:
        print(f'生成失败：{exc}', file=sys.stderr)
        sys.exit(1)
