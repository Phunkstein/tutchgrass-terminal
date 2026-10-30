/* Deals agent tab (TEST): renders /terminal/data/deals.json into #deals.
   Free deals come only from each dispensary's own public page; every row links there. The Sponsored slot is a
   separate, clearly labeled EXAMPLE LAYOUT placeholder: it is never mixed into, or ranked above, the free list. */
(function(){
const $=s=>document.querySelector(s);
const E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function T(v){const m=String(v||'').match(/^(\d{4}-\d\d-\d\d)[ T](\d\d:\d\d)\s*([A-Z]{3})?$/);if(!m)return null;const z={EDT:'-04:00',EST:'-05:00',UTC:'Z'}[m[3]]||'-04:00';const t=Date.parse(m[1]+'T'+m[2]+z);return isNaN(t)?null:t/1000}
const clock=ts=>ts?new Date(ts*1000).toLocaleString('en-US',{timeZone:'America/Detroit',weekday:'short',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}):'unknown';
function render(D){const body=$('#dl-body');if(!body)return;
  if(!D||!D.deals){body.innerHTML='<p class="na">● Deal sources unavailable right now. No deals are shown rather than guesses.</p>';return}
  const ts=T(D.checked||D.generated),ok=D.sources.filter(s=>s.deals>0),bad=D.sources.filter(s=>!s.deals);
  $('#dl-meta').textContent=`${D.count} deals · ${ok.length}/${D.sources.length} dispensary pages read`;
  $('#dl-checked').innerHTML=`<b>Last checked:</b> <span class="mono">${E(clock(ts))}</span>`;
  $('#dl-note').innerHTML=`<b>21+ only.</b> ${E(D.disclaimer.replace(/^21\+ only\.\s*/,''))}`;
  const G={'All':D.deals};D.deals.forEach(d=>(G[d.chain]=G[d.chain]||[]).push(d));
  const cats=Object.keys(G);let lim=30;
  const row=d=>`<div class="item dl"><a class="t" href="${E(d.url)}" target="_blank" rel="noopener">${E(d.deal)}</a>
    <div class="m"><b>${E(d.store)}</b> · ${E(d.city)}, ${E(d.state)}${d.kind==='everyday'?' · <span class="tag dl-ev">EVERYDAY</span>':''}</div>
    <div class="small dim">${d.valid?`Valid: ${E(d.valid)}`:'Dates not stated on the page'} · collected ${E(d.collected)}${d.note?` · ${E(d.note)}`:''}</div></div>`;
  const show=(k,keep)=>{if(!keep)lim=30;document.querySelectorAll('#dl-tabs button').forEach(b=>b.setAttribute('aria-selected',b.dataset.k===k));const it=G[k]||[];
    $('#dl-list').innerHTML=it.slice(0,lim).map(row).join('')+(it.length>lim?`<p><button class="btn sm ghost" type="button" id="dl-more" data-k="${E(k)}">Show ${it.length-lim} more</button></p>`:'')};
  $('#dl-tabs').innerHTML=cats.map(k=>`<button role="tab" data-k="${E(k)}">${E(k)} <span class="mono small">${G[k].length}</span></button>`).join('');
  $('#dl-tabs').onclick=e=>{const b=e.target.closest('button');if(b)show(b.dataset.k)};
  $('#dl-list').onclick=e=>{const b=e.target.closest('#dl-more');if(b){lim+=40;show(b.dataset.k,true)}};show('All');
  const S=D.sponsored||{};
  $('#dl-sponsored').innerHTML=`<div class="dl-sph"><span class="dl-splbl">Sponsored</span><span class="dl-ex">${E(S.label||'EXAMPLE LAYOUT')}</span></div>
    <p class="small dim">${E(S.note||'')}</p>${(S.items||[]).length?'':`<div class="dl-skel" aria-hidden="true"><i></i><i></i><i class="s"></i></div><p class="small mute">No sponsored deals. This empty box only shows where a paid, labeled listing would sit.</p>`}`;
  $('#dl-foot').innerHTML=`Read from each dispensary's own public page (robots.txt checked first): ${ok.map(s=>`<a href="${E(s.url)}" target="_blank" rel="noopener">${E(s.name)}</a>`).join(' · ')}`+
    (bad.length?`<br>No deals this check: ${bad.map(s=>`${E(s.name)} (${E(s.status)})`).join(', ')}`:'')+
    (D.not_used&&D.not_used.length?`<br><span class="mute">Not used: ${D.not_used.map(n=>`${E(n.name)}: ${E(n.why)}`).join(' ')}</span>`:'');}
fetch('/terminal/data/deals.json',{cache:'no-cache'}).then(r=>r.ok?r.json():null).catch(()=>null).then(render);
})();
