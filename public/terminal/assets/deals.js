/* Deals agent tab (TEST): renders /terminal/data/deals.json into #deals, nearest first.
   Location is the main way in: "Near me" (browser location, asked only when the button is clicked), or a ZIP / city
   typed into the box. ZIPs and cities are looked up IN THE BROWSER from bundled Census tables (data/geo/zip.csv,
   place.csv), loaded only once a location is used; distances are worked out here too. No location is ever sent
   anywhere: the last one chosen is kept in this browser's localStorage only. Without a location the tab shows a
   prompt plus State → City → Chain filters instead of the whole national list.
   Free deals come only from each dispensary's own public page; every row links there. The Sponsored slot is a
   separate, clearly labeled EXAMPLE LAYOUT placeholder: it is never mixed into, or ranked above, the free list. */
(function(){
const $=s=>document.querySelector(s);
const E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function T(v){const m=String(v||'').match(/^(\d{4}-\d\d-\d\d)[ T](\d\d:\d\d)\s*([A-Z]{3})?$/);if(!m)return null;const z={EDT:'-04:00',EST:'-05:00',UTC:'Z'}[m[3]]||'-04:00';const t=Date.parse(m[1]+'T'+m[2]+z);return isNaN(t)?null:t/1000}
const clock=ts=>ts?new Date(ts*1000).toLocaleString('en-US',{timeZone:'America/Detroit',weekday:'short',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}):'unknown';
const KEY='tg-deals-filter',LKEY='tg-deals-loc',RADII=[5,10,25,50];
const ld=k=>{try{return JSON.parse(localStorage.getItem(k)||'null')}catch(e){return null}};
const sv=(k,v)=>{try{v==null?localStorage.removeItem(k):localStorage.setItem(k,JSON.stringify(v))}catch(e){}};
const R=Math.PI/180,mi=(a,b,c,d)=>{const x=Math.sin((c-a)*R/2)**2+Math.cos(a*R)*Math.cos(c*R)*Math.sin((d-b)*R/2)**2;return 7917.5*Math.asin(Math.sqrt(x))};
const fmt=m=>m<10?m.toFixed(1):String(Math.round(m));
// ---- bundled Census lookup tables (lazy) ----
let ZIP=null,PL=null;
const getTxt=u=>fetch(u).then(r=>r.ok?r.text():Promise.reject(r.status));
function zips(){return ZIP||(ZIP=getTxt('/terminal/data/geo/zip.csv').then(t=>{const m=new Map();t.split('\n').forEach(l=>{if(!l)return;const p=l.split(',');m.set(p[0],[p[1]/100,p[2]/100])});return m}))}
function places(){return PL||(PL=getTxt('/terminal/data/geo/place.csv').then(t=>t.split('\n').filter(Boolean).map(l=>{const p=l.split('|');return{n:p[0],k:p[0].toLowerCase(),st:p[1],lat:p[2]/100,lon:p[3]/100}})))}
function nearestPlace(P,lat,lon){let b=null,bd=1e9;for(const p of P){const d=Math.abs(p.lat-lat)+Math.abs(p.lon-lon)*Math.cos(lat*R);if(d<bd){bd=d;b=p}}return b}

function render(D){const list=$('#dl-list');if(!list)return;
  if(!D||!D.deals){$('#dl-body').innerHTML='<p class="na">● Deal sources unavailable right now. No deals are shown rather than guesses.</p>';$('#dl-loc').hidden=true;$('#dl-filters').hidden=true;return}
  const ts=T(D.checked||D.generated),src=D.sources||[],ok=src.filter(s=>s.deals>0),bad=src.filter(s=>!s.deals);
  const NM={},CODE={};(D.states||[]).forEach(s=>{NM[s.code]=s.name;CODE[s.name.toLowerCase()]=s.code});
  const LOC=D.locations||[],cities=d=>(d.cities&&d.cities.length)?d.cities:[];
  $('#dl-meta').textContent=`${D.count||D.deals.length} deals · ${ok.length}/${src.length} dispensary pages read`;
  // store-data cities (checked before the national places table, so "Ann Arbor" finds the one with deals)
  const SC={};LOC.forEach(l=>{const k=(l.city+'|'+l.state).toLowerCase();(SC[k]=SC[k]||{n:l.city,st:l.state,a:[],o:[]}).a.push(l.lat);SC[k].o.push(l.lon)});
  const el={st:$('#dl-state'),ci:$('#dl-city'),ch:$('#dl-chain'),q:$('#dl-q'),kw:$('#dl-kw'),msg:$('#dl-locmsg'),cur:$('#dl-cur'),rad:$('#dl-rad'),fl:$('#dl-filters'),pr:$('#dl-prompt')};
  let F=Object.assign({st:'',ci:'',ch:''},ld(KEY)||{}),L=ld(LKEY),lim=30,nearest=false,kw='';
  if(L&&!(isFinite(L.lat)&&isFinite(L.lon)))L=null;
  const rad=()=>(L&&RADII.includes(L.r))?L.r:25;
  const opt=(v,t,n,dis)=>`<option value="${E(v)}"${dis?' disabled':''}>${E(t)}${n!=null?` (${n})`:''}</option>`;
  const sc={};D.deals.forEach(d=>sc[d.state]=(sc[d.state]||0)+1);
  const withD=(D.states||[]).filter(s=>sc[s.code]).sort((a,b)=>a.name.localeCompare(b.name)),zero=(D.states||[]).filter(s=>!sc[s.code]);
  el.st.innerHTML=opt('','Choose a state',null)+withD.map(s=>opt(s.code,s.name,sc[s.code])).join('')+
    (zero.length?`<optgroup label="No deals found yet">${zero.map(s=>opt(s.code,s.name,0,true)).join('')}</optgroup>`:'');
  if(F.st&&!sc[F.st])F={st:'',ci:'',ch:''};
  // keyword filter: every word must appear in the deal, store, chain or city (e.g. "gummies", "vape", "bogo", "lume")
  const hay=d=>(d._h||(d._h=[d.deal,d.store,d.chain,d.city,NM[d.state],d.state,d.note,d.kind].join(' ').toLowerCase()));
  const kwOK=d=>!kw||kw.split(/\s+/).every(w=>hay(d).includes(w)||(w==='bogo'&&/buy one,? get one|b1g1|2 for 1/.test(hay(d))));
  // ---------- browse mode (no location): State → City → Chain ----------
  const inState=()=>D.deals.filter(d=>!F.st||d.state===F.st);
  function fillCity(){const C={};let multi=0;inState().forEach(d=>{const cs=cities(d);if(!cs.length)multi++;cs.forEach(c=>C[c]=(C[c]||0)+1)});
    const ks=Object.keys(C).sort((a,b)=>a.localeCompare(b));if(F.ci&&F.ci!=='*'&&!C[F.ci])F.ci='';
    el.ci.innerHTML=opt('','All cities',null)+ks.map(k=>opt(k,k,C[k])).join('')+(multi?opt('*','Statewide / multiple stores',multi):'');el.ci.value=F.ci;el.ci.disabled=!F.st}
  const inCity=()=>inState().filter(d=>{if(!F.ci)return true;const cs=cities(d);if(F.ci==='*')return!cs.length;return cs.includes(F.ci)||!cs.length});
  function fillChain(){const C={};inCity().forEach(d=>C[d.chain]=(C[d.chain]||0)+1);const ks=Object.keys(C).sort((a,b)=>a.localeCompare(b));if(F.ch&&!C[F.ch])F.ch='';
    el.ch.innerHTML=opt('','All chains',null)+ks.map(k=>opt(k,k,C[k])).join('');el.ch.value=F.ch;el.ch.disabled=!F.st}
  // ---------- rows ----------
  const ev=d=>d.kind==='everyday'?' · <span class="tag dl-ev">EVERYDAY</span>':'';
  const foot=d=>`<div class="small dim">${d.valid?`Valid: ${E(d.valid)}`:'Dates not stated on the page'} · collected ${E(d.collected)}${d.note?` · ${E(d.note)}`:''}</div>`;
  const where=d=>cities(d).length?d.city:(d.city||'multiple stores');
  const rowB=d=>`<div class="item dl"><a class="t" href="${E(d.url)}" target="_blank" rel="noopener">${E(d.deal)}</a>
    <div class="m"><b>${E(d.store)}</b> · ${E(where(d))}, ${E(d.state)}${ev(d)}</div>${foot(d)}</div>`;
  const rowN=x=>{const d=x.d,l=x.l;let dist;
    if(!l)dist=`<span class="dl-mi sw">${d.region?'REGION':'STATEWIDE'}</span> <b>${E(d.store)}</b> · ${E(d.region?d.region.name+', '+d.state:NM[d.state]||d.state)}`;
    else dist=`<span class="dl-mi"${l.precision==='city'?' title="Store address not known: distance to the city centre"':''}>${l.precision==='city'?'≈':''}${fmt(x.m)} mi</span> <b>${E(l.name||d.store)}</b>, ${E(l.city)}${l.precision==='city'?' <span class="mute">(city centre)</span>':''}${x.more?` <span class="mute">+${x.more} more store${x.more>1?'s':''}</span>`:''}`;
    return`<div class="item dl"><div class="m dl-where">${dist}${ev(d)}</div><a class="t" href="${E(d.url)}" target="_blank" rel="noopener">${E(d.deal)}</a>${foot(d)}</div>`};
  const more=(n,id)=>n>lim?`<p><button class="btn sm ghost" type="button" data-more>Show ${n-lim} more</button></p>`:'';
  // ---------- location mode ----------
  function scored(){const out=[];for(const d of D.deals){if(!kwOK(d))continue;
      if(d.loc&&d.loc.length){let b=null,bm=1e9;for(const i of d.loc){const l=LOC[i];if(!l)continue;const m=mi(L.lat,L.lon,l.lat,l.lon);if(m<bm){bm=m;b=l}}
        if(b){const r=rad();out.push({d,l:b,m:bm,more:d.loc.filter(i=>LOC[i]&&mi(L.lat,L.lon,LOC[i].lat,LOC[i].lon)<=Math.max(r,bm)).length-1});continue}}
      out.push({d,l:null,m:Infinity})}
    return out.sort((a,b)=>a.m-b.m)}
  const inReg=d=>{const b=d.region&&d.region.bbox;return!b||(L.lat>=b[0]&&L.lat<=b[2]&&L.lon>=b[1]&&L.lon<=b[3])};
  function showNear(){const r=rad(),S=scored(),near=S.filter(x=>x.m<=r),sw=S.filter(x=>!x.l&&L.st&&x.d.state===L.st&&inReg(x.d));
    el.rad.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.r===r)));
    const kwT=kw?` matching “${E(kw)}”`:'';let h='';
    if(near.length&&!nearest){$('#dl-count').innerHTML=`<b>${near.length}</b> deal${near.length===1?'':'s'} within ${r} mi of ${E(L.label)}${kwT}, nearest first${sw.length?` · plus ${sw.length} statewide`:''}`;
      h=near.slice(0,lim).map(rowN).join('')+more(near.length)}
    else{const far=S.filter(x=>x.l);
      if(nearest){$('#dl-count').innerHTML=`Nearest deals to ${E(L.label)}${kwT}, any distance`;h=far.slice(0,lim).map(rowN).join('')+more(far.length)}
      else{$('#dl-count').innerHTML=`0 deals within ${r} mi of ${E(L.label)}${kwT}`;
        const n=far[0],wid=n?RADII.find(x=>x>r&&x>=n.m):0;
        h=`<div class="dl-empty"><p><b>No deals found within ${r} miles.</b> ${n?`The nearest listed deal is ${fmt(n.m)} mi away (${E(n.l.name||n.d.store)}, ${E(n.l.city)}, ${E(n.l.state)}).`:kw?'Nothing matches that keyword anywhere.':''}</p>
          <p>${wid?`<button class="btn sm" type="button" data-r="${wid}">Widen to ${wid} mi</button> `:''}${n?`<button class="btn sm ghost" type="button" data-nearest>Show nearest deals anyway</button>`:''}${kw?` <button class="btn sm ghost" type="button" data-clearkw>Clear keyword</button>`:''}</p>
          <p class="small mute">This test list covers ${ok.length} dispensary pages, so many areas have no stores listed yet.</p></div>`}}
    if(sw.length&&!nearest)h+=`<h3 class="dl-sub">Statewide deals in ${E(NM[L.st]||L.st)} <span class="small mute">(chain-wide; store addresses not listed, so no distance)</span></h3>`+sw.slice(0,12).map(rowN).join('');
    list.innerHTML=h}
  function show(){el.pr.hidden=!!L;el.fl.hidden=!!L;el.rad.hidden=!L;el.cur.hidden=!L;
    if(L){el.cur.innerHTML=`<span class="dim">Near</span> <b>${E(L.label)}</b> <button type="button" class="dl-x" data-clear aria-label="Clear location">change</button>`;showNear();return}
    fillCity();fillChain();
    if(!F.st&&!kw){$('#dl-count').textContent='';list.innerHTML='';return}
    let it=inCity().filter(d=>(!F.ch||d.chain===F.ch)&&kwOK(d));
    if(F.ci&&F.ci!=='*')it=it.filter(d=>cities(d).length).concat(it.filter(d=>!cities(d).length));
    const w=[F.ci==='*'?'statewide / multiple stores':F.ci,F.st?NM[F.st]:'all states',F.ch,kw?`“${kw}”`:''].filter(Boolean).join(' · ');
    $('#dl-count').textContent=`${it.length} deal${it.length===1?'':'s'} · ${w}`;
    list.innerHTML=it.length?it.slice(0,lim).map(rowB).join('')+more(it.length):'<p class="na">No current deals found for this filter yet.</p>';sv(KEY,F)}
  // ---------- choosing a location ----------
  const say=(t,bad)=>{el.msg.innerHTML=t||'';el.msg.className='dl-locmsg small '+(bad?'bad':'dim')};
  function setLoc(o){L=Object.assign({r:rad()},o);L.lat=Math.round(L.lat*1000)/1000;L.lon=Math.round(L.lon*1000)/1000;sv(LKEY,L);lim=30;nearest=false;say('');show()}
  // name for a point: a city with listed stores within 7 mi first (a big city's Census centre can sit miles from its
  // downtown ZIPs, so plain nearest-place would call 48226 "Hamtramck"), otherwise the nearest Census place
  async function label(lat,lon){let b=null,bd=7;for(const k in SC){const c=SC[k],m=mi(lat,lon,c.a.reduce((x,y)=>x+y,0)/c.a.length,c.o.reduce((x,y)=>x+y,0)/c.o.length);if(m<bd){bd=m;b={n:c.n,st:c.st}}}
    if(b)return b;try{const p=nearestPlace(await places(),lat,lon);return p?{n:p.n,st:p.st}:null}catch(e){return null}}
  async function find(q){q=q.trim().replace(/\s+/g,' ');if(!q)return;say('Looking up…');
    try{const z=q.match(/^(\d{5})(?:-\d{4})?$/);
      if(z){const m=await zips(),c=m.get(z[1]);if(!c)return say(`ZIP ${E(z[1])} not found in the Census ZIP table. Try a nearby ZIP or a city.`,1);
        const p=await label(c[0],c[1]);return setLoc({lat:c[0],lon:c[1],label:z[1]+(p?` (${p.n}, ${p.st})`:''),st:p&&p.st,src:'zip'})}
      // state name or code alone → browse that state
      const sc2=CODE[q.toLowerCase()]||(/^[a-z]{2}$/i.test(q)&&NM[q.toUpperCase()]?q.toUpperCase():'');
      if(sc2){L=null;sv(LKEY,null);F={st:sc2,ci:'',ch:''};el.st.value=sc2;say(`Showing ${E(NM[sc2])}. Add a city or ZIP to sort by distance.`);return show()}
      const m=q.match(/^(.*?)[,\s]+([A-Za-z]{2}|[A-Za-z ]{4,})$/),cands=[];
      let name=q.toLowerCase(),st='';
      if(m){const s2=m[2].trim();const c=CODE[s2.toLowerCase()]||(s2.length===2&&NM[s2.toUpperCase()]?s2.toUpperCase():'');if(c){name=m[1].trim().toLowerCase();st=c}}
      name=name.replace(/^st\.? /,'st. ').replace(/^mt\.? /,'mount ').replace(/^saint /,'st. ');
      for(const k in SC){const c=SC[k];if(c.n.toLowerCase().replace(/^saint /,'st. ')===name&&(!st||c.st===st))cands.push({n:c.n,st:c.st,lat:c.a.reduce((x,y)=>x+y,0)/c.a.length,lon:c.o.reduce((x,y)=>x+y,0)/c.o.length})}
      if(!cands.length){const P=await places();for(const p of P)if(p.k===name&&(!st||p.st===st))cands.push(p)}
      if(!cands.length)return say(`Couldn't find “${E(q)}”. Try a 5-digit ZIP, or “City, ST” (e.g. Jackson, MI).`,1);
      const c=cands[0];setLoc({lat:c.lat,lon:c.lon,label:`${c.n}, ${c.st}`,st:c.st,src:'city'});
      if(cands.length>1)say('Not this one? '+cands.slice(1,6).map(x=>`<button type="button" class="dl-alt" data-alt="${E(x.n)}, ${E(x.st)}">${E(x.n)}, ${E(x.st)}</button>`).join(' '))
    }catch(e){say('Location tables failed to load. Use the state filters below.',1);L=null;show()}}
  $('#dl-near').onclick=()=>{if(!navigator.geolocation)return say('This browser has no location option. Type a ZIP or city instead.',1);
    say('Asking your browser for your location (it stays on this device)…');
    navigator.geolocation.getCurrentPosition(async p=>{const la=p.coords.latitude,lo=p.coords.longitude,pl=await label(la,lo);
        setLoc({lat:la,lon:lo,label:pl?`your location (near ${pl.n}, ${pl.st})`:'your location',st:pl&&pl.st,src:'gps'})},
      e=>say(e.code===1?'Location permission was declined. Type a ZIP or city instead.':'Couldn\'t get your location. Type a ZIP or city instead.',1),
      {enableHighAccuracy:false,timeout:12000,maximumAge:600000})};
  $('#dl-search').onsubmit=e=>{e.preventDefault();find(el.q.value)};
  let kt;el.kw.oninput=()=>{clearTimeout(kt);kt=setTimeout(()=>{kw=el.kw.value.trim().toLowerCase();lim=30;show()},150)};
  el.rad.onclick=e=>{const b=e.target.closest('button[data-r]');if(b&&L){L.r=+b.dataset.r;sv(LKEY,L);lim=30;nearest=false;show()}};
  $('#deals').addEventListener('click',e=>{const t=e.target;
    if(t.closest('[data-more]')){lim+=40;show()}
    else if(t.closest('.dl-empty [data-r]')){L.r=+t.closest('[data-r]').dataset.r;sv(LKEY,L);show()}
    else if(t.closest('[data-nearest]')){nearest=true;show()}
    else if(t.closest('[data-clearkw]')){el.kw.value='';kw='';show()}
    else if(t.closest('[data-clear]')){L=null;sv(LKEY,null);say('');el.q.value='';el.q.focus();show()}
    else if(t.closest('[data-alt]')){const v=t.closest('[data-alt]').dataset.alt;el.q.value=v;find(v)}});
  el.st.value=F.st;
  el.st.onchange=()=>{F={st:el.st.value,ci:'',ch:''};lim=30;show()};
  el.ci.onchange=()=>{F.ci=el.ci.value;F.ch='';lim=30;show()};
  el.ch.onchange=()=>{F.ch=el.ch.value;lim=30;show()};
  if(L&&L.src!=='gps')el.q.value=L.label.replace(/ \(.*\)$/,'');
  show();
  const S=D.sponsored||{};
  $('#dl-sponsored').innerHTML=`<div class="dl-sph"><span class="dl-splbl">Sponsored</span><span class="dl-ex">${E(S.label||'EXAMPLE LAYOUT')}</span></div>
    <p class="small dim">${E(S.note||'')}</p>${(S.items||[]).length?'':`<div class="dl-skel" aria-hidden="true"><i></i><i></i><i class="s"></i></div><p class="small mute">No sponsored deals. This empty box only shows where a paid, labeled listing would sit.</p>`}`;
  const byS=(D.states||[]).map(s=>`${E(s.code)} ${sc[s.code]||0}`).join(' · ');
  const grp={};ok.forEach(s=>(grp[s.state]=grp[s.state]||[]).push(s));
  const G=D.geo||{};
  $('#dl-foot').innerHTML=`<p><b>21+ only.</b> ${E((D.disclaimer||'').replace(/^21\+ only\.\s*/,''))}</p>
    <p><b>Your location stays on your device.</b> “Near me” asks your browser only when you tap it; ZIPs and cities are looked up from tables downloaded to this page, and distances are worked out here. Nothing about where you are is sent to us or anyone else. The last place you picked is remembered in this browser only (tap “change” to clear it).</p>
    <p><b>How this works.</b> Last checked ${E(clock(ts))}. A test agent reads each dispensary's own free public deals page (robots.txt checked first; no logins, no menu platforms or aggregators), keeps each deal in the store's own words, and drops anything expired, dated in the future or not clearly current. At most ${E(D.per_store||10)} deals per store. ${E(D.state_note||'')}</p>
    <p><b>Distances.</b> ${E(D.geo_note||'')} ${G.locations?`${G.store_points} store addresses and ${G.city_points} city-centre points; ${G.deals_statewide} chain-wide deals have no store list and show as statewide.`:''} ZIP and city centres: US Census Bureau 2023 Gazetteer (public domain). Geocoding: US Census Bureau; some addresses © OpenStreetMap contributors (ODbL).</p>
    <p><b>Dispo Deals by state</b> (every state with legal dispensaries, including 0 so far): ${byS}</p>
    <details><summary>Sources read this check (${ok.length})</summary><p>${Object.keys(grp).sort().map(k=>`<b>${E(k)}</b> ${grp[k].map(s=>`<a href="${E(s.url)}" target="_blank" rel="noopener">${E(s.name)}</a>`).join(', ')}`).join(' · ')}</p></details>
    ${bad.length?`<details><summary>No deals this check (${bad.length})</summary><p>${bad.map(s=>`${E(s.state)} ${E(s.name)}: ${E(s.status)}`).join('<br>')}</p></details>`:''}
    ${D.not_used&&D.not_used.length?`<details><summary>Not used (${D.not_used.length})</summary><p>${D.not_used.map(n=>`<b>${E(n.name)}</b>: ${E(n.why)}`).join('<br>')}</p></details>`:''}`;
}
fetch('/terminal/data/deals.json',{cache:'no-cache'}).then(r=>r.ok?r.json():null).catch(()=>null).then(render);
})();
