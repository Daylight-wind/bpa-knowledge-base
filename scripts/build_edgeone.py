#!/usr/bin/env python3
"""Build approved articles for a Git-backed static-site deployment."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
import build_site

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dist'

def main():
    published = build_site.build_site('publish')
    content = (published / 'articles.js').read_text(encoding='utf-8')
    articles = json.loads(content.split('window.BPA_SITE_ARTICLES = ', 1)[1].rstrip().removesuffix(';'))
    if not articles:
        raise ValueError('没有已发布文章；请先审核内容并将可发布文章的 status 设为 published。不会生成新的部署目录。')
    if any(a.get('status') != 'published' for a in articles):
        raise ValueError('发布结果包含非 published 文章，构建已停止。')
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    staging = Path(tempfile.mkdtemp(prefix='.dist-stage-', dir=ROOT))
    try:
        shutil.copytree(published, staging, dirs_exist_ok=True)
        (staging / 'build-version.json').write_text(json.dumps({'git_commit': revision, 'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'article_count': len(articles)}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if OUTPUT.is_symlink():
            raise ValueError('dist 是符号链接，拒绝替换。')
        if OUTPUT.exists():
            if not (OUTPUT / '.bpa-generated').exists():
                raise ValueError('dist 已存在但不是本站生成的目录，拒绝替换。')
            shutil.rmtree(OUTPUT)
        (staging / '.bpa-generated').write_text('Generated static output.\n')
        os.replace(staging, OUTPUT)
    finally:
        if staging.exists(): shutil.rmtree(staging)
    print(f'部署构建完成：{len(articles)} 篇文章，Git 版本 {revision[:12]}，输出 dist/')

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'部署构建失败：{exc}', file=sys.stderr)
        sys.exit(1)
