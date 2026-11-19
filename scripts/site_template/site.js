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

const paths = {
  employee: {title:'普通员工', subtitle:'查找和阅读与自己有关的流程与文件', ids:['employee-login','employee-portal','employee-find-read','employee-tasks','employee-help']},
  po: {title:'PO／文件编辑人员', subtitle:'从流程基础到编写、保存和发布', ids:['document-types','process-management','po-responsibilities','platform-login','portal-workbench','curriculum-draft-01','po-practical-case','curriculum-draft-05','process-attributes-save','process-diagram-roles','process-publish-revisions','process-cancellation-review','curriculum-draft-13','po-practical-case-standard','forms-attachments-upload']},
  admin: {title:'平台管理员', subtitle:'管理授权、流程监控与系统维护', ids:['curriculum-draft-19','curriculum-draft-20','curriculum-draft-21','curriculum-draft-24','curriculum-draft-25','curriculum-draft-26']}
};
const pathItems = key => (paths[key]?.ids || []).map(id => articles.find(a => a.id === id)).filter(Boolean);
const roleArticleHref = (a, role) => '#article/' + encodeURIComponent(a.id) + (role ? '?role=' + encodeURIComponent(role) : '');
const roleCards = () => [['employee','01','查阅流程与制度'],['po','02','编写和发布流程文件'],['admin','03','权限、监控与系统维护']].map(([key,num,caption]) => `<a class="role-card role-card-${key}" href="#path/${key}"><span class="role-index">${num} / 学习路径</span><span class="role-symbol" aria-hidden="true">${key==='employee'?'◉':key==='po'?'✎':'⚙'}</span><h3>${esc(paths[key].title)}</h3><p>${esc(caption)}</p><span class="role-enter">开始学习 <span aria-hidden="true">↗</span></span></a>`).join('');
function home() {
  return `<div class="academy-home"><section class="academy-hero" aria-labelledby="academy-title">
    <p class="academy-name">流程管理平台学习与操作中心</p><h1 id="academy-title">理解流程管理，<br>掌握流程管理平台操作。</h1>
    <p class="academy-description">选择适合自己的学习路径，<br class="mobile-break">学习平台使用与日常操作。</p>
    </section><section id="choose-path" class="role-home" aria-label="选择学习路径">
    <div class="role-cards">${roleCards()}</div></section></div>`;
}
const roleModules = {
  employee: [
    {name:'登录与认识平台', ids:['employee-login','employee-portal']},
    {name:'查阅文件与工作信息', ids:['employee-find-read','employee-tasks']},
    {name:'遇到问题寻求帮助', ids:['employee-help']}
  ],
  po: [
    {name:'流程管理基础', category:'流程管理基础', number:1},
    {name:'认识流程管理平台', category:'认识流程管理平台', number:2},
    {name:'流程文件编写指导', category:'流程文件编写指导', number:3},
    {name:'制度与规范文件编写', category:'制度与规范文件编写', number:4},
    {name:'表单与附件', category:'表单与附件', number:5}
  ],
  admin: [
    {name:'权限管理', ids:['curriculum-draft-19']},
    {name:'流程监控与问题处理', ids:['curriculum-draft-20','curriculum-draft-21']},
    {name:'内容与系统配置', ids:['curriculum-draft-24','curriculum-draft-25','curriculum-draft-26']}
  ]
};
function rolePath(key) {
  const role = paths[key];
  if (!role) return '<div class="page-width empty-page"><h1>没有找到学习路径</h1><a href="#home">返回首页</a></div>';
  const items = pathItems(key);
  const modules = roleModules[key].map(module => ({...module, articles:items.filter(a => module.ids ? module.ids.includes(a.id) : a.category === module.category)})).filter(module => module.articles.length);
  return `<div class="page-width learning-page course-shell role-course"><aside class="learning-aside"><p class="eyebrow">学习目录</p><nav class="learning-toc" aria-label="${esc(role.title)}学习目录">${modules.map((g,i) => `<div class="role-toc-group"><div class="role-toc-row"><button class="role-toc-toggle" type="button" aria-expanded="${i===0}" aria-controls="role-toc-articles-${i+1}" aria-label="${i===0 ? '收起' : '展开'}${esc(g.name)}文章" title="${i===0 ? '收起' : '展开'}文章" data-module-toggle><span aria-hidden="true">▸</span></button><a class="role-toc-module" href="#role-module-${i+1}" data-module="role-module-${i+1}"><span>${g.case ? '★' : (g.number ?? i+1)}</span><b>${esc(g.name)}</b></a></div><div class="role-toc-articles" id="role-toc-articles-${i+1}" ${i===0 ? '' : 'hidden'}>${g.articles.map(a => `<a href="${roleArticleHref(a,key)}">${esc(a.title)}</a>`).join('')}</div></div>`).join('')}</nav><a class="role-switch" href="#learning">← 选择其他学习路径</a></aside>
    <div class="course-main"><p class="breadcrumb"><a href="#home">首页</a> / <a href="#learning">培训课程</a> / ${esc(role.title)}</p><div class="learning-heading role-course-heading"><p class="eyebrow">YOUR LEARNING PATH</p><h1>${esc(role.title)}</h1><p>${esc(role.subtitle)}。</p><small>学习路径用于指引阅读，实际权限以系统配置为准。</small></div>
    <div class="learning-layout">${modules.length ? modules.map((g,i) => `<section class="stage" id="role-module-${i+1}"><div class="stage-number">${g.case ? '★' : (g.number ?? i+1)}</div><div class="stage-body"><p class="eyebrow">${g.case ? '完整实操案例' : '模块 '+(g.number ?? i+1)}</p><h2>${esc(g.name)}</h2><div class="stage-articles">${g.articles.map(a => `<div class="role-article"><a class="role-article-title" href="${roleArticleHref(a,key)}"><span class="document-symbol" aria-hidden="true">▤</span><div><b>${esc(a.title)}</b> ${adminBadge(a)}<small>${a.id==='po-practical-case'?'先看实操 · ':''}${esc(a.audience)}${preview && a.status!=='published'?' · 草稿待审核':''}</small></div><span aria-hidden="true">→</span></a></div>`).join('')}</div></div></section>`).join('') : '<p class="empty-state">该学习路径的文章正在整理，完成审核后展示。</p>'}</div></div></div>`;
}

