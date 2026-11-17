#!/usr/bin/env python3
"""Validate and publish a user-reviewed snapshot of the local repository."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, 'GIT_TERMINAL_PROMPT': '0'}


def git(*args, text=True):
    return subprocess.run(['git', *args], cwd=ROOT, env=ENV, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text).stdout


def check_repository():
    if git('branch', '--show-current').strip() != 'main':
        raise ValueError('当前不在 main 分支，请先检查仓库状态。')
    if git('diff', '--cached', '--name-only').strip():
        raise ValueError('暂存区已有文件；为避免混入其他更改，请先处理暂存区。')
    if git('ls-files', '-u').strip():
        raise ValueError('存在合并冲突，请先处理。')
    local = git('rev-parse', 'HEAD').strip()
    remote = git('ls-remote', '--exit-code', 'origin', 'refs/heads/main').split()[0]
    if local != remote:
        raise ValueError('本地版本与远端 main 不一致，请先处理未推送提交或远端更改。')


def fingerprint():
    status = git('status', '--porcelain=v1', '-z', '--untracked-files=all', text=False)
    paths = git('ls-files', '-z', '--modified', '--others', '--exclude-standard', text=False)
    h = hashlib.sha256(status + b'\0')
    for name in sorted(filter(None, paths.split(b'\0'))):
        h.update(name + b'\0')
        file = ROOT / os.fsdecode(name)
        if file.is_symlink():
            h.update(b'link:' + os.fsencode(os.readlink(file)))
        elif file.is_file():
            with file.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1048576), b''):
                    h.update(chunk)
        else:
            h.update(b'missing')
    return h.hexdigest()


def validate():
    for mode in ('preview', 'publish'):
        subprocess.run([sys.executable, str(ROOT / 'scripts/build_site.py'), mode],
                       cwd=ROOT, env=ENV, check=True, capture_output=True, text=True)


def main():
    if len(sys.argv) not in (2, 3) or sys.argv[1] not in ('prepare', 'publish'):
        raise ValueError('无效的操作参数。')
    check_repository()
    validate()
    state = fingerprint()
    status = git('-c', 'core.quotepath=false', 'status', '--short', '--untracked-files=all').strip()
    if sys.argv[1] == 'prepare':
        print(json.dumps({'fingerprint': state, 'status': status}, ensure_ascii=False))
        return
    if len(sys.argv) != 3 or state != sys.argv[2]:
        raise ValueError('确认后文件发生了变化，请重新检查再发布。')
    if not status:
        raise ValueError('没有需要提交的更改。')
    git('add', '-A')
    try:
        git('commit', '-m', '更新知识库 ' + datetime.now().strftime('%Y-%m-%d %H:%M'))
    except subprocess.CalledProcessError as exc:
        raise ValueError('Git 提交失败，暂存内容已保留，请先检查：' + exc.stderr.strip()) from exc
    revision = git('rev-parse', '--short', 'HEAD').strip()
    try:
        git('push', 'origin', 'main')
    except subprocess.CalledProcessError as exc:
        raise ValueError(f'本地提交 {revision} 已保存，但推送失败；请先检查网络、登录或远端版本。不要重复提交。\n{exc.stderr.strip()}') from exc
    print(json.dumps({'commit': revision}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print('检查或构建失败：' + (exc.stderr or str(exc)).strip(), file=sys.stderr)
        sys.exit(1)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
