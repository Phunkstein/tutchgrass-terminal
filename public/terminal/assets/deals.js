/* Deals agent tab (TEST): renders /terminal/data/deals.json into #deals.
   Multi-state: every deal carries its state; filters go State → City → Chain (city first, so people can find deals near them).
   Free deals come only from each dispensary's own public page; every row links there. The Sponsored slot is a
   separate, clearly labeled EXAMPLE LAYOUT placeholder: it is never mixed into, or ranked above, the free list. */
(function(){
const $=s=>document.querySelector(s);
const E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function T(v){const m=String(v||'').match(/^(\d{4}-\d\d-\d\d)[ T](\d\d:\d\d)\s*([A-Z]{3})?$/);if(!m)return null;const z={EDT:'-04:00',EST:'-05:00',UTC:'Z'}[m[3]]||'-04:00';const t=Date.parse(m[1]+'T'+m[2]+z);return isNaN(t)?null:t/1000}
const clock=ts=>ts?new Date(ts*1000).toLocaleString('en-US',{timeZone:'America/Detroit',weekday:'short',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}):'unknown';
const KEY='tg-deals-filter';
const load=()=>{try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return{}}};
const save=f=>{try{localStorage.setItem(KEY,JSON.stringify(f))}catch(e){}};
function render(D){const list=$('#dl-list');if(!list)return;
  if(!D||!D.deals){$('#dl-body').innerHTML='<p class="na">● Deal sources unavailable right now. No deals are shown rather than guesses.</p>';$('#dl-filters').hidden=true;return}
  const ts=T(D.checked||D.generated),src=D.sources||[],ok=src.filter(s=>s.deals>0),bad=src.filter(s=>!s.deals);
  const NM={};(D.states||[]).forEach(s=>NM[s.code]=s.name);
  const cities=d=>(d.cities&&d.cities.length)?d.cities:[];
  $('#dl-meta').textContent=`${ok.length}/${src.length} dispensary pages read`;
  const sel={st:$('#dl-state'),ci:$('#dl-city'),ch:$('#dl-chain')};
  let F=Object.assign({st:'',ci:'',ch:''},load()),lim=30;
  const opt=(v,t,n,dis)=>`<option value="${E(v)}"${dis?' disabled':''}>${E(t)}${n!=null?` (${n})`:''}</option>`;
  // state options: states with deals first (by count), then every other legal state with 0 so far
  const sc={};D.deals.forEach(d=>sc[d.state]=(sc[d.state]||0)+1);
  const withD=(D.states||[]).filter(s=>sc[s.code]).sort((a,b)=>a.name.localeCompare(b.name)),zero=(D.states||[]).filter(s=>!sc[s.code]);
  sel.st.innerHTML=opt('','All states',null)+withD.map(s=>opt(s.code,s.name,sc[s.code])).join('')+
    (zero.length?`<optgroup label="No deals found yet">${zero.map(s=>opt(s.code,s.name,0,true)).join('')}</optgroup>`:'');
  if(F.st&&!sc[F.st])F={st:'',ci:'',ch:''};
  const inState=()=>D.deals.filter(d=>!F.st||d.state===F.st);
  const ckey=(c,st)=>F.st?c:`${c}, ${st}`;
  function fillCity(){const C={};let multi=0;inState().forEach(d=>{const cs=cities(d);if(!cs.length)multi++;cs.forEach(c=>{const k=ckey(c,d.state);C[k]=(C[k]||0)+1})});
    const ks=Object.keys(C).sort((a,b)=>a.localeCompare(b));if(F.ci&&F.ci!=='*'&&!C[F.ci])F.ci='';
    sel.ci.innerHTML=opt('','All cities',null)+ks.map(k=>opt(k,k,C[k])).join('')+(multi?opt('*','Statewide / multiple stores',multi):'');sel.ci.value=F.ci}
  const inCity=()=>inState().filter(d=>{if(!F.ci)return true;const cs=cities(d);if(F.ci==='*')return!cs.length;
      // a chain-wide deal (no single city) also applies near you, so it is listed after the city's own stores
      const st=F.st||F.ci.split(', ').pop();return cs.some(c=>ckey(c,d.state)===F.ci)||(!cs.length&&d.state===st)});
  function fillChain(){const C={};inCity().forEach(d=>C[d.chain]=(C[d.chain]||0)+1);const ks=Object.keys(C).sort((a,b)=>a.localeCompare(b));if(F.ch&&!C[F.ch])F.ch='';
    sel.ch.innerHTML=opt('','All chains',null)+ks.map(k=>opt(k,k,C[k])).join('');sel.ch.value=F.ch}
  const row=d=>{const loc=cities(d).length?d.city:(d.city||'multiple stores');
    return`<div class="item dl"><a class="t" href="${E(d.url)}" target="_blank" rel="noopener">${E(d.deal)}</a>
    <div class="m"><b>${E(d.store)}</b> · ${E(loc)}, ${E(d.state)}${d.kind==='everyday'?' · <span class="tag dl-ev">EVERYDAY</span>':''}</div>
    <div class="small dim">${d.valid?`Valid: ${E(d.valid)}`:'Dates not stated on the page'} · collected ${E(d.collected)}${d.note?` · ${E(d.note)}`:''}</div></div>`};
  function show(){let it=inCity().filter(d=>!F.ch||d.chain===F.ch);
    if(F.ci&&F.ci!=='*')it=it.filter(d=>cities(d).length).concat(it.filter(d=>!cities(d).length));
    const where=[F.ci==='*'?'statewide / multiple stores':F.ci,F.st&&!(F.ci&&F.ci!=='*'&&F.ci.includes(', '))?NM[F.st]:'',F.ch].filter(Boolean).join(' · ');
    $('#dl-count').textContent=`${it.length} deal${it.length===1?'':'s'}${where?' · '+where:' · all states'}`;
    list.innerHTML=it.length?it.slice(0,lim).map(row).join('')+(it.length>lim?`<p><button class="btn sm ghost" type="button" id="dl-more">Show ${it.length-lim} more</button></p>`:''):
      '<p class="na">No current deals found for this filter yet.</p>'}
  function all(){fillCity();fillChain();show();save(F)}
  sel.st.value=F.st;all();
  sel.st.onchange=()=>{F={st:sel.st.value,ci:'',ch:''};lim=30;all()};
  sel.ci.onchange=()=>{F.ci=sel.ci.value;F.ch='';lim=30;fillChain();show();save(F)};
  sel.ch.onchange=()=>{F.ch=sel.ch.value;lim=30;show();save(F)};
  list.onclick=e=>{if(e.target.closest('#dl-more')){lim+=40;show()}};
  const S=D.sponsored||{};
  $('#dl-sponsored').innerHTML=`<div class="dl-sph"><span class="dl-splbl">Sponsored</span><span class="dl-ex">${E(S.label||'EXAMPLE LAYOUT')}</span></div>
    <p class="small dim">${E(S.note||'')}</p>${(S.items||[]).length?'':`<div class="dl-skel" aria-hidden="true"><i></i><i></i><i class="s"></i></div><p class="small mute">No sponsored deals. This empty box only shows where a paid, labeled listing would sit.</p>`}`;
  // footer: disclaimer, method, per-state counts, sources
  const byS=(D.states||[]).map(s=>`${E(s.code)} ${sc[s.code]||0}`).join(' · ');
  const grp={};ok.forEach(s=>(grp[s.state]=grp[s.state]||[]).push(s));
  $('#dl-foot').innerHTML=`<p><b>21+ only.</b> ${E((D.disclaimer||'').replace(/^21\+ only\.\s*/,''))}</p>
    <p><b>How this works.</b> Last checked ${E(clock(ts))}. A test agent reads each dispensary's own free public deals page (robots.txt checked first; no logins, no menu platforms or aggregators), keeps each deal in the store's own words, and drops anything expired, dated in the future or not clearly current. At most ${E(D.per_store||10)} deals per store. ${E(D.state_note||'')}</p>
    <p><b>Deals by state</b> (every state with legal dispensaries, including 0 so far): ${byS}</p>
    <details><summary>Sources read this check (${ok.length})</summary><p>${Object.keys(grp).sort().map(k=>`<b>${E(k)}</b> ${grp[k].map(s=>`<a href="${E(s.url)}" target="_blank" rel="noopener">${E(s.name)}</a>`).join(', ')}`).join(' · ')}</p></details>
    ${bad.length?`<details><summary>No deals this check (${bad.length})</summary><p>${bad.map(s=>`${E(s.state)} ${E(s.name)}: ${E(s.status)}`).join('<br>')}</p></details>`:''}
    ${D.not_used&&D.not_used.length?`<details><summary>Not used (${D.not_used.length})</summary><p>${D.not_used.map(n=>`<b>${E(n.name)}</b>: ${E(n.why)}`).join('<br>')}</p></details>`:''}`;
}
fetch('/terminal/data/deals.json',{cache:'no-cache'}).then(r=>r.ok?r.json():null).catch(()=>null).then(render);
})();
