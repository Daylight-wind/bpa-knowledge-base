const articles = window.BPA_SITE_ARTICLES;
const preview = window.BPA_SITE_MODE === 'preview';
const main = document.querySelector('#main');
const dialog = document.querySelector('#search-dialog');
const input = document.querySelector('#search-input');
const results = document.querySelector('#search-results');
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let searchOpener;

document.querySelector('#preview-note').hidden = !preview;

function groups(items = articles) {
  return [...new Set(items.map(a => a.category))].map(name => ({name, articles: items.filter(a => a.category === name)}));
}

const isAdmin = a => a.category === '管理员操作';
const adminBadge = a => isAdmin(a) ? '<span class="admin-badge">管理员专用</span>' : '';

function home() {
  return `<div class="academy-home"><section class="academy-hero" aria-labelledby="academy-title">
    <p class="academy-name">流程管理平台学习与操作中心</p><h1 id="academy-title">理解流程管理，<br>掌握流程管理平台操作。</h1>
    <p class="academy-description">面向具有文件编辑权限的人员，<br class="mobile-break">提供培训课程与日常操作指南。</p>
    <div class="academy-actions"><a class="academy-primary" href="#learning">开始流程管理平台系统操作培训 <span aria-hidden="true">→</span></a><a class="academy-secondary" href="#guides">查找操作指南 <span aria-hidden="true">↗</span></a></div>
    </section><section class="academy-main-entries">
    <a class="academy-main-entry training" href="#learning"><span class="academy-emoji" aria-hidden="true">🧭</span><div><p class="academy-kicker">系统学习</p><h2>流程管理平台系统操作培训</h2><p>从流程管理基础开始，逐步学习平台操作。</p></div><span class="academy-card-action">查看培训目录 <span>→</span></span></a>
    <a class="academy-main-entry guide" href="#guides"><span class="academy-emoji" aria-hidden="true">📖</span><div><p class="academy-kicker">按任务查阅</p><h2>操作指南</h2><p>直接查找需要的操作说明和常见问题。</p></div><span class="academy-card-action">查看操作指南 <span>→</span></span></a>
    </section></div>`;
}

function learning() {
  const intro = articles.filter(a => a.category === '课程导读');
  const categories = groups(articles.filter(a => a.category !== '课程导读'));
  return `<div class="page-width learning-page course-shell"><aside class="learning-aside"><p class="eyebrow">课程目录</p><nav class="learning-toc">${categories.map((g, i) => `<a href="#module-${i + 1}" data-module="module-${i + 1}"><span>${i + 1}</span><b>${esc(g.name)}</b></a>`).join('')}</nav></aside>
    <div class="course-main"><p class="breadcrumb"><a href="#home">首页</a> / 流程管理平台系统操作培训</p><div class="learning-heading"><p class="eyebrow">COURSE GUIDE</p><h1>流程管理平台系统操作培训</h1><p>从流程管理基础到平台操作，按课程目录学习。</p><div class="chips"><span>适用：具有文件编辑权限的人员</span><span>${articles.length} 篇文章</span></div></div>
    <div class="learning-layout"><div>${intro.length ? `<section class="course-intro"><h2>课程导读</h2>${intro.map(a => `<a href="#article/${encodeURIComponent(a.id)}">${esc(a.title)} →</a>`).join('')}</section>` : ''}${categories.map((g, i) => `<section class="stage" id="module-${i + 1}"><div class="stage-number">${i + 1}</div><div class="stage-body"><p class="eyebrow">模块 ${i + 1}</p><h2>${esc(g.name)}</h2><div class="stage-articles">${g.articles.map(a => `<a href="#article/${encodeURIComponent(a.id)}"><span class="document-symbol">▤</span><div><b>${esc(a.title)}</b> ${adminBadge(a)}<small>${esc(a.audience)}</small></div><span>→</span></a>`).join('')}</div></div></section>`).join('') || '<p class="empty-state">暂无可查看的文章。</p>'}</div></div></div></div>`;
}

