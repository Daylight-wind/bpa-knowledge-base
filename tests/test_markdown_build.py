import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('build_markdown_pilot', Path(__file__).resolve().parents[1] / 'scripts/build_markdown_pilot.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def note(identifier, title, body):
    return f'''---
id: {identifier}
title: {title}
category: 测试
audience: 读者
status: draft
source:
  - 测试材料
---
# {title}

{body}
'''

class MarkdownBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        build.VAULT = self.root / 'vault'; build.VAULT.mkdir()
        build.SOURCE = build.VAULT / 'pilot.md'
        build.GENERATED = self.root / 'generated'; build.GENERATED.mkdir()
        build.ASSETS = build.GENERATED / 'pilot-assets'
        build.OUTPUT = build.GENERATED / 'markdown-pilot.js'

    def tearDown(self): self.temp.cleanup()

    def output(self):
        data = build.OUTPUT.read_text(encoding='utf-8')
        return json.loads(data.split(' = ', 1)[1].rstrip(';\n'))

    def test_formats_links_images_and_security(self):
        (build.VAULT/'图片.png').write_bytes(b'fake-image')
        (build.VAULT/'第二篇.md').write_text(note('second','第二篇','## 目标标题\n\n目标内容\n\n### 子章节\n\n测试'), encoding='utf-8')
        build.SOURCE.write_text(note('first','第一篇', '''## 排版

**粗体** *斜体* ~~删除~~ `行内代码` [外部](https://example.com)

> 引用

1. 一
2. 二

- 无序

| 名称 | 内容 |
| --- | --- |
| 表格 | 数据 |

```python
print("[[第二篇]]")
```

![普通图片](图片.png)

![[图片.png|320]]

[[第二篇#目标标题|查看目标]] [Markdown链接](第二篇.md#子章节)

<script>alert(1)</script>
'''), encoding='utf-8')
        build.build()
        articles = self.output()
        self.assertEqual([a['id'] for a in articles], ['first','second'])
        content = articles[0]['sections'][0]['html']
        for element in ('<strong>粗体</strong>', '<em>斜体</em>', '<s>删除</s>', '<code>行内代码</code>', '<blockquote>', '<ol>', '<ul>', '<table>', '<pre><code', 'width="320"', 'https://example.com', '&lt;script&gt;'):
            self.assertIn(element, content)
        self.assertNotIn('<script>', content)
        self.assertNotIn('![普通图片]', articles[0]['sections'][0]['text'])
        self.assertIn('查看目标', articles[0]['sections'][0]['text'])
        self.assertIn('#article/second?section=md-heading-2', content)
        self.assertIn('#article/second?section=md-heading-3', content)
        self.assertIn('[[第二篇]]', content)  # fenced code is not converted
        self.assertEqual(len(list(build.ASSETS.iterdir())), 1)
        self.assertIn('section-md-heading-3', articles[1]['sections'][0]['html'])

    def test_obsidian_highlight_and_literal_code(self):
        build.SOURCE.write_text(note('first', '第一篇', '## 内容\n\n==重要 **提示**== 与 `==原样==`，以及 ==未闭合'), encoding='utf-8')
        build.build()
        html = self.output()[0]['sections'][0]['html']
        self.assertIn('<mark>重要 <strong>提示</strong></mark>', html)
        self.assertIn('<code>==原样==</code>', html)
        self.assertIn('==未闭合', html)

    def test_numbered_note_name_without_extension(self):
        (build.VAULT/'3.1 示例文章.md').write_text(note('numbered', '3.1 示例文章', '## 内容\n\n文字'), encoding='utf-8')
        build.SOURCE.write_text(note('first', '第一篇', '## 内容\n\n[[3.1 示例文章|阅读文章]]'), encoding='utf-8')
        build.build()
        self.assertIn('#article/numbered', self.output()[0]['sections'][0]['html'])

    def test_missing_link_fails_without_replacing_previous_output(self):
        build.SOURCE.write_text(note('first','第一篇','## 内容\n\n[[不存在]]'),encoding='utf-8')
        build.OUTPUT.write_text('old output', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '找不到文件'): build.build()
        self.assertEqual(build.OUTPUT.read_text(), 'old output')

    def test_ambiguous_name_fails(self):
        for directory in ('a','b'):
            p=build.VAULT/directory; p.mkdir()
            (p/'重名.md').write_text(note(directory,'重名','## 内容\n\n文字'),encoding='utf-8')
        build.SOURCE.write_text(note('first','第一篇','## 内容\n\n[[重名]]'),encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '不唯一'): build.build()

if __name__ == '__main__': unittest.main()
