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

fetch('/terminal/data/terminal.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw r.status;return r.json()}).then(render).catch(e=>{
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
  // ---- agents
  const A=d.agents||{};const col={scientist:'#14532d',lab:'#5b3fa3',holistic:'#0e6b7a',wire:'#1f4f99',social:'#b4470f',grower:'#4d7c0f'};
  const ag=Object.keys(A).map(k=>({k,...A[k]}));
  ag.splice(4,0,{k:'news',name:'News & Law',status:N?`${N.total} items · ${N.sources.filter(s=>s.status==='ok').length}/${N.sources.length} feeds ok`:'unavailable',gen:N&&N.generated},
    {k:'market',name:'Market',status:M?`${M.rows.filter(r=>r.status==='ok').length}/${M.rows.length} tickers live (Yahoo Finance)`:'unavailable',gen:M&&M.generated},
    {k:'prices',name:'Prices',status:P?P.series.map(s=>s.region+': '+(s.status!=='ok'?'no source':s.stale?'stale':'ok')).join(' · '):'unavailable',gen:P&&P.generated});
  const acol={news:'#8a5a00',market:'#0f766e',prices:'#334155'};
  const anchor={scientist:'#scientist',lab:'#lab',holistic:'#holistic',wire:'#wire',social:'#social',grower:'#grower',news:'#news',market:'#market',prices:'#prices'};
  $('#agents').innerHTML='<h3><span>Agents</span><span>'+ag.length+' running</span></h3>'+ag.map(a=>{const bad=/unavailable/.test(a.status||'');
    return`<a class="agent" href="${anchor[a.k]||'#'}" style="--ac:${col[a.k]||acol[a.k]||'#64748b'}"><div class="t"><span class="nm">${E(a.name)}</span><span class="badge ${bad?'b-down':'b-ok'}">${bad?'DOWN':'LIVE'}</span></div><div class="st">${E(a.status||'')}</div><div class="age">${a.ts?ago(a.ts):E(a.gen||'')}</div></a>`}).join('')+
    '<div class="card legendcard" style="padding:12px 14px"><div class="lbl" style="margin-top:0">Evidence tags</div><div class="legend">'+['RCT','SR','GUIDELINE','REPORT','HUMAN-OBS','PRECLINICAL','HORT','CASE','REVIEW','ANECDOTAL'].map(tag).join('')+'</div><p class="small mute" style="margin:8px 0 0">RCT = randomized trial · SR = systematic review · PRECLINICAL = animal/cell only · ANECDOTAL = not evidence.</p></div>';
  // ---- scientist
  if(!S){$('#sci').innerHTML=NA('Scientist');}else{
    $('#sci-meta').textContent=`${conds.length} conditions · ${cites} citations · ${S.dropped_unverified||0} unverified dropped · ${S.generated}`;
    $('#strain-note').textContent=S.strain_note+' Method: '+S.method;
    const FB={};F.forEach(f=>FB[f.sci]=f);
    $('#sci').innerHTML=conds.map(c=>{const g=L&&L.grower&&L.grower[c.id],h=L&&L.holistic&&L.holistic[c.id],r=c.recent,f=FB[c.id];
      return`<details class="cond" id="cond-${E(c.id)}"><summary><span class="cn">${E(c.name)}</span><span>${ev(c.evidence)}</span><span class="tp">${E(c.top_pick)}</span><span class="tr">${E((c.terpenes||[]).join(', '))}</span><span class="num">${c.new_papers_30d??'—'}</span><span class="num">${(c.citations||[]).length}</span><span class="chev">▶</span></summary>
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
  $('#fgrid').innerHTML=F.length?F.map(f=>`<div class="fcard" id="finding-${E(f.slug)}"><a href="${E(f.path)}"><img src="${E(f.img)}" alt="${E(f.headline)}" loading="lazy" width="1600" height="900"></a><div class="fb"><div class="fc">${E(f.condition)}</div><a href="${E(f.path)}" style="color:inherit"><b>${E(f.headline)}</b></a><span class="badge grade g-${E(f.grade_cls)}">${E(f.grade)}</span><p>${E(f.summary[0])}</p>${f.strains?`<p class="st"><b>Typical strains:</b> ${E(f.strains)}</p>`:''}<p class="small">${f.studies.map(s=>`<a href="${pm(s.pmid)}" target="_blank" rel="noopener">PubMed ${E(s.pmid)}</a>`).join(' · ')}</p><div class="ft"><a class="small" href="${E(f.path)}">Read the finding →</a><a class="btn sm xbtn" href="${E(f.x_intent)}" target="_blank" rel="noopener">Share on X</a></div></div></div>`).join(''):NA('Findings');
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
  if(!N){$('#news-body').innerHTML=NA('News feeds');}else{const cats=Object.keys(N.by_category);
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
  // ---- wire
  if(!W)$('#wi-body').innerHTML=NA('PubMed');else{$('#wi-meta').textContent='PubMed newest 14 d · '+W.generated;
    const pl=(a)=>a&&a.length?a.map(p=>`<div class="item"><a class="t" href="${E(p.url)}" target="_blank" rel="noopener">${E(p.title)}</a><div class="m">${E(p.first_author)} · ${E(p.journal)} ${E(p.year)} ${p.preclinical?tag('PRECLINICAL'):''} ${(p.pubtypes||[]).filter(t=>/Trial|Review|Meta|Observational/.test(t)).map(t=>`<span class="mute">${E(t)}</span>`).join(' ')}</div></div>`).join(''):'<p class="mute small">No new papers in the window.</p>';
    $('#wi-body').innerHTML=`<div class="lbl" style="margin-top:0">Medical · ${W.papers_medical.length}</div><div class="scroll" style="max-height:300px">${pl(W.papers_medical)}</div><div class="lbl">Cultivation · ${W.papers_cultivation.length}</div><div class="scroll" style="max-height:240px">${pl(W.papers_cultivation)}</div>`;}
  // ---- grower
  if(!L)$('#gr-body').innerHTML=NA('Grower notes');else $('#gr-body').innerHTML=Object.values(L.factors).map(f=>`<div class="note" style="background:#fff">${f.anecdotal?tag('ANECDOTAL')+' ':''}<b>${E(f.name)}</b><p class="small" style="margin:4px 0">${E(f.finding)}</p>${f.citations&&f.citations.length?cl(f.citations,1):`<p class="small mute">${E(f.source||'No study; grower lore only.')}</p>`}</div>`).join('');
  // ---- feed + sources
  $('#feed').innerHTML=(d.feed||[]).map(f=>`<tr><td class="mono small" style="white-space:nowrap">${E(f.ts.slice(5,16))}</td><td><span class="badge" style="color:${col[f.agent]||'#475569'}">${E(f.agent.toUpperCase())}</span></td><td><b>${E(f.kind)}</b> ${E(f.what)}<div class="why">${E(f.reason)}</div></td></tr>`).join('');
  $('#src-meta').textContent=okN+'/'+srcs.length+' sources live';
  $('#sources').innerHTML=srcs.map(s=>`<span class="pill">${s.ok?'<span class="pos">●</span>':s.stale?'<span style="color:#8a5a00">●</span>':'<span class="neg">●</span>'} ${E(s.n)}${s.stale?' (stale)':s.none?' (unavailable)':''}</span>`).join('');
}
})();
