'use strict';
const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const money = value => 'NT$ ' + Number(value).toLocaleString('zh-TW');
const state = {content:null, expected:null, seed:'', worker:null, pending:new Map(), requestId:0, ready:false, page:'overview', lesson:0, table:0, drafts:{}, custom:null, revision:0};
const main = $('#main');
$('.skip-link').addEventListener('click', event => {event.preventDefault();main.focus();main.scrollIntoView();});
const names = {overview:'案例總覽',design:'資料庫設計',lab:'SQL 實驗室',compare:'結果比較',guide:'作品解說'};
const stockSQL = `WITH incoming AS (
 SELECT product_id, SUM(quantity) AS qty FROM stock_receipts GROUP BY product_id
), outgoing AS (
 SELECT si.product_id, SUM(si.quantity) AS qty
 FROM sale_items si JOIN sales s ON s.sale_id=si.sale_id
 WHERE s.status='completed' GROUP BY si.product_id
)
SELECT p.product_id, p.name, p.opening_stock, COALESCE(i.qty,0) AS received,
 COALESCE(o.qty,0) AS sold, p.opening_stock+COALESCE(i.qty,0)-COALESCE(o.qty,0) AS stock,
 p.reorder_level
FROM products p LEFT JOIN incoming i ON i.product_id=p.product_id
LEFT JOIN outgoing o ON o.product_id=p.product_id ORDER BY p.product_id;`;

