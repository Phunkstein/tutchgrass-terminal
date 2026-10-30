/* Tutchgrass Labs research terminal: renders /terminal/data/terminal.json. Missing sources show "unavailable". */
(function(){
const $=s=>document.querySelector(s);
const E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const NA=(what)=>`<p class="na">● ${E(what||'Source')} unavailable right now. No numbers are shown rather than guesses.</p>`;
const num=(v,d=2)=>v==null||isNaN(v)?'—':Number(v).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct=v=>v==null?'<span class="mute">—</span>':`<span class="${v>=0?'pos':'neg'}">${v>=0?'+':''}${num(v,2)}%</span>`;
const pm=id=>`https://pubmed.ncbi.nlm.nih.gov/${id}/`;
const ago=ts=>{if(!ts)return'';const m=Math.round((Date.now()/1000-ts)/60);return m<1?'just now':m<60?m+' min ago':m<2880?Math.round(m/60)+' h ago':Math.round(m/1440)+' d ago'};
const tag=t=>`<span class="tag t-${E(t)}">${E(t)}</span>`;
const cl=(cs,max)=>!cs||!cs.length?'<p class="small mute">No citations.</p>':'<ul class="cites">'+cs.slice(0,max||99).map(c=>`<li>${tag(c.type)}<a href="${E(c.url||pm(c.pmid))}" target="_blank" rel="noopener">${E(c.title)}</a> <span class="mute small">${E(c.first_author||'')} · ${E(c.journal||'')} ${E(c.year||'')}</span></li>`).join('')+'</ul>';
const ev=e=>`<span class="badge ev-${E(e)}">${E(String(e||'').toUpperCase())}</span>`;
const spark=(pts,w=96,h=28)=>{if(!pts||pts.length<2)return'';const mn=Math.min(...pts),mx=Math.max(...pts),r=mx-mn||1;
  const p=pts.map((v,i)=>`${(i/(pts.length-1)*w).toFixed(1)},${(h-2-(v-mn)/r*(h-4)).toFixed(1)}`).join(' ');
  const up=pts[pts.length-1]>=pts[0];return`<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true"><polyline fill="none" stroke="${up?'#15803d':'#b42318'}" stroke-width="1.5" points="${p}"/></svg>`};

const TG=window.TG=window.TG||{};
const GC={meta:'g-meta',rct:'g-rct',noplacebo:'g-nop',obs:'g-obs',mice:'g-mice',cells:'g-mice',review:'g-rev',case:'g-rev'};
TG.E=E;TG.gchip=(p,G)=>`<span class="badge gchip ${GC[p.grade]||''}">${E((G&&G[p.grade]&&G[p.grade].label)||p.grade_label||p.grade)}</span>`;
TG.AI_STUDY="AI-graded from the published study: software rules written with AI tools read each paper's PubMed record and abstract to set its grade. No person checks each grade. Always check the source.";
TG.AI_SCORE="Evidence levels come from the National Academies 2017 report, matched to each condition by AI tools; study counts are AI-graded automatically from PubMed. Always check the source.";
TG.AI_FIND="AI-graded: the grade and plain-words summary were written by AI from the cited studies; PubMed and DOI links were checked automatically. Not reviewed by a doctor. Always check the source.";
TG.aitag=(tip,l='AI-graded')=>`<span class="aitag" tabindex="0" role="note" title="${E(tip)}" data-tip="${E(tip)}">${E(l)} <i aria-hidden="true">ⓘ</i></span>`;
TG.paper=(p,G,L)=>`<article class="ns" id="pmid-${E(p.pmid)}"><div class="nst">${TG.gchip(p,G)}<span class="mono small mute">${E(p.date||'')}</span>${(p.conditions||[]).map(c=>`<a class="pill sm" href="/terminal/my/?c=${E(c)}">${E((L&&L[c])||c)}</a>`).join('')}</div>
  <a class="t" href="${E(p.url)}" target="_blank" rel="noopener">${E(p.title)}</a><div class="small mute">${E(p.first_author||'')} · ${E(p.journal||'')} · PMID ${E(p.pmid)}</div>
  <dl><dt>What they did</dt><dd>${E(p.plain&&p.plain.did)}</dd>${p.plain&&p.plain.found?`<dt>What the authors concluded</dt><dd>${E(p.plain.found)}</dd>`:''}<dt>Grade caveat</dt><dd class="cav">${E(p.plain&&p.plain.caveat)}</dd></dl>
  <div class="ft"><a class="small" href="${E(p.url)}" target="_blank" rel="noopener">Read on PubMed →</a><button class="btn sm ghost save" type="button" data-save="paper:${E(p.pmid)}">☆ Save</button></div></article>`;
TG.dec11=D=>{const el=$('#dec11');if(!el)return;if(!D){el.innerHTML=NA('Dec 11 tracker');return}
  const t=new Date(D.deadline).getTime(),syn=new Date(D.synthetic).getTime();
  el.innerHTML=`<div class="d11"><div class="d11h"><span class="lbl" style="margin:0">Dec 11, 2026 · federal hemp THC rule</span><div class="cd" aria-live="off"><b id="cd-d">–</b><small>days</small><b id="cd-h">–</b><small>hrs</small><b id="cd-m">–</b><small>min</small><b id="cd-s">–</b><small>sec</small></div></div>
  <p class="d11t"><b>${E(D.headline)}</b> <span class="dim">Synthetic-cannabinoid exclusion starts Nov 12 (<span id="cd-syn">–</span> days).</span></p>
  <details class="d11d"><summary class="small">Key dates &amp; sources</summary><ul class="small">${D.dates.map(x=>`<li><span class="mono">${E(x.date)}</span> ${E(x.text)}</li>`).join('')}</ul><p class="small">${D.sources.map(x=>`<a href="${E(x.url)}" target="_blank" rel="noopener">${E(x.label)}</a>`).join(' · ')} · <span class="mute">${E(D.note)}</span></p></details></div>`;
  const tick=()=>{let r=Math.max(0,t-Date.now())/1000;const dd=Math.floor(r/86400);r-=dd*86400;const hh=Math.floor(r/3600);r-=hh*3600;const mm=Math.floor(r/60),ss=Math.floor(r-mm*60);
    $('#cd-d').textContent=dd;$('#cd-h').textContent=String(hh).padStart(2,'0');$('#cd-m').textContent=String(mm).padStart(2,'0');$('#cd-s').textContent=String(ss).padStart(2,'0');
    $('#cd-syn').textContent=Math.max(0,Math.ceil((syn-Date.now())/864e5))};tick();setInterval(tick,1000)};
TG.week=d=>{const el=$('#thisweek');if(!el)return;const n=d.newstudies;if(!n){el.innerHTML=NA('New this week (PubMed)');return}
  const wk=Object.entries(n.week).filter(x=>x[1]>0).sort((a,b)=>b[1]-a[1]),tot=n.papers.filter(p=>(p.date||'')>=n.week_start).length;
  el.innerHTML=`<div class="wk"><span class="lbl" style="margin:0">New this week</span><b class="mono">${tot}</b><span class="small dim">new studies since ${E(n.week_start)}</span>${wk.map(([k,v])=>`<a class="pill" href="/terminal/my/?c=${E(k)}">${E(n.labels[k]||k)} <b class="mono">${v}</b></a>`).join('')||'<span class="small mute">None in the last 7 days.</span>'}<a class="small" href="#newstudies">See them explained →</a></div>`};
TG.feed=d=>{const n=d.newstudies,b=$('#ns-body');if(!b)return;if(!n){b.innerHTML=NA('PubMed new studies');return}
  $('#ns-meta').textContent=`${n.papers.length} papers · ${n.window.start} to ${n.window.end} · ${n.source}`;
  const gc={};n.papers.forEach(p=>gc[p.grade]=(gc[p.grade]||0)+1);
  const tabs=[['all','All',n.papers.length],['hi','Human RCT / meta-analysis',(gc.rct||0)+(gc.meta||0)+(gc.noplacebo||0)],['obs','Observational',gc.obs||0],['mice','Mice / cells only',(gc.mice||0)+(gc.cells||0)],['review','Reviews & cases',(gc.review||0)+(gc.case||0)]];
  const f={all:()=>true,hi:p=>['rct','meta','noplacebo'].includes(p.grade),obs:p=>p.grade==='obs',mice:p=>['mice','cells'].includes(p.grade),review:p=>['review','case'].includes(p.grade)};
  let lim=8;const show=k=>{document.querySelectorAll('#ns-tabs button').forEach(x=>x.setAttribute('aria-selected',x.dataset.k===k));const l=n.papers.filter(f[k]);
    b.innerHTML=l.length?l.slice(0,lim).map(p=>TG.paper(p,n.grades,n.labels)).join('')+(l.length>lim?`<button class="btn ghost more" type="button" data-more="${k}">Show all ${l.length}</button>`:''):'<p class="mute">None in this window. That is the honest answer.</p>';document.dispatchEvent(new CustomEvent('tg:rendered'))};
  $('#ns-tabs').innerHTML=tabs.map(t=>`<button role="tab" data-k="${t[0]}">${E(t[1])} <span class="mono small">${t[2]}</span></button>`).join('');
  $('#ns-tabs').onclick=e=>{const x=e.target.closest('button');if(x){lim=8;show(x.dataset.k)}};b.onclick=e=>{const m=e.target.closest('[data-more]');if(m){lim=999;show(m.dataset.more)}};show('all');
  $('#ns-foot').innerHTML=TG.aitag(TG.AI_STUDY)+' '+E(TG.AI_STUDY)+' Mice and cell results often do not hold in people. "Concluded" is the authors’ own wording, shortened. Research, not medical advice.'};
TG.board=d=>{const r=d.scoreboard,b=$('#sb-body');if(!b)return;if(!r||!r.length){b.innerHTML=NA('Scoreboard');return}
  $('#sb-meta').textContent='National Academies grade + PubMed 2025–26';
  b.innerHTML='<div class="scroll-x"><table class="sb"><thead><tr><th>#</th><th>Condition</th><th>Evidence</th><th class="num" title="Meta-analyses / reviews and RCTs among 2025–26 matches">High-grade 25–26</th><th class="num">New 30 d</th><th class="hide-m">What changed recently</th><th class="hide-m"></th></tr></thead><tbody>'+r.map(x=>`<tr><td class="mono">${x.rank}</td><td><a href="/terminal/my/?c=${E(x.id)}"><b>${E(x.emoji)} ${E(x.label)}</b></a></td><td>${ev(x.evidence==='not graded'?'not graded':x.evidence)}</td>
   <td class="num mono">${x.recent_high.meta} SR/MA <wbr>· ${x.recent_high.rct} RCT</td><td class="num mono">${x.new_30d}${x.new_mice_30d?`<div class="small mute">${x.new_mice_30d} animal</div>`:''}</td>
   <td class="small hide-m">${x.latest?`${tag(x.latest.tag)}<a href="${E(x.latest.url)}" target="_blank" rel="noopener">${E(x.latest.title)}</a> <span class="mute mono">${E(x.latest.date)}</span>`:'<span class="mute">No new meta-analysis or RCT in 2025–26.</span>'}</td>
   <td class="hide-m"><button class="btn sm ghost save" type="button" data-save="condition:${E(x.id)}" title="Save condition">☆</button></td></tr>`).join('')+'</tbody></table></div><p class="ainote">'+TG.aitag(TG.AI_SCORE)+' '+E(TG.AI_SCORE)+'</p><p class="small mute">Evidence = National Academies 2017 grade for the closest condition (strong / moderate / limited). Conditions with no formal grade are listed last. Rank is a reading aid, not a recommendation.</p>'};
if(document.getElementById('kpis'))fetch('/terminal/data/terminal.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw r.status;return r.json()}).then(render).catch(e=>{
  $('#built').textContent='data unavailable';document.querySelectorAll('.content .card [id$="-body"],#sci').forEach(el=>el.innerHTML=NA('Data'));});

function render(d){
  const S=d.scientist,L=d.lab,W=d.wire,So=d.social,M=d.market,P=d.prices,N=d.news,F=d.findings||[];
  $('#built').textContent='Updated '+(d.built||'')+' · '+ago(d.built_ts);
  // ---- counters
  const conds=S?S.conditions:[];const cites=conds.reduce((a,c)=>a+(c.citations||[]).length,0);
  const new30=conds.reduce((a,c)=>a+(+c.new_papers_30d||0),0);
  const msos=M&&M.rows?M.rows.find(r=>r.ticker==='MSOS'&&r.status==='ok'):null;
  const us=P&&P.series?P.series.find(s=>s.region==='US'&&s.status==='ok'&&s.points&&s.points.length):null;const usl=us?us.points[us.points.length-1]:null;
  const srcs=[];(d.source_status&&d.source_status.wire_sources||[]).forEach(s=>srcs.push({n:s.source,ok:s.status==='ok'}));
  (N&&N.sources||[]).forEach(s=>{if(!srcs.find(x=>x.n===s.source))srcs.push({n:s.source,ok:s.status==='ok'})});
  srcs.push({n:'Yahoo Finance (market)',ok:!!(M&&M.rows&&M.rows.some(r=>r.status==='ok'))});
  (P&&P.series||[]).forEach(s=>srcs.push({n:s.label,ok:s.status==='ok'&&!s.stale,stale:s.stale,none:s.status!=='ok'}));
  srcs.push({n:'X posts + X News (social)',ok:!!(So&&So.posts&&So.posts.length)});
  const okN=srcs.filter(s=>s.ok).length;
  const K=[[conds.length||'—','Conditions tracked'],[cites||'—','Verified PubMed citations'],[new30||'—','New papers, last 30 d'],[F.length||'—','Latest findings'],
    [N?N.total:'—','News items read'],[msos?'$'+num(msos.price):'n/a',`MSOS ${msos?'<em class="'+(msos.chg_pct>=0?'pos':'neg')+'">'+(msos.chg_pct>=0?'+':'')+num(msos.chg_pct)+'%</em>':'unavailable'}`],
    [usl?'$'+num(usl.value,0):'n/a',`US wholesale /lb ${usl?'<em class="'+(usl.chg_pct>=0?'pos':'neg')+'">'+(usl.chg_pct>=0?'+':'')+num(usl.chg_pct,1)+'%</em>':'unavailable'}`],[okN+'/'+srcs.length,'Sources live']];
  $('#kpis').innerHTML=K.map(k=>`<div class="kpi"><b>${k[0]}</b><span>${k[1]}</span></div>`).join('');
  // ---- sidebar legend (agent statuses now live in the agents bar, agents.js)
  const col={scientist:'#14532d',lab:'#5b3fa3',holistic:'#0e6b7a',wire:'#1f4f99',social:'#b4470f',grower:'#4d7c0f'};
  $('#agents').innerHTML=
    '<div class="card legendcard" style="padding:12px 14px"><div class="lbl" style="margin-top:0">Evidence tags</div><div class="legend">'+['RCT','SR','GUIDELINE','REPORT','HUMAN-OBS','PRECLINICAL','HORT','CASE','REVIEW','ANECDOTAL'].map(tag).join('')+'</div><p class="small mute" style="margin:8px 0 0">RCT = randomized trial · SR = systematic review · PRECLINICAL = animal/cell only · ANECDOTAL = not evidence.</p></div>';
  // ---- scientist
  if(!S){$('#sci').innerHTML=NA('Scientist');}else{
    $('#sci-meta').textContent=`${conds.length} conditions · ${cites} citations · ${S.dropped_unverified||0} unverified dropped · ${S.generated}`;
    $('#strain-note').textContent=S.strain_note+' Method: '+S.method;
    const FB={};F.forEach(f=>FB[f.sci]=f);
    $('#sci').innerHTML=conds.map(c=>{const g=L&&L.grower&&L.grower[c.id],h=L&&L.holistic&&L.holistic[c.id],r=c.recent,f=FB[c.id];
      return`<details class="cond" id="cond-${E(c.id)}"><summary><span class="cn">${E(c.name)}${c.last_updated?`<span class="upd" title="Newest new study on PubMed (checked ${E(c.checked||'')})">Updated ${E(c.last_updated.slice(5))}</span>`:''}</span><span>${ev(c.evidence)}</span><span class="tp">${E(c.top_pick)}</span><span class="tr">${E((c.terpenes||[]).join(', '))}</span><span class="num">${c.new_papers_30d??'—'}</span><span class="num">${(c.citations||[]).length}</span><span class="chev">▶</span></summary>
      <div class="det"><div>
        <div class="lbl">Top pick</div><div class="pick">${E(c.top_pick)}</div><p class="small dim" style="margin-top:4px">${E(c.chemotype)} · THC:CBD ${E(c.thc_cbd)}</p>
        <div class="lbl">Evidence</div><p>${ev(c.evidence)} <span class="small">${E(c.evidence_note)}</span></p>
        <div class="lbl">Why (what studies suggest)</div><p>${E(c.mechanism)}</p>
        <div class="lbl">Minor cannabinoids · terpenes</div><p>${(c.minors||[]).concat(c.terpenes||[]).map(x=>`<span class="pill">${E(x)}</span>`).join('')}</p>
        <div class="lbl">Typical strains · check the COA</div><p>${(c.strains||[]).map(x=>`<span class="pill">${E(x)}</span>`).join('')}</p><p class="small mute">Typically, not guaranteed. The same name tests differently by grower and batch.</p>
        <div class="lbl">Cautions</div><ul>${(c.cautions||[]).map(x=>`<li>${E(x)}</li>`).join('')}</ul>
        ${g?`<div class="lbl">Grower note</div><div class="note"><b>Target:</b> ${E(g.target)}<br><b>Genetics:</b> ${E(g.genetics)}<br><span class="mute">Factors: ${E((g.factor_names||[]).join(', '))}</span></div>`:''}
        ${h?`<div class="lbl">Holistic pairings</div><ul>${h.pairs.map(x=>`<li>${E(x)}</li>`).join('')}</ul>`:''}
      </div><div>
        ${f?`<div class="lbl">Latest finding</div><p><a href="${E(f.path)}"><b>${E(f.headline)}</b></a></p>`:''}
        <div class="lbl">PubMed citations (${(c.citations||[]).length})</div>${cl(c.citations)}
        <div class="lbl">Newest studies 2025–26 ${r?`<span class="mute">· ${r.matches} matches</span>`:''}</div>
        ${r&&r.studies&&r.studies.length?'<ul class="cites recent">'+r.studies.map(s=>`<li>${tag(s.tag)}<a href="${pm(s.pmid)}" target="_blank" rel="noopener">${E(s.title)}</a> <span class="mute small">${E(s.first_author)} · ${E(s.journal)} · ${E(s.date)}</span>${s.conclusion?`<span class="cc">${E(s.conclusion.length>230?s.conclusion.slice(0,227)+'…':s.conclusion)}</span>`:''}</li>`).join('')+'</ul>':'<p class="small mute">No recent-study list for this condition.</p>'}
        <div class="lbl">New papers, last 30 days</div><p><b class="mono">${c.new_papers_30d??'—'}</b> <span class="small dim">on PubMed · <a href="https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent('(cannabis OR cannabinoid OR cannabidiol) AND '+c.name.split('/')[0].trim())}&sort=date" target="_blank" rel="noopener">browse newest</a></span></p>
      </div></div></details>`}).join('');
    const open=()=>{const h=location.hash.match(/^#cond-(.+)/);const el=h&&document.getElementById('cond-'+h[1]);if(el){el.open=true;setTimeout(()=>el.scrollIntoView({block:'start'}),50);return true}};
    if(!open()&&innerWidth>760){const f=$('#sci details');if(f)f.open=true}
    addEventListener('hashchange',open);
  }
  // ---- latest findings
  $('#fgrid').innerHTML=F.length?F.map(f=>`<div class="fcard" id="finding-${E(f.slug)}"><a href="${E(f.path)}"><img src="${E(f.img)}" alt="${E(f.headline)}" loading="lazy" width="1600" height="900"></a><div class="fb"><div class="fc">${E(f.condition)}</div><a href="${E(f.path)}" style="color:inherit"><b>${E(f.headline)}</b></a><span class="badge grade g-${E(f.grade_cls)}">${E(f.grade)}</span> ${TG.aitag(TG.AI_FIND)}<p>${E(f.summary[0])}</p>${f.strains?`<p class="st"><b>Typical strains:</b> ${E(f.strains)}</p>`:''}<p class="small">${f.studies.map(s=>`<a href="${pm(s.pmid)}" target="_blank" rel="noopener">PubMed ${E(s.pmid)}</a>`).join(' · ')}</p><div class="ft"><a class="small" href="${E(f.path)}">Read the finding →</a><button class="btn sm ghost save" type="button" data-save="finding:${E(f.slug)}">☆ Save</button><a class="btn sm xbtn" href="${E(f.x_intent)}" target="_blank" rel="noopener">Share on X</a></div></div></div>`).join(''):NA('Findings');
  TG.dec11(d.dec11);TG.week(d);TG.feed(d);TG.board(d);
  // ---- lab
  if(!L)$('#lab-body').innerHTML=NA('Lab');else{const sp=L.compounds.find(c=>c.id===L.spotlight_id)||L.compounds[0];
    $('#lab-meta').textContent='spotlight '+L.spotlight_rule;
    $('#lab-body').innerHTML=`<div class="lbl" style="margin-top:0">Today's spotlight</div><div class="pick">${E(sp.name)}</div><p class="small dim">${E(sp.kind)} · ${E(sp.aroma)} ${ev(sp.evidence)}</p>
      <div class="lbl">Health angle</div><p>${E(sp.health)}</p><div class="lbl">Also found in</div><p class="small">${E(sp.also_in)}</p>
      <div class="lbl">Grow &amp; preserve</div><p class="small">${E(sp.grow)}</p>${cl(sp.citations,3)}
      <div class="lbl">In rotation</div><p>${L.compounds.map(c=>`<span class="pill" title="${E(c.kind)}">${c.id===sp.id?'<b>':''}${E(c.name)}${c.id===sp.id?'</b>':''}</span>`).join('')}</p>
      <div class="lbl">Entourage effect?</div><p class="small">${E(L.entourage.text)}</p>${cl(L.entourage.citations,2)}`}
  // ---- holistic / interactions
  if(!L)$('#hol-body').innerHTML=NA('Holistic');else $('#hol-body').innerHTML='<p class="small dim" style="margin-top:0">Cautions to raise with a doctor or pharmacist. Per-condition lifestyle pairings are inside each Scientist condition.</p>'+L.interactions.map(i=>`<div class="item"><b>${E(i.title)}</b><p class="small" style="margin:3px 0">${E(i.text)}</p>${cl(i.citations,2)}</div>`).join('');
  // ---- news & law
  if(!N){$('#news-body').innerHTML=NA('News feeds');}else{const have=new Set(Object.values(N.by_category).flat().map(i=>i.title));
    const hx=W?[...(W.news_us||[]),...(W.news_intl||[])].filter(i=>i.source==='Cannabis Health News (UK)'&&!have.has(i.title)).map(i=>({title:i.title,link:i.link,source:i.source,date:i.date,summary:(i.summary||'').slice(0,220)})):[];
    if(hx.length)N.by_category=Object.assign({},N.by_category,{'Health (UK)':hx});const cats=Object.keys(N.by_category);
    $('#news-meta').textContent=`${N.total} items · ${N.sources.filter(s=>s.status==='ok').length}/${N.sources.length} feeds ok · ${N.generated}`;
    const show=k=>{document.querySelectorAll('#news-tabs button').forEach(b=>b.setAttribute('aria-selected',b.dataset.k===k));
      const it=N.by_category[k]||[];$('#news-body').innerHTML=it.length?it.map(n=>`<div class="item"><a class="t" href="${E(n.link)}" target="_blank" rel="noopener">${E(n.title)}</a><div class="m">${E(n.source)} · ${E(n.date)}</div><div class="small dim">${E(n.summary)}</div></div>`).join(''):'<p class="mute">Nothing new in this category.</p>'};
    $('#news-tabs').innerHTML=cats.map(k=>`<button role="tab" data-k="${E(k)}">${E(k)} <span class="mono small">${N.by_category[k].length}</span></button>`).join('');
    $('#news-tabs').onclick=e=>{const b=e.target.closest('button');if(b)show(b.dataset.k)};show(cats[0]);}
  // ---- market
  if(!M||!M.rows)$('#mk-body').innerHTML=NA('Yahoo Finance');else{$('#mk-meta').textContent='Yahoo Finance · '+M.generated;
    $('#mk-body').innerHTML='<table><thead><tr><th>Ticker</th><th class="num">Price</th><th class="num">Day</th><th class="num">1 mo</th><th class="mk-hide">30 d</th></tr></thead><tbody>'+M.rows.map(r=>r.status!=='ok'?`<tr><td><b class="mono">${E(r.ticker)}</b></td><td colspan="4" class="na">unavailable</td></tr>`:`<tr><td><b class="mono">${E(r.ticker)}</b><div class="small mute">${E(r.name)}</div></td><td class="num mono">$${num(r.price,r.price<1?3:2)}</td><td class="num mono">${pct(r.chg_pct)}</td><td class="num mono">${pct(r.chg_1mo_pct)}</td><td class="mk-hide">${spark(r.spark)}</td></tr>`).join('')+'</tbody></table><p class="small mute">Close as of '+E((M.rows.find(r=>r.as_of)||{}).as_of||'')+' ET. Information only, not investment advice.</p>';}
  // ---- prices
  if(!P||!P.series)$('#pr-body').innerHTML=NA('Price feeds');else{$('#pr-meta').textContent=P.generated||'';
    $('#pr-body').innerHTML=P.series.map(s=>{if(s.status!=='ok'||!s.points||!s.points.length)return`<div class="item"><b>${E(s.label)}</b><p class="na" style="margin:4px 0 0">● Unavailable: ${E(s.note||'no source')}</p></div>`;
      const l=s.points[s.points.length-1],cur=s.region==='US'?'$':'C$',unit=s.region==='US'?'/lb':'/g';
      return`<div class="item"><div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start;flex-wrap:wrap"><div><b>${E(s.label)}</b> ${s.stale?`<span class="badge b-stale">STALE · ${s.age_days} d old</span>`:'<span class="badge b-ok">LIVE</span>'}<div class="big">${cur}${num(l.value,s.region==='US'?0:2)}<span class="small dim" style="font-family:var(--sans)"> ${unit}</span></div>
      <div class="small">${pct(l.chg_pct)} week · ${l.per_gram?'$'+num(l.per_gram)+'/g · ':''}week of <span class="mono">${E(l.date)}</span>${l.forward?` · fwd ${E(l.forward[0])} ${cur}${num(l.forward[1],0)}`:''}</div></div>${spark(s.points.map(p=>p.value),120,40)}</div>
      <p class="small mute" style="margin:6px 0 0">${s.stale?'Latest free public report is old, so treat as historical. ':''}Source: <a href="${E(l.link||s.url)}" target="_blank" rel="noopener">${E(s.source)}</a></p></div>`}).join('');}
  // ---- social
  if(!So||!So.posts)$('#so-body').innerHTML=NA('X');else{$('#so-meta').textContent='X posts read '+(So.generated||'').slice(0,10)+' · X News '+(So.news_generated||'');
    const tc=So.topic_counts||{};const post=p=>`<div class="post ${E(p.audience)}"><div class="m small mute"><a href="${E(p.url)}" target="_blank" rel="noopener">@${E(p.handle)}</a> · ${E(p.date)} · ${E(p.topic)}${p.views?` · ${Number(p.views).toLocaleString()} views`:''}</div>${E(p.text.length>220?p.text.slice(0,217)+'…':p.text)}</div>`;
    $('#so-body').innerHTML=`<p>${Object.entries(tc).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`<span class="pill">${E(k)} <b class="mono">${v}</b></span>`).join('')}</p>
      <div class="lbl">Health posts <span class="mute">· claims people make, not evidence</span></div>${So.posts.filter(p=>p.audience==='health').slice(0,4).map(post).join('')}
      <div class="lbl">Grower posts</div>${So.posts.filter(p=>p.audience==='grow').slice(0,3).map(post).join('')}
      <div class="lbl">Trending on X News</div>${(So.news||[]).map(n=>`<div class="item"><a class="t" href="${E(n.url)}" target="_blank" rel="noopener">${E(n.title)}</a><div class="small dim">${E(n.summary)}</div></div>`).join('')||'<p class="mute small">unavailable</p>'}`;}
  // ---- former Research Wire (PubMed newest 14 d + health feed): only items not shown elsewhere, folded into Study Grader and Grower Notes
  const pl=(a,why)=>a.map(p=>`<div class="item"><a class="t" href="${E(p.url)}" target="_blank" rel="noopener">${E(p.title)}</a><div class="m">${E(p.first_author)} · ${E(p.journal)} ${E(p.year)} ${p.preclinical?tag('PRECLINICAL'):''} <span class="mute">${E(why)}</span></div></div>`).join('');
  const nsIds=new Set(((d.newstudies||{}).papers||[]).map(p=>p.pmid));
  if(W&&!$('#ns-extra')){const med=W.papers_medical.filter(p=>!nsIds.has(p.pmid));if(med.length)$('#ns-foot').insertAdjacentHTML('afterend',`<details class="extra" id="ns-extra"><summary class="small"><b>${med.length} more new medical papers</b> <span class="mute">· PubMed newest 14 d, not matched to a tracked condition, so not graded · ${E(W.generated)}</span></summary><div class="list">${pl(med,'not graded')}</div></details>`)}
  // ---- grower
  if(!L)$('#gr-body').innerHTML=NA('Grower notes');else $('#gr-body').innerHTML=Object.values(L.factors).map(f=>`<div class="note" style="background:#fff">${f.anecdotal?tag('ANECDOTAL')+' ':''}<b>${E(f.name)}</b><p class="small" style="margin:4px 0">${E(f.finding)}</p>${f.citations&&f.citations.length?cl(f.citations,1):`<p class="small mute">${E(f.source||'No study; grower lore only.')}</p>`}</div>`).join('');
  if(W&&!$('#gr-papers')&&W.papers_cultivation.length)$('#gr-body').insertAdjacentHTML('afterend',`<div id="gr-papers"><div class="lbl">New cultivation papers · PubMed newest 14 d · ${W.papers_cultivation.length}</div><div class="list">${pl(W.papers_cultivation,'cultivation')}</div></div>`);
  // ---- feed + sources
  $('#feed').innerHTML=(d.feed||[]).map(f=>`<tr><td class="mono small" style="white-space:nowrap">${E(f.ts.slice(5,16))}</td><td><span class="badge" style="color:${col[f.agent]||'#475569'}">${E(f.agent.toUpperCase())}</span></td><td><b>${E(f.kind)}</b> ${E(f.what)}<div class="why">${E(f.reason)}</div></td></tr>`).join('');
  $('#src-meta').textContent=okN+'/'+srcs.length+' sources live';
  document.dispatchEvent(new CustomEvent('tg:rendered'));
  $('#sources').innerHTML=srcs.map(s=>`<span class="pill">${s.ok?'<span class="pos">●</span>':s.stale?'<span style="color:#8a5a00">●</span>':'<span class="neg">●</span>'} ${E(s.n)}${s.stale?' (stale)':s.none?' (unavailable)':''}</span>`).join('');
}
})();
