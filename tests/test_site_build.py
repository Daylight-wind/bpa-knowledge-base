import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('build_site', ROOT / 'scripts/build_site.py')
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)


def note(identifier, title, status, body):
    return f'---\nid: {identifier}\ntitle: {title}\ncategory: 测试\naudience: 读者\nstatus: {status}\n---\n# {title}\n\n## 内容\n\n{body}\n'


class SiteBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.vault = self.root / 'vault'
        self.vault.mkdir()
        self.out = self.root / 'out'

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, status, body='正文', identifier='one', title='文章一'):
        path = self.vault / name
        path.write_text(note(identifier, title, status, body), encoding='utf-8')
        return path

    def articles(self, path):
        text = (path / 'articles.js').read_text(encoding='utf-8')
        return json.loads(text.split('window.BPA_SITE_ARTICLES = ', 1)[1].rstrip(';\n'))

    def test_build_uses_prototype_styles_without_prototype_content(self):
        self.write('a.md', 'published')
        out = site.build_site('publish', self.vault, self.out)
        for name in ('styles.css', 'homepage.css'):
            self.assertEqual((out / name).read_bytes(), (ROOT / '页面原型' / name).read_bytes())
        html = (out / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('content.js', html)
        self.assertNotIn('markdown-pilot.js', html)
        self.assertFalse((out / 'content.js').exists())

    def test_guides_filter_with_status_and_update_obsidian_navigation(self):
        published = self.write('published.md', 'published', identifier='one', title='已发布操作')
        draft = self.write('draft.md', 'draft', identifier='two', title='草稿操作')
        concept = self.write('concept.md', 'published', identifier='three', title='基础概念')
        for path, group in ((published, '常用操作'), (draft, '草稿分类')):
            path.write_text(path.read_text().replace('status:', f'guide_group: {group}\nstatus:'), encoding='utf-8')
        preview = site.build_site('preview', self.vault, self.out)
        entries = {a['id']: a['guideGroup'] for a in self.articles(preview)}
        self.assertEqual(entries, {'one': '常用操作', 'two': '草稿分类', 'three': ''})
        nav = self.vault / site.NAVIGATION
        text = nav.read_text(encoding='utf-8')
        self.assertIn('[[published|已发布操作]]', text)
        self.assertIn('[[draft|草稿操作]]', text)
        self.assertNotIn('基础概念', text)
        nav.write_text('用户笔记\n' + text + '\n保留内容\n', encoding='utf-8')
        draft.rename(self.vault / 'renamed.md')
        site.build_site('preview', self.vault, self.out)
        self.assertIn('[[renamed|草稿操作]]', nav.read_text(encoding='utf-8'))
        self.assertIn('用户笔记', nav.read_text(encoding='utf-8'))
        self.assertIn('保留内容', nav.read_text(encoding='utf-8'))
        before = nav.read_text(encoding='utf-8')
        out = site.build_site('publish', self.vault, self.out)
        self.assertEqual({a['id']: a['guideGroup'] for a in self.articles(out)}, {'one': '常用操作', 'three': ''})
        self.assertNotIn('草稿分类', (out / 'articles.js').read_text(encoding='utf-8'))
        self.assertEqual(nav.read_text(encoding='utf-8'), before)

    def test_navigation_does_not_overwrite_unmanaged_file(self):
        self.write('a.md', 'draft')
        nav = self.vault / site.NAVIGATION
        nav.parent.mkdir()
        nav.write_text('用户现有内容', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '不是可更新的自动导航'):
            site.build_site('preview', self.vault, self.out)
        self.assertEqual(nav.read_text(encoding='utf-8'), '用户现有内容')

    def test_status_rename_delete_and_asset_cleanup(self):
        image = self.vault / 'image.png'; image.write_bytes(b'image')
        attachment = self.vault / 'file.pdf'; attachment.write_bytes(b'pdf')
        first = self.write('a.md', 'published', '![图片](image.png) [附件](file.pdf)')
        second = self.write('b.md', 'draft', '草稿秘密', 'two', '文章二')
        missing = self.vault / 'missing.md'; missing.write_text('# 无状态\n不应出现', encoding='utf-8')
        out = site.build_site('publish', self.vault, self.out)
        self.assertEqual([a['id'] for a in self.articles(out)], ['one'])
        self.assertEqual(len(list((out / 'assets').iterdir())), 2)
        self.assertNotIn('草稿秘密', (out / 'articles.js').read_text())
        first.rename(self.vault / 'renamed.md')
        second.write_text(note('two', '文章二改名', 'published', '新正文'), encoding='utf-8')
        out = site.build_site('publish', self.vault, self.out)
        self.assertEqual({a['title'] for a in self.articles(out)}, {'文章一', '文章二改名'})
        (self.vault / 'renamed.md').unlink()
        second.write_text(note('two', '文章二改名', 'draft', '新正文'), encoding='utf-8')
        out = site.build_site('publish', self.vault, self.out)
        self.assertEqual(self.articles(out), [])
        self.assertEqual(list((out / 'assets').iterdir()), [])
        preview = site.build_site('preview', self.vault, self.out)
        self.assertEqual([a['id'] for a in self.articles(preview)], ['two'])
        self.assertEqual(self.articles(out), [])

    def test_published_link_to_draft_fails_without_changing_previous_build(self):
        first = self.write('a.md', 'published', '原始内容')
        out = site.build_site('publish', self.vault, self.out)
        old = (out / 'articles.js').read_bytes()
        self.write('draft.md', 'draft', '秘密', 'two', '草稿')
        first.write_text(note('one', '文章一', 'published', '[[draft]]'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '不允许'):
            site.build_site('publish', self.vault, self.out)
        self.assertEqual((out / 'articles.js').read_bytes(), old)

    def test_duplicate_status_and_unsupported_attachment_fail(self):
        path = self.write('a.md', 'published', '[危险文件](test.html)')
        (self.vault / 'test.html').write_text('secret')
        with self.assertRaisesRegex(ValueError, '不支持'):
            site.build_site('publish', self.vault, self.out)
        path.write_text(note('one', '文章一', 'published', '正文').replace('status: published', 'status: draft\nstatus: published'))
        with self.assertRaisesRegex(ValueError, '多个 status'):
            site.build_site('publish', self.vault, self.out)


if __name__ == '__main__':
    unittest.main()