const taskLabels = {'平台基础操作':'管理角色、岗位与岗位组', '流程文件编写':'编写、发布或作废流程文件', '制度文件编写':'编写制度文件', '表单与附件':'创建表单与上传附件', '管理员操作':'管理平台与处理异常'};
function guides() {
  const guideArticles = articles.filter(a => a.guideGroup);
  const guideGroups = [...new Set(guideArticles.map(a => a.guideGroup))].map(name => ({name, articles: guideArticles.filter(a => a.guideGroup === name)}));
  return `<div class="page-width guides-page"><p class="breadcrumb"><a href="#home">首页</a> / 操作指南</p><p class="eyebrow">BROWSE BY TASK</p><h1>按任务，找到操作说明。</h1><p class="lead">选择需要查看的文章，或按关键词搜索。</p><button class="button secondary" data-search>⌕ 搜索文章</button><div class="guide-groups">${guideGroups.map(g => `<section><h2>${esc(taskLabels[g.name] || g.name)}</h2><div>${g.articles.map(a => `<a href="#article/${encodeURIComponent(a.id)}"><div><h3>${esc(a.title)}</h3>${adminBadge(a)}<p>${esc(a.audience)}</p></div><span>→</span></a>`).join('')}</div></section>`).join('') || '<p class="empty-state">暂无可查看的操作指南。</p>'}</div></div>`;
}

function articlePage(a) {
  const index = articles.indexOf(a), prev = articles[index - 1], next = articles[index + 1];
  return `<div class="reading-layout"><aside class="chapter-sidebar"><a class="back-home" href="#learning">← 培训课程目录</a><details class="chapter-details" open><summary>全部文章</summary><div>${groups().map(g => `<div class="chapter-group"><h3>${esc(g.name)}</h3>${g.articles.map(item => `<a ${item.id === a.id ? 'aria-current="page"' : ''} href="#article/${encodeURIComponent(item.id)}">${esc(item.title)}</a>`).join('')}</div>`).join('')}</div></details><a class="sidebar-learning" href="#guides">↗ 按任务查阅</a></aside>
    <article class="article"><p class="breadcrumb"><a href="#home">首页</a> / ${esc(a.category)}</p><div class="article-tags"><span>${esc(a.category)}</span>${adminBadge(a)}${preview ? `<span>${esc(a.status)}</span>` : ''}</div><h1 id="section-${esc(a.titleAnchor)}">${esc(a.title)}</h1><div class="article-meta"><span>适用：${esc(a.audience)}</span></div>
    ${preview ? '<div class="article-warning"><b>草稿预览</b><p>内容及截图需审核后再用于正式发布。</p></div>' : ''}
    ${a.sections.map(s => `<section class="article-section" id="${esc(s.id)}"><h2>${esc(s.title)}</h2>${s.html}</section>`).join('')}
    <div class="article-pagination">${prev ? `<a href="#article/${encodeURIComponent(prev.id)}"><small>← 上一篇</small><b>${esc(prev.title)}</b></a>` : '<span></span>'}${next ? `<a href="#article/${encodeURIComponent(next.id)}"><small>下一篇 →</small><b>${esc(next.title)}</b></a>` : '<a href="#learning"><small>返回课程 →</small><b>查看培训目录</b></a>'}</div></article>
    <aside class="page-toc"><details class="page-details" open><summary>本页目录</summary>${a.sections.map(s => `<button data-section="${esc(s.id)}">${esc(s.title)}</button>`).join('')}<div class="toc-tip"><button data-search>⌕ 搜索相关内容</button></div></details></aside></div>`;
}