function learning() {
  return `<div class="page-width role-selection"><p class="breadcrumb"><a href="#home">首页</a> / 培训课程</p><div class="role-selection-heading"><p class="eyebrow">LEARNING PATHS</p><h1>选择您的学习路径</h1><p>根据工作角色，找到适合自己的课程内容。</p></div><div class="role-cards">${roleCards()}</div></div>`;
}

const taskLabels = {'平台基础操作':'管理角色、岗位与岗位组', '流程文件编写':'编写、发布或作废流程文件', '制度文件编写':'编写制度文件', '表单与附件':'创建表单与上传附件', '管理员操作':'管理平台与处理异常'};
function guides() {
  const guideArticles = articles.filter(a => a.guideGroup);
  const guideGroups = [...new Set(guideArticles.map(a => a.guideGroup))].map(name => ({name, articles: guideArticles.filter(a => a.guideGroup === name)}));
  return `<div class="page-width guides-page"><p class="breadcrumb"><a href="#home">首页</a> / 操作指南</p><p class="eyebrow">BROWSE BY TASK</p><h1>按任务，找到操作说明。</h1><p class="lead">选择需要查看的文章，或按关键词搜索。</p><button class="button secondary" data-search>⌕ 搜索文章</button><div class="guide-groups">${guideGroups.map(g => `<section><h2>${esc(taskLabels[g.name] || g.name)}</h2><div>${g.articles.map(a => `<a href="#article/${encodeURIComponent(a.id)}"><div><h3>${esc(a.title)}</h3>${adminBadge(a)}<p>${esc(a.audience)}</p></div><span>→</span></a>`).join('')}</div></section>`).join('') || '<p class="empty-state">暂无可查看的操作指南。</p>'}</div></div>`;
}

function consecutiveGroups(items) {
  return items.reduce((result, article) => {
    const last = result[result.length - 1];
    if (last && last.name === article.category) last.articles.push(article);
    else result.push({name: article.category, articles: [article]});
    return result;
  }, []);
}

