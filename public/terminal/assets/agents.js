/* Cannabis Agent Terminal "agents are live" bar + agent header cards + All agents grid.
   Every status, time and count comes from the published data files (terminal.json, meta.json, breaking.json).
   Green = ran recently, amber = data is stale, grey = source unavailable. Nothing here is simulated. */
(function(){
const E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const H=3600,D=86400,now=()=>Date.now()/1000;
// "2026-10-29 22:05 EDT" | "2026-10-29T20:46" (box time, America/Detroit) | ISO with offset | epoch seconds
function T(v){if(v==null||v==='')return null;if(typeof v==='number')return v;let s=String(v).trim();
  const z={EDT:'-04:00',EST:'-05:00',UTC:'Z',GMT:'Z'};const m=s.match(/^(\d{4}-\d\d-\d\d)[ T](\d\d:\d\d(?::\d\d)?)\s*([A-Z]{3})?$/);
  if(m){const mo=+m[1].slice(5,7);const off=m[3]?z[m[3]]:(mo>3&&mo<11?'-04:00':'-05:00');if(off===undefined)return null;s=m[1]+'T'+m[2]+off}
  else if(/^\d{4}-\d\d-\d\d$/.test(s))s+='T12:00:00-04:00';else s=s.replace(/([+-]\d\d)(\d\d)$/,'$1:$2');
  const t=Date.parse(s);return isNaN(t)?null:t/1000}
const ago=ts=>{if(!ts)return'unknown';const m=Math.round((now()-ts)/60);return m<1?'just now':m<60?m+' min ago':m<2880?Math.round(m/60)+' h ago':Math.round(m/1440)+' days ago'};
const clock=ts=>ts?new Date(ts*1000).toLocaleString('en-US',{timeZone:'America/Detroit',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}):'';
const st=(ts,max,ok=true)=>!ok||!ts?'down':now()-ts>max?'stale':'ok';
const LBL={ok:'LIVE',stale:'STALE',down:'UNAVAILABLE',pend:'CHECKING'};
// registry: each agent has one distinct job and data source. secs = its sections on the home page (shown together as its tab).
const R=[
 {id:'scientist',nm:'Scientist',ic:'🔬',secs:['scientist','holistic'],page:/^\/terminal\/(my|findings)\//,job:'Matches each condition to cannabinoids and terpenes from verified PubMed citations; writes the findings, pairings and cautions.',
  f:(d)=>{const S=d.scientist;if(!S)return null;const n=S.conditions.length,c=S.conditions.reduce((a,x)=>a+(x.citations||[]).length,0);const ts=T(S.generated),F=d.findings||[],L=d.lab;
   return{ts,state:st(ts,26*H),doing:`Matched ${n} conditions to ${c} citations`,src:'PubMed E-utilities + National Academies 2017',log:[`Checked ${n} conditions against ${S.pubmed_records_cached||0} cached PubMed records`,`${c} citations kept · ${(S.dropped_unverified||[]).length} unverified dropped`,`${F.length} plain-words findings published${F[0]?' · newest '+F.map(f=>f.date).sort().pop():''}`,L?`${L.interactions.length} interaction cautions · lifestyle pairings for ${Object.keys(L.holistic||{}).length} conditions`:'Pairings unavailable']}}},
 {id:'grader',nm:'Study Grader',ic:'🧪',secs:['newstudies','scoreboard'],job:'AI-grades every new cannabis paper on PubMed and ranks conditions in the evidence scoreboard.',
  f:(d)=>{const n=d.newstudies;if(!n)return null;const ts=T(n.generated),wk=n.papers.filter(p=>(p.date||'')>=n.week_start).length;const g={};n.papers.forEach(p=>g[p.grade]=(g[p.grade]||0)+1);const r=d.scoreboard||[];
   return{ts,state:st(ts,26*H),doing:`AI-graded ${n.papers.length} new papers`,src:(n.source||'PubMed')+' + National Academies 2017',log:[`Window ${n.window.start} to ${n.window.end}: ${n.papers.length} papers, ${wk} since ${n.week_start}`,`Human trials/meta-analyses ${(g.rct||0)+(g.meta||0)+(g.noplacebo||0)} · observational ${g.obs||0} · mice/cells ${(g.mice||0)+(g.cells||0)}`,r.length?`Scoreboard: ${r.length} conditions ranked, #1 ${r[0].label}`:'Scoreboard unavailable']}}},
 {id:'policy',nm:'Policy Watch',ic:'⚖️',secs:['dec11','laws','ag-policy'],job:'Counts down to the Dec 11, 2026 federal hemp THC rule and flags state and federal cannabis laws that just took effect or take effect soon, each linked to its official source.',
  f:(d)=>{const x=d.dec11,L=d.laws;if(!x&&!L)return null;const ts=d.built_ts,days=x?Math.max(0,Math.floor((T(x.deadline)-now())/D)):null,c=L&&L.counts;
   const doing=c&&c.alerts?`${c.alerts} law${c.alerts===1?'':'s'} just took effect`:c?`${c.in_effect} laws now in effect, ${c.upcoming} coming soon`:`${days} days to the Dec 11 hemp rule`;
   const log=[];if(c){log.push(`${c.in_effect} in effect (last ${L.window.past_days} days), ${c.upcoming} taking effect in the next ${L.window.ahead_days} days`);
     log.push(`Federal Register: ${L.fr_status==='ok'||!L.fr_status?c.federal_register+' cannabis rules in the window':'unavailable, kept last good'}`);
     if(c.leads)log.push(`${c.leads} news lead${c.leads===1?'':'s'} on new laws, not shown until an official source confirms`)}
   if(x)log.push(`${days} days to the Dec 11 hemp rule: ${x.headline}`);
   return{ts,state:st(ts,26*H),doing,src:'Official statute, regulator and legislature pages · Federal Register · CRS',log}}},
 {id:'news',nm:'News Desk',ic:'📰',secs:['news'],job:'Reads cannabis news and law RSS feeds and sorts them US federal / states / international / health.',
  f:(d,x)=>{const N=d.news;if(!N)return null;const ok=N.sources.filter(s=>s.status==='ok').length,ts=T(N.generated),b=x.breaking;
   const nb=b&&b.items?b.items.filter(i=>now()-i.first_seen_ts<6*H).length:0;
   return{ts,state:st(ts,26*H,ok>0),doing:nb?`${nb} new stories in 6 h`:`Sorted ${N.total} stories`,src:`${ok}/${N.sources.length} RSS feeds ok + Cannabis Health News (UK)`,
    log:[`${N.total} stories from ${ok}/${N.sources.length} feeds`,Object.entries(N.by_category).map(([k,v])=>k+' '+v.length).join(' · ')+' shown',...(b&&b.items?b.items.slice(0,2).map(i=>`New ${clock(i.first_seen_ts)}: ${i.title.slice(0,80)}`):[])]}}},
 {id:'recalls',nm:'Recall & Safety',ic:'🚨',secs:['recalls'],job:'Collects official cannabis product recalls, health & safety advisories and failed-lab-test notices from state regulators and the FDA, each linked to the official notice.',
  // its own standard: runs hourly with a heartbeat commit at most every 6 h, so live = re-checked within 8 h and at least one official source answered
  f:(d)=>{const C=d.recalls;if(!C||!C.items)return null;const ts=T(C.generated),ok=(C.sources||[]).filter(s=>s.status==='ok'),bad=(C.sources||[]).filter(s=>s.status!=='ok'),n=C.items[0];
   return{ts,state:st(ts,8*H,ok.length>0),doing:`${C.count} official notices`,src:`${ok.length}/${(C.sources||[]).length} official sources ok: ${ok.map(s=>s.source).join(', ')}`,
    log:[n?`Newest: ${n.date} ${n.state} · ${(n.brand||n.product).slice(0,60)}`:'No notices',`${C.count} notices from ${ok.length} regulators/FDA lists, newest first, de-duplicated`,bad.length?`Unavailable now: ${bad.map(s=>s.source+' ('+(s.error||'error')+')').join(', ')}`:'Every source answered on the last check']}}},
 {id:'market',nm:'Market Watcher',ic:'📈',secs:['market','prices'],job:'Tracks cannabis stocks (Yahoo Finance), US wholesale flower prices (Cannabis Benchmarks, weekly) and Canadian retail cannabis prices (Statistics Canada CPI, monthly).',
  f:(d)=>{const M=d.market,P=d.prices;if(!M&&!P)return null;const ok=M&&M.rows?M.rows.filter(r=>r.status==='ok'):[],
   // each price series is judged by its own publishing cadence: age of its latest point vs max_age_days (fallback: the old 45-day rule)
   sa=s=>{const t=T(s.latest_date||(s.points&&s.points.length?s.points[s.points.length-1].date:null));return t?Math.round((now()-t)/D):s.age_days},
   sStale=s=>s.status==='ok'&&(sa(s)!=null?sa(s)>(s.max_age_days||45):!!s.stale),
   ps=P&&P.series?P.series.filter(s=>s.status==='ok'):[],cur=ps.filter(s=>!sStale(s)),hist=P&&P.series?P.series.filter(s=>s.status==='discontinued'):[];
   const ts=Math.max(T(M&&M.generated)||0,T(P&&P.generated)||0)||null,anyStale=ps.some(sStale)||!M||!ok.length;
   return{ts,state:!ok.length&&!cur.length?'down':anyStale?'stale':st(ts,26*H),doing:`${ok.length} stocks · ${cur.length}/${ps.length} prices`,src:'Yahoo Finance chart API · Cannabis Benchmarks public summaries · Statistics Canada CPI',
    log:[`${ok.length} of ${M&&M.rows?M.rows.length:0} tickers fetched${ok[0]&&ok[0].as_of?' · as of '+ok[0].as_of:''}`,...(P&&P.series?P.series.filter(s=>s.status!=='no source yet').map(s=>{const a=sa(s),c=s.cadence||'weekly';
     return `${s.label}: ${s.status==='discontinued'?`no longer published, last ${c} report ${s.latest_date} (history only)`:s.status!=='ok'?(s.status||'unavailable'):sStale(s)?`overdue: latest ${c} report ${s.latest_date}, ${a} days old`:`current: latest ${c} report ${s.latest_date} (${a} d old)`}`}):['Prices unavailable'])]}}},
 {id:'lab',nm:'Terpene Lab',ic:'🌿',secs:['lab'],job:'Spotlights one cannabinoid or terpene a day: what it is, health angle, how to grow and keep it.',
  f:(d)=>{const L=d.lab;if(!L)return null;const sp=L.compounds.find(c=>c.id===L.spotlight_id)||L.compounds[0],ts=T(L.generated);
   return{ts,state:st(ts,26*H),doing:`Spotlight: ${sp.name.split(' (')[0]}`,src:'PubMed-cited compound notes',log:[`Today's spotlight: ${sp.name}`,`${L.compounds.length} compounds in rotation (${L.spotlight_rule})`,`Entourage effect: ${L.entourage.citations.length} citations`]}}},
 {id:'trends',nm:'Trend Spotter',ic:'💬',secs:['social'],job:'Reads what people say about cannabis for health and growing on public social media (Bluesky, Reddit; X when connected). Read-only; it never posts.',
  f:(d)=>{const S=d.social;if(!S||!S.posts)return null;const ts=T(S.generated),tn=T(S.news_generated),fr=S.mode==='free',pl=fr?(S.platforms||['Bluesky']).join(' + '):'X';
   return{ts,state:st(ts,fr?3*H:26*H),doing:`Read ${S.posts.length} posts`,src:fr?`${pl} public search (read-only)`:'X API (read-only)',log:[`${S.posts.length} posts kept from ${S.queries} searches on ${pl}`,fr?`${(S.threads||[]).length} top Reddit threads today`:`${(S.news||[]).length} X News stories${tn?' · read '+clock(tn):''}`,`Top topic: ${(Object.entries(S.topic_counts||{}).sort((a,b)=>b[1]-a[1])[0]||['none'])[0]}`]}}},
 {id:'grower',nm:'Grower Notes',ic:'🌱',secs:['grower'],job:'What changes cannabis chemistry when growing: genetics, light, harvest, drying, storage, plus new cultivation papers.',
  f:(d)=>{const L=d.lab,W=d.wire;if(!L)return null;const ts=T(L.generated),fs=Object.values(L.factors),an=fs.filter(x=>x.anecdotal).length;
   return{ts,state:st(ts,26*H),doing:`${fs.length-an} studied factors`,src:'Horticulture studies (PubMed)',log:[`${fs.length-an} factors backed by studies`,`${an} grower practice flagged anecdotal`,W?`${W.papers_cultivation.length} new cultivation papers (PubMed, 14 d)`:'New cultivation papers unavailable']}}},
 {id:'brands',nm:'Brand Auditor',ic:'🏷️',href:'/terminal/report-cards/',page:/^\/terminal\/report-cards\//,job:"Scores hemp brands' label claims against their own published lab reports (COAs).",
  f:(d,x)=>{const m=x.meta;if(!m)return null;const ts=T(m.checked||m.generated),ck=m.checked!=null;
   return{ts,state:st(ts,ck?50*H:8*D),doing:ck?`Checked ${m.coas_checked} lab reports`:`Audited ${m.coa_count} lab reports`,src:"Brands' own published COAs",log:[`${m.coa_count} COAs read from ${m.brand_count} brands · ${m.scored} scored against the label`,ck?`Daily check: ${m.links_ok} COA links up, ${m.links_removed} removed, ${m.links_unreachable} unreachable`:`${m.dec11_over} products over the Dec 11 THC limit`,ck?`${Number(m.queued_coas).toLocaleString()} more COAs on brand lab pages, not yet scored (${m.new_coas_today} new today)`:`${m.dec11_over} products over the Dec 11 THC limit`]}}}];
R.forEach(a=>{a.href=a.href||'/terminal/#'+a.secs[0]});
function feed(d,a,n){return(d.feed||[]).filter(f=>f.agent===a).slice(0,n).map(f=>`${f.kind}: ${f.what}`)}
const nav=document.querySelector('.top .nav');if(!nav)return;
const path=location.pathname.replace(/index\.html$/,''),HOME=path==='/terminal/';
const byId={};R.forEach(a=>byId[a.id]=a);
const pageAgent=(R.find(a=>a.page&&a.page.test(path))||{}).id;
const pill=s=>`<span class="apill s-${s}"><i></i>${LBL[s]}</span>`;
function chip(a,s){return`<a class="ag" data-ag="${a.id}" href="${a.href}"><span class="av" aria-hidden="true">${a.ic}</span><span class="tx"><span class="nm">${E(a.nm)}<i class="dot s-${s.state}" title="${LBL[s.state]}"></i></span><small class="doing">${E(s.doing)}</small></span></a>`}
function count(n){return`<b>${n}</b> ${n===1?'agent is':'agents are'} live`}
function build(d,x){
  const S={};R.forEach(a=>{let r=null;try{r=d?a.f(d,x):null}catch(e){r=null}S[a.id]=r||{state:'down',ts:null,doing:'Source unavailable',src:'unavailable',log:['Source unavailable right now. No numbers are shown rather than guesses.']}});
  const N=R.filter(a=>S[a.id].state==='ok').length;
  nav.classList.add('agnav');
  nav.innerHTML=`<div class="ascroll">`+
    `<a class="ag all" data-ag="all" href="/terminal/"><span class="av" aria-hidden="true">◎</span><span class="tx"><span class="nm">All agents</span><small class="doing">${R.length} on the team</small></span></a>`+
    R.map(a=>chip(a,S[a.id])).join('')+`</div>`;
  document.querySelectorAll('[data-agcount]').forEach(el=>el.innerHTML=count(N));
  document.querySelectorAll('[data-agtotal]').forEach(el=>el.textContent=R.length);
  const card=a=>{const s=S[a.id];return`<div class="ahead s-${s.state}" id="ah-${a.id}"><div class="scan" aria-hidden="true"></div><div class="ahh"><span class="av lg" aria-hidden="true">${a.ic}</span><div class="ahm"><div class="ahn"><b>${E(a.nm)}</b>${pill(s.state)}</div><div class="ahj">${E(a.job)}</div></div><div class="ahr"><span class="mono">Last run: <span data-ts="${s.ts||''}">${ago(s.ts)}</span></span><small>${E(clock(s.ts))}</small></div></div>
    <ul class="alog">${s.log.map(l=>`<li><span class="mono">›</span> ${E(l)}</li>`).join('')}</ul><div class="asrc">Source: ${E(s.src)}${s.state==='stale'?' · <b>stale</b>: shown as historical':''}${s.state==='down'?' · unavailable':''}</div></div>`};
  // header cards: home sections, or the agent's own page
  if(HOME){R.forEach(a=>{if(!a.secs||document.getElementById('ah-'+a.id))return;
      if(a.id==='policy'){const dd=document.getElementById('dec11');if(!dd)return;const w=document.createElement('div');w.id='ag-policy';w.className='agwrap';w.innerHTML=card(a);dd.before(w)}
      else{const el=document.getElementById(a.secs[0]);if(el)el.insertAdjacentHTML('afterbegin',card(a))}});
    const g=document.getElementById('agrid');if(g)g.innerHTML=R.map(a=>{const s=S[a.id];return`<a class="acard s-${s.state}" href="${a.href}" data-ag="${a.id}"><div class="ach"><span class="av" aria-hidden="true">${a.ic}</span><b>${E(a.nm)}</b><i class="dot s-${s.state}"></i></div><div class="acd">${E(s.doing)}</div><div class="acl"><span>${LBL[s.state]}</span><span data-ts="${s.ts||''}">${ago(s.ts)}</span></div></a>`}).join('');
    const gm=document.getElementById('agrid-meta');if(gm)gm.textContent=`${N} live · ${R.filter(a=>S[a.id].state==='stale').length} stale · ${R.filter(a=>S[a.id].state==='down').length} unavailable · from the published data files`;
  }else if(pageAgent){const m=document.querySelector('main.wrap,main');if(m&&!document.getElementById('ah-'+pageAgent)){const h=m.querySelector('h1');(h||m.firstChild)&&(h?h.insertAdjacentHTML('afterend',card(byId[pageAgent])):m.insertAdjacentHTML('afterbegin',card(byId[pageAgent])))}}
  setup();
}
// exactly one aria-current. Home = true tabs: only the selected agent's sections are shown; scrolling never changes the tab.
let cur;const sc=()=>nav.querySelector('.ascroll');
// center the selected tab in the scrolling bar (clamped at the ends); smooth on tap, instant on load / deep link
function center(a,smooth){const s=sc();if(!s||s.scrollWidth<=s.clientWidth+1)return;const r=a.getBoundingClientRect(),n=s.getBoundingClientRect();
  const max=s.scrollWidth-s.clientWidth,left=Math.max(0,Math.min(max,s.scrollLeft+(r.left-n.left)-(n.width-r.width)/2));
  s.scrollTo({left,behavior:smooth&&!matchMedia('(prefers-reduced-motion: reduce)').matches?'smooth':'auto'});if(!smooth)edge(s)}
function set(id,smooth){cur=id;nav.querySelectorAll('[aria-current]').forEach(x=>x.removeAttribute('aria-current'));const a=id&&nav.querySelector(`[data-ag="${id}"]`);if(!a)return;
  a.setAttribute('aria-current','page');center(a,smooth)}
const edge=s=>s.classList.toggle('atend',s.scrollLeft>=s.scrollWidth-s.clientWidth-2);
document.addEventListener('scroll',e=>{const t=e.target;if(t&&t.classList&&t.classList.contains('ascroll'))edge(t)},true);
addEventListener('resize',()=>{const a=nav.querySelector('[aria-current]');if(a)center(a,false)});
const OV=['.hero','#all','.mcband','#thisweek','.content>.cta','#log'];   // overview-only blocks
function tagHome(){OV.forEach(q=>document.querySelectorAll(q).forEach(el=>el.dataset.view='all'));
  R.forEach(a=>(a.secs||[]).forEach(id=>{const el=document.getElementById(id);if(el)el.dataset.agent=a.id}));document.body.classList.add('agtabs')}
function agentOf(id){if(!id||id==='all')return null;const el=document.getElementById(id);if(!el)return R.find(a=>a.id===id)?id:null;
  const h=el.closest('[data-agent]');return h?h.dataset.agent:null}
let lastTab;
function route(force,smooth){if(!HOME)return;const id=decodeURIComponent(location.hash.slice(1)),ag=agentOf(id)||(R.find(a=>a.id===id)||{}).id||null,tab=ag||'all';
  document.querySelectorAll('[data-view="all"]').forEach(el=>el.hidden=tab!=='all');
  document.querySelectorAll('[data-agent]').forEach(el=>el.hidden=el.dataset.agent!==tab);
  document.body.dataset.tab=tab;set(tab,smooth===true);
  const a=ag&&R.find(x=>x.id===ag),target=id&&document.getElementById(id);
  // tab switch scrolls to the top; a deep link to something inside a tab (a condition, a paper) scrolls to that item
  if(target&&a&&id!==a.secs[0])setTimeout(()=>target.scrollIntoView({block:'start'}),30);else if(force===true||tab!==lastTab)scrollTo(0,0);
  lastTab=tab;document.dispatchEvent(new CustomEvent('tg:tab',{detail:tab}))}
let built;function setup(){if(!HOME){set(pageAgent||null);return}tagHome();route(!built&&!(location.hash&&agentOf(location.hash.slice(1))&&location.hash.slice(1)!==(R.find(a=>a.id===agentOf(location.hash.slice(1)))||{secs:[]}).secs[0]));built=1}
if(HOME){
  // in-page links (#…, /terminal/#…) switch tabs through history so Back/Forward work
  document.addEventListener('click',e=>{const a=e.target.closest('a[href]');if(!a||e.defaultPrevented||e.metaKey||e.ctrlKey||e.shiftKey||a.target==='_blank')return;
    const u=new URL(a.getAttribute('href'),location.href);if(u.origin!==location.origin||u.pathname.replace(/index\.html$/,'')!=='/terminal/')return;
    e.preventDefault();const h=u.hash||'#all';if(h!==location.hash)history.pushState(null,'',h);route(true,true)});
  addEventListener('popstate',route);addEventListener('hashchange',route)}
if(HOME){if('scrollRestoration' in history)history.scrollRestoration='manual';tagHome();route(true)}
const J=u=>fetch(u,{cache:'no-cache'}).then(r=>r.ok?r.json():null).catch(()=>null);
Promise.all([J('/terminal/data/terminal.json'),J('/terminal/data/meta.json'),J('/terminal/data/breaking.json')]).then(([d,meta,breaking])=>{build(d,{meta,breaking});
  // home sections are filled by terminal.js; re-add a card if a section re-rendered over it
  if(HOME)document.addEventListener('tg:rendered',()=>{if(R.some(a=>a.secs&&document.getElementById(a.secs[0])&&!document.getElementById('ah-'+a.id)))build(d,{meta,breaking})});
  setInterval(()=>document.querySelectorAll('[data-ts]').forEach(el=>{const t=+el.dataset.ts;if(t)el.textContent=ago(t)}),60000)});
})();