function toast(message) {
  const el = $('#toast'); el.textContent = message; el.classList.add('show');
  clearTimeout(toast.timer); toast.timer = setTimeout(() => el.classList.remove('show'), 3000);
}
function setStatus(message, failed=false) {
  $('#engine-status').innerHTML = `<span class="dot ${failed?'failed':''}"></span>${escapeHTML(message)}`;
}
async function loadFile(path, json=false) {
  const response = await fetch(new URL(path, document.baseURI));
  if (!response.ok) throw new Error(`無法讀取 ${path}（${response.status}）`);
  return json ? response.json() : response.text();
}
async function startEngine() {
  state.ready = false; setStatus('SQL 引擎準備中');
  state.worker = new Worker(new URL('./sql-worker.js', document.baseURI));
  return new Promise((resolve,reject) => {
    const initTimer = setTimeout(() => reject(new Error('SQL 引擎載入逾時，請重新整理頁面。')), 20000);
    state.worker.onmessage = ({data}) => {
      if (data.type === 'ready') {
        clearTimeout(initTimer); state.ready=true; setStatus('SQLite 已就緒'); resolve();
      } else if (data.type === 'initError') {clearTimeout(initTimer);reject(new Error(data.error));}
      else if (data.type === 'result') {
        const request = state.pending.get(data.id);
        if (request) { clearTimeout(request.timer);state.pending.delete(data.id);request.resolve(data); }
      }
    };
    state.worker.onerror = event => {clearTimeout(initTimer);reject(new Error(event.message || 'SQL 引擎無法載入'));};
    state.worker.postMessage({type:'init',seedSQL:state.seed});
  });
}
function executeSQL(sql) {
  if (!state.ready) return Promise.reject(new Error('查詢引擎尚未就緒，請稍後再試。'));
  return new Promise((resolve,reject) => {
    const id = ++state.requestId;
    const timer = setTimeout(async () => {
      state.worker.terminate();
      for (const request of state.pending.values()) {clearTimeout(request.timer);request.reject(new Error('查詢超過 8 秒，已停止執行。請縮小資料範圍後重試。'));}
      state.pending.clear();
      try {await startEngine();toast('查詢引擎已重新準備完成');} catch(error) {setStatus('引擎載入失敗',true);toast(error.message);}
    },8000);
    state.pending.set(id,{resolve,reject,timer});
    state.worker.postMessage({type:'run',id,sql});
  });
}
function tableHTML(result, caption='查詢結果') {
  if (!result || !Array.isArray(result.columns)) return '<div class="empty-state">沒有結果資料表。</div>';
  const count = result.rowCount ?? result.values.length;
  return `<div class="table-wrap"><table><caption class="visually-hidden">${escapeHTML(caption)}</caption><thead><tr>${result.columns.map(c=>`<th scope="col">${escapeHTML(c)}</th>`).join('')}</tr></thead><tbody>${result.values.map(row=>`<tr>${row.map(value=>`<td>${value===null?'<span class="null">NULL</span>':escapeHTML(value)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>${count===0?'<div class="empty-state">查詢成功，符合條件的資料為 0 筆。</div>':''}${count>300?`<p class="mini-label">共 ${count.toLocaleString()} 筆，畫面顯示前 300 筆。</p>`:''}`;
}
function outputHTML(data) {
  if (data.error) return `<div class="notice error"><strong>SQL 執行錯誤</strong><pre>${escapeHTML(data.error)}</pre><p>請檢查資料表、欄位名稱與語法，修改後可以再次執行。</p></div>`;
  if (!data.results.length) return `<div class="notice success">SQL 執行完成，本次變更 ${data.changed} 筆資料；沒有回傳資料表。可在同次執行後加入 SELECT 查看變更。</div>`;
  return data.results.map((r,i)=>`<div class="query-output">${data.results.length>1?`<h4>結果 ${i+1}</h4>`:''}<div class="result-status success"><span>✓ 執行成功 · ${(r.rowCount??r.values.length).toLocaleString()} 筆</span><span>${Number(data.ms).toFixed(1)} ms</span></div>${tableHTML(r)}</div>`).join('');
}
function pageHeading(eyebrow,title,description,actions='') {
  return `<div class="page-heading"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${description}</p></div>${actions?`<div class="heading-actions">${actions}</div>`:''}</div>`;
}
function route() {
  const [page,lesson] = location.hash.slice(1).split('/');
  state.page=names[page]?page:'overview';state.revision++;
  if (state.page==='lab' && lesson) {
    const index = state.content.lessons.findIndex(item=>String(item.id)===lesson);
    if(index>=0){state.lesson=index;state.custom=null;}
  }
  $$('[data-nav]').forEach(a=>{a.classList.toggle('active',a.dataset.nav===state.page);a.setAttribute('aria-current',a.dataset.nav===state.page?'page':'false');});
  $('#breadcrumb').textContent='WORKSPACE / '+names[state.page];
  document.title=names[state.page]+'｜角落選物 MINI MART';
  ({overview:renderOverview,design:renderDesign,lab:renderLab,compare:renderCompare,guide:renderGuide}[state.page])();
  window.scrollTo({top:0,behavior:'instant'});
}
async function renderOverview() {
  const rev=state.revision;
  main.innerHTML=pageHeading('THE EVERYDAY DATA PROJECT','把小店的日常，變成資料的答案。','一個以便利商店為情境，可以自己動手操作的 SQL 查詢作品。',`<a class="btn secondary" href="./seed.sql" download>↓ 下載樣本 SQL</a>`)+`
  <section class="hero"><div class="hero-copy"><span class="pill">角落選物 · 商品與庫存分析</span><h2>每一筆庫存，<br>都有 SQL 的答案<span>。</span></h2><p>什麼賣得最好？哪些商品該補貨？<br>從一筆銷售出發，讀懂這間小店的營運日常。</p><div class="heading-actions"><a class="btn primary" href="#lab">開始查詢 <span>↗</span></a><a class="text-link" href="#design">先認識資料庫 →</a></div><div class="hero-foot">自建模擬資料 <span>／</span> 固定基準日 2026.11.18</div></div>
  <div class="hero-visual" aria-hidden="true"><div class="store-sign">MINI MART <span>OPEN DAILY</span></div><div class="store-awning"></div><div class="store-window"><div class="shelf"><i class="bottle"></i><i class="bottle alt"></i><i class="bottle light"></i><i class="box"></i><i class="box alt"></i></div><div class="shelf"><i class="box light"></i><i class="box"></i><i class="bottle alt"></i><i class="box alt"></i><i class="bottle light"></i></div></div><div class="store-bottom">GOOD THINGS, GOOD DATA.</div><div class="floating-label">SELECT a little insight.</div></div></section>
  <section class="stats-grid" aria-label="作品規模">${[['06','關聯資料表','商品、進貨與銷售，完整串接'],['100','筆模擬資料','包含取消、零銷售與異常案例'],['10','個 SQL 查詢','從基本篩選到庫存分析'],['04','組結果比較','改一段 SQL，看懂不同結果']].map(([n,l,f])=>`<div class="stat-card"><div class="stat-label">${l}</div><div class="stat-value">${n}<span>↗</span></div><div class="stat-foot">${f}</div></div>`).join('')}</section>
  <section class="grid-two"><article class="panel"><div class="panel-header"><div><span class="eyebrow">STOCK WATCH</span><h2>今天，哪些商品該補貨？</h2></div><a class="text-link" href="#lab">用 SQL 找答案 ↗</a></div><div class="panel-body" id="stock-preview"><div class="empty-state">正在計算庫存…</div></div></article><article class="panel"><div class="panel-header"><div><span class="eyebrow">SALES MIX</span><h2>各分類已完成銷售額</h2></div><span class="tag">取消單已排除</span></div><div class="panel-body" id="sales-chart"><div class="empty-state">正在整理銷售…</div></div></article></section>
  <section class="case-grid"><article class="case-card"><span class="icon-circle">01</span><h3>誰會用這份資料？</h3><p>便利商店店長與補貨人員，用來掌握商品銷量、庫存及供應商資訊。</p></article><article class="case-card"><span class="icon-circle">02</span><h3>要解決什麼問題？</h3><p>把分散的進貨與銷售紀錄整理起來，找出補貨清單、熱銷品與零銷售商品。</p></article><article class="case-card"><span class="icon-circle">03</span><h3>為什麼使用關聯資料庫？</h3><p>商品、訂單與明細各自保存，透過主鍵與外鍵串接，減少重複並讓統計規則一致。</p></article></section>
  <div class="notice"><strong>先記住兩個規則</strong><p>目前庫存＝期初庫存＋進貨數量－已完成訂單的銷售數量。營收使用「明細成交單價 × 數量」，取消單不計營收也不扣庫存。負庫存代表需要盤點的模擬異常，會保留原值。</p></div>`;
  try {
    const [stock,categories]=await Promise.all([executeSQL(stockSQL),executeSQL(`SELECT c.name AS category, COALESCE(SUM(CASE WHEN s.status='completed' THEN si.quantity*si.unit_price ELSE 0 END),0) AS revenue FROM categories c LEFT JOIN products p ON p.category_id=c.category_id LEFT JOIN sale_items si ON si.product_id=p.product_id LEFT JOIN sales s ON s.sale_id=si.sale_id GROUP BY c.category_id,c.name ORDER BY revenue DESC,c.category_id;`)]);
    if(rev!==state.revision)return;
    if(stock.error||categories.error)throw new Error(stock.error||categories.error);
    const low=stock.results[0].values.filter(r=>r[5]<=r[6]);
    $('#stock-preview').innerHTML=`<div class="table-wrap"><table><thead><tr><th>商品</th><th>目前庫存</th><th>補貨門檻</th><th>狀態</th></tr></thead><tbody>${low.map(r=>`<tr><td>${escapeHTML(r[1])}</td><td><strong>${r[5]}</strong></td><td>${r[6]}</td><td><span class="stock-pill ${r[5]<0?'negative':'low'}">${r[5]<0?'待盤點':'需補貨'}</span></td></tr>`).join('')}</tbody></table></div><p class="mini-label">庫存小於或等於補貨門檻即列入；資料由實際 SQL 計算。</p>`;
    const rows=categories.results[0].values,max=Math.max(1,...rows.map(r=>r[1]));
    $('#sales-chart').innerHTML=`<div class="bar-chart">${rows.map((r,i)=>`<div class="bar-row"><div><span>${escapeHTML(r[0])}</span><strong>${money(r[1])}</strong></div><div class="bar-track"><div class="bar-fill color-${i%3}" style="width:${r[1]/max*100}%"></div></div></div>`).join('')}</div><p class="mini-label">總營收 ${money(rows.reduce((s,r)=>s+r[1],0))} · 以歷史成交價計算</p>`;
  }catch(error){if(rev===state.revision){$('#stock-preview').innerHTML=`<div class="notice error">${escapeHTML(error.message)}</div>`;$('#sales-chart').textContent='資料計算未完成。';}}
}
function renderERD() {
  const positions={categories:[20,15,250],suppliers:[20,300,250],products:[390,90,280],stock_receipts:[790,10,270],sales:[400,400,270],sale_items:[790,310,270]};
  const edges=[['M270 62 H325 V132 H390',285,50,368,120],['M270 350 H325 V235 H390',285,338,368,223],['M670 130 H730 V58 H790',684,118,767,46],['M670 245 H730 V362 H790',684,234,767,350],['M670 445 H730 V420 H790',684,434,767,408]];
  return `<div class="erd-board"><svg viewBox="0 0 1080 550" role="img" aria-labelledby="erd-title erd-description"><title id="erd-title">角落選物六張資料表實體關聯圖</title><desc id="erd-description">分類一對多商品；供應商一對多商品；商品一對多進貨紀錄；商品一對多銷售明細；銷售訂單一對多銷售明細。銷售訂單與商品透過明細形成多對多。</desc><defs><pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#d8dfd5"/></pattern></defs><rect width="1080" height="550" fill="url(#dots)"/>${edges.map(([d,x1,y1,x2,y2])=>`<path d="${d}" fill="none" stroke="#80a391" stroke-width="2"/><text x="${x1}" y="${y1}" class="erd-cardinality">1</text><text x="${x2}" y="${y2}" class="erd-cardinality">N</text>`).join('')}${state.content.tables.map(table=>{
    const [x,y,w]=positions[table.name];const h=52+table.columns.length*24;
    return `<g transform="translate(${x},${y})"><rect width="${w}" height="${h}" rx="12" fill="white" stroke="#d2dfd3"/><path d="M12 0H${w-12}Q${w} 0 ${w} 12V40H0V12Q0 0 12 0" fill="#173f35"/><text x="14" y="26" fill="white" font-size="14" font-weight="600">${escapeHTML(table.name)} · ${escapeHTML(table.label)}</text>${table.columns.map((c,i)=>`<text x="14" y="${62+i*24}" fill="${c.key?'#225f45':'#58685e'}" font-size="13" font-family="monospace">${escapeHTML((c.key?(c.key.startsWith('FK')?'FK':c.key==='UNIQUE'?'UQ':c.key)+' ':'')+c.name)}</text>`).join('')}</g>`;
  }).join('')}</svg></div>`;
}
function renderDesign() {
  main.innerHTML=pageHeading('DATABASE DESIGN','每一張表，都有自己的角色。','先看懂資料如何連接，再開始寫查詢。主鍵識別一筆資料，外鍵建立資料之間的關係。',`<a class="btn secondary" href="./seed.sql" download>↓ 完整建表與樣本 SQL</a>`)+`
  <section class="panel"><div class="panel-header"><div><span class="eyebrow">ENTITY RELATIONSHIP DIAGRAM</span><h2>資料庫關聯圖</h2></div><div class="heading-actions"><span class="tag">PK 主鍵</span><span class="tag">FK 外鍵</span><span class="tag">1 : N 一對多</span></div></div>${renderERD()}<div class="panel-body relation-list">${[['分類','商品'],['供應商','商品'],['商品','進貨紀錄'],['商品','銷售明細'],['銷售訂單','銷售明細']].map(([a,b])=>`<span class="relation-chip">${a} <b>1 → N</b> ${b}</span>`).join('')}<p class="mini-label">本案例每項商品指定一個主要供應商。訂單與商品為多對多，透過銷售明細拆解；每個實體方框列出實際欄位。</p></div></section>
  <section class="panel"><div class="panel-header"><div><span class="eyebrow">SCHEMA & SAMPLE DATA</span><h2>欄位字典與樣本資料</h2></div><span class="tag">與執行查詢使用相同資料</span></div><div class="table-tabs" role="tablist" aria-label="資料表">${state.content.tables.map((t,i)=>`<button class="tab-button ${i===state.table?'active':''}" role="tab" aria-selected="${i===state.table}" aria-controls="schema-data" id="table-tab-${i}" data-table="${i}">${escapeHTML(t.label)}<small>${escapeHTML(t.name)}</small></button>`).join('')}</div><div class="panel-body" id="schema-data" role="tabpanel"></div></section>
  <section class="grid-two"><div class="notice"><strong>為什麼拆成六張表？</strong><p>分類與供應商獨立保存，避免每個商品重複填寫名稱。訂單只保留交易時間與狀態，商品及數量寫進明細，讓一張訂單可以購買多種商品。</p></div><div class="notice warning"><strong>兩種價格，兩種用途</strong><p>products.unit_price 是目前售價；sale_items.unit_price 是當次成交價。歷史營收要使用明細成交價，才不會受到之後調價的影響。</p></div></section>`;
  $$('[data-table]').forEach(b=>b.addEventListener('click',()=>{state.table=Number(b.dataset.table);$$('[data-table]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-selected',String(x===b));});renderTableDetail();}));
  const tabs=$$('[data-table]');tabs.forEach((tab,i)=>tab.addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(i+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[next].click();tabs[next].focus();}}));
  renderTableDetail();
}
async function renderTableDetail() {
  const table=state.content.tables[state.table],rev=state.revision;
  const target=$('#schema-data');target.setAttribute('aria-labelledby','table-tab-'+state.table);
  target.innerHTML=`<h3>${escapeHTML(table.label)} <span class="mini-label">${escapeHTML(table.name)}</span></h3><p>${escapeHTML(table.description)}</p><div class="table-wrap"><table class="field-table"><thead><tr><th>欄位名稱</th><th>型態</th><th>鍵</th><th>可為 NULL</th><th>欄位說明</th></tr></thead><tbody>${table.columns.map(c=>`<tr><td><code>${escapeHTML(c.name)}</code></td><td>${escapeHTML(c.type)}</td><td>${c.key?`<span class="tag">${escapeHTML(c.key)}</span>`:'—'}</td><td>${c.nullable?'是':'否'}</td><td>${escapeHTML(c.description)}</td></tr>`).join('')}</tbody></table></div><h4>實際樣本資料 <span id="sample-count" class="tag">載入中</span></h4><div id="sample-data"></div>`;
  try {
    const data=await executeSQL(`SELECT * FROM ${table.name} ORDER BY ${table.columns[0].name};`);
    if(rev!==state.revision||state.content.tables[state.table].name!==table.name)return;
    if(data.error)throw new Error(data.error);
    $('#sample-data').innerHTML=tableHTML(data.results[0],table.label+'樣本資料');
    $('#sample-count').textContent=(data.results[0]?.values.length??0)+' 筆';
  }catch(error){if(rev===state.revision&&$('#sample-data'))$('#sample-data').textContent=error.message;}
}
function currentLesson() {return state.custom || state.content.lessons[state.lesson];}
function expectedFor(lesson) {return state.custom?state.custom.expected:state.expected.lessons[lesson.id];}
function renderLab() {
  const lesson=currentLesson(),draftKey=state.custom?'custom':String(lesson.id),expected=expectedFor(lesson);
  main.innerHTML=pageHeading('SQL PLAYGROUND','自己改一行，看看會發生什麼。','選一個問題、閱讀預期結果，再修改 SQL 並執行。結果由 SQLite 實際計算。')+`
  <div class="lab-layout"><aside class="lesson-sidebar"><div class="mini-label">查詢練習 · ${state.content.lessons.length} 題</div>${state.content.lessons.map((l,i)=>`<button class="lesson-button ${!state.custom&&i===state.lesson?'active':''}" data-lesson="${i}" ${!state.custom&&i===state.lesson?'aria-current="true"':''}><span>${String(i+1).padStart(2,'0')}</span><div>${escapeHTML(l.title.replace(/^\d+[｜|]\s*/,''))}<small>${escapeHTML(l.level)} · ${escapeHTML(l.concepts.join(' / '))}</small></div></button>`).join('')}<a class="text-link" href="#design">查看 ERD 與原始資料 ↗</a></aside><section class="lesson-content"><article class="panel"><div class="panel-header"><div><div class="lesson-meta"><span class="tag">${state.custom?'比較延伸':'QUERY '+String(state.lesson+1).padStart(2,'0')}</span>${lesson.concepts.map(c=>`<span class="tag">${escapeHTML(c)}</span>`).join('')}</div><h2>${escapeHTML(lesson.title)}</h2><p>${escapeHTML(lesson.question)}</p></div></div><div class="panel-body"><div class="editor-toolbar"><label for="sql-input">SQL 編輯器</label><div class="heading-actions"><button class="btn ghost small" id="restore-sql">還原 SQL</button><button class="btn ghost small" id="copy-sql">複製</button><button class="btn ghost small" id="download-sql">下載</button><button class="btn primary small" id="run-sql">▶ 執行 SQL</button></div></div><div class="code-editor"><div class="line-numbers" id="line-numbers" aria-hidden="true"></div><textarea class="sql-input" id="sql-input" aria-describedby="editor-help" spellcheck="false" autocapitalize="off" autocomplete="off"></textarea></div><div class="editor-footer" id="editor-help"><span>Ctrl / ⌘ + Enter 執行 · Tab 縮排 · Shift+Tab 離開</span><span>SQLite · 每次從相同樣本開始</span></div></div></article>
  <div class="result-grid"><section class="result-card"><div class="result-heading"><h3>預期結果</h3><span class="tag">原始 SQL · ${expected?.values.length??0} 筆</span></div><p class="mini-label">固定基準答案，修改 SQL 時不會跟著改變。</p>${tableHTML(expected,'原始SQL預期結果')}</section><section class="result-card" aria-live="polite" aria-atomic="false"><div class="result-heading"><h3>實際結果</h3><span class="tag" id="actual-badge">尚未執行</span></div><div id="actual-results"><div class="empty-state"><span class="empty-symbol">›_</span><p>準備好了嗎？按「執行 SQL」查看結果。</p></div></div></section></div><div class="notice"><strong>這題在學什麼？</strong><p>${escapeHTML(lesson.explanation)}</p></div><div class="notice warning"><strong>自由實驗，也能回到起點</strong><p>每次執行都重新載入樣本資料。你可以在同一次執行中先 UPDATE 再 SELECT 觀察變化；下次執行會回到原樣。輸入錯誤 SQL 會顯示引擎原始錯誤，修正後可再試。</p></div></section></div>`;
  const input=$('#sql-input');input.value=state.drafts[draftKey]??lesson.sql;
  const updateLines=()=>{$('#line-numbers').textContent=Array.from({length:input.value.split('\n').length},(_,i)=>i+1).join('\n');state.drafts[draftKey]=input.value;};
  updateLines();input.addEventListener('input',updateLines);input.addEventListener('scroll',()=>{$('#line-numbers').scrollTop=input.scrollTop;});
  input.addEventListener('keydown',event=>{
    if(event.key==='Enter'&&(event.ctrlKey||event.metaKey)){event.preventDefault();$('#run-sql').click();}
    if(event.key==='Tab'&&!event.shiftKey){event.preventDefault();const start=input.selectionStart,end=input.selectionEnd;input.setRangeText('  ',start,end,'end');updateLines();}
  });
  $$('[data-lesson]').forEach(b=>b.addEventListener('click',()=>{state.lesson=Number(b.dataset.lesson);state.custom=null;const hash='#lab/'+state.content.lessons[state.lesson].id;if(location.hash===hash){state.revision++;renderLab();}else location.hash=hash;}));
  $('#restore-sql').onclick=()=>{input.value=lesson.sql;updateLines();toast('已還原本題 SQL');};
  $('#copy-sql').onclick=async()=>{try{await navigator.clipboard.writeText(input.value);toast('已複製 SQL');}catch{input.focus();input.select();toast('請按 Ctrl / ⌘ + C 複製選取的 SQL');}};
  $('#download-sql').onclick=()=>download(input.value,'mini-mart-query.sql','text/plain;charset=utf-8');
  $('#run-sql').onclick=async()=>{
    if(!input.value.trim()){toast('請先輸入 SQL');return;}
    const revision=state.revision,button=$('#run-sql');button.disabled=true;button.textContent='執行中…';$('#actual-badge').textContent='執行中';
    try {
      const data=await executeSQL(input.value);
      if(revision!==state.revision)return;
      $('#actual-results').innerHTML=outputHTML(data);$('#actual-badge').textContent=data.error?'請修正 SQL':'已執行';
      if(!data.error&&data.results.length===1&&expected){const actual=data.results[0];const match=JSON.stringify(actual.columns)===JSON.stringify(expected.columns)&&JSON.stringify(actual.values)===JSON.stringify(expected.values);$('#actual-results').insertAdjacentHTML('beforeend',`<p class="mini-label">${match?'✓ 與原始 SQL 的預期結果相同（含欄名與排序）。':'結果與原始 SQL 不同，可以檢查篩選、欄位、排序或計算方式。不同結果不一定代表語法錯誤。'}</p>`);}
    }catch(error){if(revision===state.revision){$('#actual-results').innerHTML=outputHTML({error:error.message});$('#actual-badge').textContent='執行未完成';}}
    finally {if(revision===state.revision){button.disabled=false;button.textContent='▶ 執行 SQL';}}
  };
}
function download(content,filename,type) {
  const url=URL.createObjectURL(new Blob([content],{type}));const link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function renderCompare() {
  main.innerHTML=pageHeading('SAME QUESTION, DIFFERENT RESULTS','SQL 能執行，不代表答案就正確。','固定同一個問題，對照修改前後的 SQL 與結果，理解每一段改寫的理由。')+`
  <div class="notice"><strong>怎麼閱讀比較？</strong><p>每組先固定同一個業務問題，左邊呈現常見但不完整的寫法，右邊修正它。下方預先列出兩邊結果，也可以按「實際執行兩種 SQL」重新驗證。</p></div><div class="compare-list">${state.content.comparisons.map((c,i)=>{
    const expected=state.expected.comparisons[c.id];
    return `<article class="panel compare-card" id="comparison-${i}"><div class="panel-header"><div><div class="eyebrow">COMPARISON ${String(i+1).padStart(2,'0')}</div><h2>${escapeHTML(c.title)}</h2><p><strong>同一個問題：</strong>${escapeHTML(c.question)}</p></div><button class="btn primary small" data-run-compare="${i}">▶ 實際執行兩種 SQL</button></div><div class="panel-body"><div class="compare-grid">${[['before','修改前 · 常見問題',c.beforeSQL,c.beforeExplanation],['after','修改後 · 完整回答',c.afterSQL,c.afterExplanation]].map(([side,label,sql,explanation])=>`<section class="compare-side ${side}"><div class="result-heading"><h3>${label}</h3><button class="btn ghost small" data-open-compare="${i}" data-side="${side}">送到實驗室 ↗</button></div><pre class="sql-preview"><code>${escapeHTML(sql)}</code></pre><p>${escapeHTML(explanation)}</p><div class="mini-label" id="compare-label-${i}-${side}">預期執行結果 · ${expected[side].values.length} 筆</div><div id="compare-result-${i}-${side}">${tableHTML(expected[side])}</div></section>`).join('')}</div><div class="notice"><strong>為什麼結果改變？</strong><p>${escapeHTML(c.reason)}</p></div></div></article>`;
  }).join('')}</div>`;
  $$('[data-open-compare]').forEach(b=>b.onclick=()=>{
    const c=state.content.comparisons[Number(b.dataset.openCompare)],side=b.dataset.side;
    state.custom={id:'custom',title:c.title+' · '+(side==='before'?'修改前':'修改後'),question:c.question,sql:c[side+'SQL'],explanation:c.reason,concepts:['比較延伸'],expected:state.expected.comparisons[c.id][side]};
    delete state.drafts.custom;location.hash='#lab';
  });
  $$('[data-run-compare]').forEach(b=>b.onclick=async()=>{
    const i=Number(b.dataset.runCompare),c=state.content.comparisons[i],rev=state.revision;
    b.disabled=true;b.textContent='驗證中…';
    try {
      const results=await Promise.all([executeSQL(c.beforeSQL),executeSQL(c.afterSQL)]);
      if(rev!==state.revision)return;
      ['before','after'].forEach((side,index)=>{$(`#compare-label-${i}-${side}`).textContent='本次實際執行結果';$(`#compare-result-${i}-${side}`).innerHTML=outputHTML(results[index]);});
    }catch(error){if(rev===state.revision)toast(error.message);}
    finally{if(rev===state.revision){b.disabled=false;b.textContent='↻ 再執行一次';}}
  });
}
function renderGuide() {
  main.innerHTML=pageHeading('BEHIND THE PROJECT','能操作，也能說明為什麼。','用這份解說回顧資料庫設計與查詢邏輯，準備好自己介紹這個作品。',`<button class="btn secondary" id="print-guide">列印此頁</button>`)+`
  <section class="guide-grid"><article class="panel guide-card"><span class="eyebrow">01 / CASE</span><h2>案例背景</h2><p>「角落選物」是一間虛構便利商店。店長需要知道商品目前庫存、補貨優先順序、各分類營收，以及哪些商品沒有銷售。</p><p>資料涵蓋分類、供應商、商品、進貨、銷售訂單與銷售明細。所有姓名、商品及交易皆為自建模擬資料，分析基準固定為 2026-11-18。</p></article><article class="panel guide-card"><span class="eyebrow">02 / DESIGN</span><h2>設計重點</h2><ul class="tip-list"><li>六張表各保存一種實體或事件，使用主鍵與外鍵維護關係。</li><li>商品與訂單的多對多關係透過 sale_items 拆成兩個一對多。</li><li>一個商品在本案例指定一個主要供應商；進貨以逐商品的紀錄保存。</li><li>單價、數量與金額分開保存；銷售明細保留歷史成交價。</li></ul></article></section>
  <section class="panel"><div class="panel-header"><div><span class="eyebrow">BUSINESS RULES</span><h2>三個一定要說得清楚的計算</h2></div></div><div class="panel-body case-grid"><article><h3>01 · 庫存</h3><p><code>期初＋進貨－完成銷量</code></p><p>進貨與銷售先各自按商品彙總再連接。直接把兩種明細一起 JOIN，會互相重複而算錯。</p></article><article><h3>02 · 營收</h3><p><code>SUM(成交單價 × 數量)</code></p><p>僅計 status = 'completed' 的訂單；商品現價不等於每次交易的成交價。</p></article><article><h3>03 · 異常</h3><p><code>目前庫存 ≤ 補貨門檻</code></p><p>列為補貨候選。負庫存原樣呈現，代表待盤點異常，不會自動改成零。</p></article></div></section>
  <section class="grid-two"><article class="panel guide-card"><span class="eyebrow">A THREE-MINUTE WALKTHROUGH</span><h2>三分鐘展示順序</h2><ol class="tip-list"><li><strong>30 秒：</strong>介紹店長的補貨與營收問題。</li><li><strong>45 秒：</strong>打開 ERD，說明商品、訂單與明細關係。</li><li><strong>60 秒：</strong>執行一題庫存查詢，再改條件觀察結果；故意拼錯欄名展示錯誤訊息後修正。</li><li><strong>45 秒：</strong>展示一組修改前後比較，解釋為什麼能執行的 SQL 仍可能算錯。</li></ol></article><article class="panel guide-card"><span class="eyebrow">QUESTIONS TO PRACTICE</span><h2>教授可能會問</h2><details><summary>為什麼訂單與明細分開？</summary><p>一張訂單有多項商品。訂單時間與狀態只保存一次，每個品項的數量與成交單價存入明細，避免重複與更新不一致。</p></details><details><summary>為什麼 LEFT JOIN 之後不能直接 COUNT(*)？</summary><p>沒有匹配時，左表仍保留一列，右表欄位為 NULL。COUNT(*) 會算這一列；COUNT(右表主鍵) 只算非 NULL，才能得到零次。</p></details><details><summary>為什麼要先彙總再連接？</summary><p>同一商品若有 2 筆進貨、3 筆銷售，直接連接會產生 6 列，導致重複加總。兩邊先各算成一筆，再連接就能避免。</p></details><details><summary>為什麼每次執行都從相同資料開始？</summary><p>讓所有題目的預期結果可重現。修改資料只影響同次執行，不會讓後續練習的基準答案失效。</p></details></article></section>
  <section class="panel"><div class="panel-header"><div><span class="eyebrow">ASSIGNMENT CHECKLIST</span><h2>作業要求對照</h2></div></div><div class="panel-body"><ul class="check-list"><li>案例背景：使用者、情境與要解決的問題。</li><li>資料庫設計：ERD、主外鍵、欄位字典與實際樣本。</li><li>查詢操作：自然語言題目、可編輯 SQL、預期結果。</li><li>實際執行：SQLite 計算結果、零筆資料與原始錯誤訊息。</li><li>結果比較：同一問題的前後 SQL、結果、差異原因。</li></ul><p class="mini-label">交付前另外確認：GitHub Pages 公開網址可直接開啟，並依課堂規定提交網址。作品提供解說，仍需由作者理解後自行報告。</p></div></section>
  <div class="notice"><strong>使用範圍與資料說明</strong><p>本作品是 SQL 學習與資料分析展示，使用 SQLite 語法。金額為新臺幣，日期以固定模擬資料為準。畫面最多呈現每個結果集前 300 筆，超過 8 秒的查詢會停止並重建引擎。SQL 引擎為 sql.js 1.13.0，依其開源授權使用。</p><a class="text-link" href="./README.md" download>下載操作與部署說明 ↓</a> <a class="text-link" href="./seed.sql" download>下載全部建表與樣本 SQL ↓</a></div>`;
  $('#print-guide').onclick=()=>window.print();
}
async function boot() {
  try {
    [state.content,state.expected,state.seed]=await Promise.all([loadFile('./content.json',true),loadFile('./expected.json',true),loadFile('./seed.sql')]);
    await startEngine();window.addEventListener('hashchange',route);route();
  } catch(error) {
    setStatus('載入未完成',true);
    main.innerHTML=`<div class="loading-card"><span class="empty-symbol">!</span><h1>資料還沒準備好</h1><p>${escapeHTML(error.message)}</p><p>請透過 GitHub Pages 或本機 HTTP 伺服器開啟，並確認所有檔案（包含 vendor 資料夾）都已上傳。</p><button class="btn primary" id="retry-load">重新載入</button></div>`;
    $('#retry-load').onclick=()=>location.reload();
  }
}
boot();