function articlePage(a, role) {
  const items = role && paths[role] && pathItems(role).some(item => item.id === a.id) ? pathItems(role) : articles;
  const currentRole = items === articles ? '' : role;
  const index = items.indexOf(a), prev = items[index - 1], next = items[index + 1];
  const backHref = currentRole ? '#path/' + currentRole : '#learning';
  const backLabel = currentRole ? '← 返回' + paths[currentRole].title + '学习路径' : '← 培训课程目录';
  return `<div class="reading-layout"><aside class="chapter-sidebar"><a class="back-home" href="${backHref}">${esc(backLabel)}</a><details class="chapter-details" open><summary>${currentRole ? "本路径文章" : "全部文章"}</summary><div>${(currentRole ? consecutiveGroups(items) : groups(items)).map(g => `<div class="chapter-group"><h3>${esc(g.name)}</h3>${g.articles.map(item => `<a ${item.id === a.id ? 'aria-current="page"' : ''} href="${roleArticleHref(item,currentRole)}">${esc(item.title)}</a>`).join('')}</div>`).join('')}</div></details><a class="sidebar-learning" href="#guides">↗ 按任务查阅</a></aside>
    <article class="article"><p class="breadcrumb"><a href="#home">首页</a> / ${currentRole ? `<a href="${backHref}">${esc(paths[currentRole].title)}学习路径</a> / ` : ""}${esc(a.category)}</p><div class="article-tags"><span>${esc(a.category)}</span>${adminBadge(a)}${preview ? `<span>${esc(a.status)}</span>` : ''}</div><h1 id="section-${esc(a.titleAnchor)}">${esc(a.title)}</h1><div class="article-meta"><span>适用：${esc(a.audience)}</span></div>
    ${preview ? '<div class="article-warning"><b>草稿预览</b><p>内容及截图需审核后再用于正式发布。</p></div>' : ''}
    ${a.sections.map(s => `<section class="article-section" id="${esc(s.id)}"><h2>${esc(s.title)}</h2>${s.html}</section>`).join('')}
    <div class="article-pagination">${prev ? `<a href="${roleArticleHref(prev,currentRole)}"><small>← 上一篇</small><b>${esc(prev.title)}</b></a>` : '<span></span>'}${next ? `<a href="${roleArticleHref(next,currentRole)}"><small>下一篇 →</small><b>${esc(next.title)}</b></a>` : `<a href="${backHref}"><small>返回目录 →</small><b>${currentRole ? esc(paths[currentRole].title) + '学习路径' : '查看培训目录'}</b></a>`}</div></article>
    <aside class="page-toc"><details class="page-details" open><summary>本页目录</summary>${(a.toc || a.sections).map(s => `<button class="heading-level-${s.level || 2}" data-section="${esc(s.id)}">${esc(s.title)}</button>`).join('')}<div class="toc-tip"><button data-search>⌕ 搜索相关内容</button></div></details></aside></div>`;
}

function route() {
  const hash = location.hash.slice(1) || 'home';
  let active = hash, title = '首页';
  if (hash.startsWith('article/')) {
    const id = hash.slice(8).split('?')[0], a = articles.find(item => item.id === id);
    active = '';
    if (a) { main.innerHTML = articlePage(a, new URLSearchParams(hash.split('?')[1] || '').get('role')); title = a.title; }
    else { main.innerHTML = '<div class="page-width empty-page"><h1>没有找到这篇文章</h1><p>请返回目录查找。</p><a href="#guides" class="button primary">查看操作指南</a></div>'; title = '文章未找到'; }
  } else if (hash.startsWith('path/')) { const key = hash.slice(5); main.innerHTML = rolePath(key); title = paths[key]?.title || '学习路径'; active = 'learning'; }
  else if (hash === 'learning') { main.innerHTML = learning(); title = '培训课程'; }
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
function setModuleExpanded(group, expanded) {
  const toggle = group.querySelector('[data-module-toggle]');
  const panel = group.querySelector('.role-toc-articles');
  const name = group.querySelector('.role-toc-module b').textContent;
  toggle.setAttribute('aria-expanded', String(expanded));
  toggle.setAttribute('aria-label', (expanded ? '收起' : '展开') + name + '文章');
  toggle.title = expanded ? '收起文章' : '展开文章';
  panel.hidden = !expanded;
}
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
  const toggle = e.target.closest('[data-module-toggle]');
  if (toggle) setModuleExpanded(toggle.closest('.role-toc-group'), toggle.getAttribute('aria-expanded') !== 'true');
  const module = e.target.closest('[data-module]');
  if (module) {
    e.preventDefault();
    const group = module.closest('.role-toc-group');
    if (group) group.closest('.learning-toc').querySelectorAll('.role-toc-group').forEach(item => setModuleExpanded(item, item === group));
    document.getElementById(module.dataset.module)?.scrollIntoView({behavior: 'smooth'});
  }
});
document.addEventListener('keydown', e => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openSearch(); } });
window.addEventListener('hashchange', route);
route();