function route() {
  const hash = location.hash.slice(1) || 'home';
  let active = hash, title = '首页';
  if (hash.startsWith('article/')) {
    const id = hash.slice(8).split('?')[0], a = articles.find(item => item.id === id);
    active = '';
    if (a) { main.innerHTML = articlePage(a); title = a.title; }
    else { main.innerHTML = '<div class="page-width empty-page"><h1>没有找到这篇文章</h1><p>请返回目录查找。</p><a href="#guides" class="button primary">查看操作指南</a></div>'; title = '文章未找到'; }
  } else if (hash === 'learning') { main.innerHTML = learning(); title = '培训课程'; }
  else if (hash === 'guides') { main.innerHTML = guides(); title = '操作指南'; }
  else { main.innerHTML = home(); active = 'home'; }
  document.title = `${title} · BPA 学习与操作中心`;
  document.querySelectorAll('[data-nav]').forEach(link => { if (link.dataset.nav === active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current'); });
  prepareArticleImages();
  if (window.matchMedia('(max-width: 800px)').matches) {
    main.querySelectorAll('.page-details, .chapter-details').forEach(item => item.open = false);
  }
  window.scrollTo(0, 0);
  const section = new URLSearchParams(hash.split('?')[1] || '').get('section');
  if (section) {
    const target = document.getElementById(section) || document.getElementById('section-' + section);
    target?.scrollIntoView();
    // Images above a result can shift the page while loading; realign unless the reader intervenes.
    const pending = [...main.querySelectorAll('img')].filter(img => !img.complete && target && (img.compareDocumentPosition(target) & Node.DOCUMENT_POSITION_FOLLOWING));
    if (pending.length) {
      let interrupted = false;
      const stop = () => { interrupted = true; };
      const events = ['wheel', 'touchstart', 'pointerdown', 'keydown'];
      events.forEach(name => window.addEventListener(name, stop, {once: true, passive: true}));
      const startHash = location.hash;
      const loaded = Promise.all(pending.map(img => new Promise(resolve => {
        img.addEventListener('load', resolve, {once:true});
        img.addEventListener('error', resolve, {once:true});
        if (img.complete) resolve();
      })));
      Promise.race([loaded, new Promise(resolve => setTimeout(resolve, 2500))]).then(() => {
        events.forEach(name => window.removeEventListener(name, stop));
        if (!interrupted && location.hash === startHash && target?.isConnected) target.scrollIntoView();
      });
    }
  }
}

const imageDialog = document.querySelector('#image-dialog');
const imagePreview = document.querySelector('#image-preview');
const imageViewport = document.querySelector('#image-viewport');
const imageZoomLabel = document.querySelector('#image-zoom-label');
let imageOpener;
let imageZoom = 1;
function updateImageSize() {
  if (!imageDialog.open || !imagePreview.naturalWidth || !imagePreview.naturalHeight) return;
  const fit = Math.min(imageViewport.clientWidth / imagePreview.naturalWidth,
                       imageViewport.clientHeight / imagePreview.naturalHeight);
  imagePreview.style.width = Math.max(1, Math.floor(imagePreview.naturalWidth * fit * imageZoom)) + 'px';
  imageZoomLabel.textContent = imageZoom === 1 ? '适应窗口' : Math.round(imageZoom * 100) + '%';
}
function setImageZoom(value) {
  imageZoom = Math.max(0.5, Math.min(4, value));
  updateImageSize();
}
imagePreview.addEventListener('load', updateImageSize);
window.addEventListener('resize', updateImageSize);
document.querySelector('#image-zoom-in').addEventListener('click', () => setImageZoom(imageZoom * 1.25));
document.querySelector('#image-zoom-out').addEventListener('click', () => setImageZoom(imageZoom / 1.25));
document.querySelector('#image-zoom-fit').addEventListener('click', () => { setImageZoom(1); imageViewport.scrollTo(0, 0); });
function prepareArticleImages() {
  main.querySelectorAll('.article-section img').forEach(img => {
    if (img.closest('a, button')) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'image-zoom-trigger';
    button.setAttribute('aria-label', `放大图片：${img.alt || '文章配图'}`);
    img.replaceWith(button);
    button.append(img);
  });
}
function closeImage() {
  imageDialog.close();
  imageOpener?.focus();
}
imageDialog.querySelector('.image-close').addEventListener('click', closeImage);
imageDialog.addEventListener('cancel', event => { event.preventDefault(); closeImage(); });
imageDialog.addEventListener('click', event => { if (event.target === imageDialog) closeImage(); });

function snippet(text, query) {
  const content = String(text || '').replace(/\s+/g, ' ').trim();
  const index = content.toLocaleLowerCase().indexOf(query);
  if (index < 0) return content.slice(0, 90) + (content.length > 90 ? '…' : '');
  const start = Math.max(0, index - 35), end = Math.min(content.length, index + query.length + 55);
  return (start ? '…' : '') + content.slice(start, end) + (end < content.length ? '…' : '');
}
function search() {
  const q = input.value.trim().toLocaleLowerCase();
  const hits = [];
  for (const a of articles) {
    const matches = q ? a.sections.filter(s => (s.title + ' ' + s.text).toLocaleLowerCase().includes(q)) : [];
    if (matches.length) {
      matches.forEach(s => hits.push({a, section:s, excerpt:snippet(s.text, q)}));
    } else if (!q || (a.title + ' ' + a.category).toLocaleLowerCase().includes(q)) {
      hits.push({a, section:null, excerpt:snippet(a.sections[0]?.text, q)});
    }
  }
  results.innerHTML = hits.length ? `<p class="result-count">${q ? `找到 ${hits.length} 条结果` : '全部文章'}</p>${hits.map(({a, section, excerpt}) => {
    const href = '#article/' + encodeURIComponent(a.id) + (section ? '?section=' + encodeURIComponent(section.id) : '');
    return `<a href="${href}" data-result><span>${esc(a.category)}${isAdmin(a) ? ' · 管理员专用' : ''}</span><b>${esc(a.title)}</b>${section ? `<span class="search-section">${esc(section.title)}</span>` : ''}${excerpt ? `<p>${esc(excerpt)}</p>` : ''}</a>`;
  }).join('')}` : '<div class="no-results"><b>没有找到相关文章</b><p>请尝试其他关键词。</p></div>';
}
function openSearch() { if (dialog.open) return; searchOpener = document.activeElement; input.value = ''; search(); dialog.showModal(); input.focus(); }
function closeSearch() { dialog.close(); searchOpener?.focus(); }
input.addEventListener('input', search);
document.querySelector('#close-search').addEventListener('click', closeSearch);
dialog.addEventListener('cancel', e => { e.preventDefault(); closeSearch(); });
dialog.addEventListener('click', e => { if (e.target === dialog) closeSearch(); });
document.addEventListener('click', e => {
  const imageButton = e.target.closest('.image-zoom-trigger');
  if (imageButton) {
    const img = imageButton.querySelector('img');
    imageOpener = imageButton;
    imageZoom = 1;
    imagePreview.style.width = '';
    imagePreview.src = img.src;
    imagePreview.alt = img.alt || '文章图片';
    imageDialog.showModal();
    updateImageSize();
    imageViewport.scrollTo(0, 0);
  }
  if (e.target.closest('[data-search]')) openSearch();
  const result = e.target.closest('[data-result]');
  if (result) { closeSearch(); if (result.hash === location.hash) { e.preventDefault(); route(); } }
  const section = e.target.closest('[data-section]');
  if (section) document.getElementById(section.dataset.section)?.scrollIntoView({behavior: 'smooth'});
  const module = e.target.closest('[data-module]');
  if (module) { e.preventDefault(); document.getElementById(module.dataset.module)?.scrollIntoView({behavior: 'smooth'}); }
});
document.addEventListener('keydown', e => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openSearch(); } });
window.addEventListener('hashchange', route);
route();
