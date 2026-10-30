// Tutchgrass Labs: My Condition, saved favorites and email prefs. Uses the existing Supabase client from app.js (app.js/account.js unchanged).
import {sb,signedIn} from './app.js';
const $=s=>document.querySelector(s),E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const LS='tg_conditions_pending',SAVES='tg_saves_pending';
const st={user:null,conds:new Set(),saves:new Set(),prefs:null,ready:false};
const toast=(h)=>{let t=$('.toast');if(!t){t=document.createElement('div');t.className='toast';t.setAttribute('role','status');document.body.appendChild(t)}t.innerHTML=h;clearTimeout(t._t);t._t=setTimeout(()=>t.remove(),5200)};
const lsGet=k=>{try{return JSON.parse(localStorage.getItem(k)||'[]')}catch(e){return[]}},lsSet=(k,v)=>localStorage.setItem(k,JSON.stringify(v));
async function load(){
  if(!signedIn()) return;
  const c=await sb(); const {data:{session}}=await c.auth.getSession(); if(!session) return; st.user=session.user;
  // default-on alerts/digest row on first signed-in load (owner-only RLS); never overwrites a user's choice
  await c.from('email_prefs').upsert({user_id:st.user.id},{onConflict:'user_id',ignoreDuplicates:true});
  // move choices made before sign-up into the account
  const pc=lsGet(LS),ps=lsGet(SAVES);
  if(pc.length){await c.from('user_conditions').upsert(pc.map(id=>({condition_id:id})),{onConflict:'user_id,condition_id',ignoreDuplicates:true});localStorage.removeItem(LS)}
  if(ps.length){await c.from('user_saves').upsert(ps.map(k=>{const [kind,...r]=k.split(':');return{kind,item_id:r.join(':')}}),{onConflict:'user_id,kind,item_id',ignoreDuplicates:true});localStorage.removeItem(SAVES)}
  const [a,b,p]=await Promise.all([c.from('user_conditions').select('condition_id'),c.from('user_saves').select('kind,item_id,created_at').order('created_at',{ascending:false}),c.from('email_prefs').select('alerts,digest,last_digest_at').maybeSingle()]);
  st.conds=new Set((a.data||[]).map(x=>x.condition_id)); st.saves=new Set((b.data||[]).map(x=>x.kind+':'+x.item_id)); st.saveRows=b.data||[]; st.prefs=p.data;
}
function mark(){document.querySelectorAll('[data-save]').forEach(b=>{const on=st.saves.has(b.dataset.save);b.setAttribute('aria-pressed',on);b.textContent=b.textContent.replace(/^[☆★]/,on?'★':'☆')})}
async function toggleSave(key){
  if(!st.user){const p=lsGet(SAVES);if(!p.includes(key)){p.push(key);lsSet(SAVES,p)}
    toast('Saved for when you join. <a href="/terminal/account/#signup">Sign up free</a> to keep favorites and get new-study alerts.');return}
  const c=await sb(),[kind,...r]=key.split(':'),item_id=r.join(':');
  if(st.saves.has(key)){await c.from('user_saves').delete().match({kind,item_id});st.saves.delete(key);toast('Removed from saved.')}
  else{const {error}=await c.from('user_saves').insert({kind,item_id});if(error){toast('Could not save: '+E(error.message));return}st.saves.add(key);toast('Saved. See it under <a href="/terminal/my/">My Condition</a>.')}
  mark(); if(window.TGMY_refresh) window.TGMY_refresh();
}
async function toggleCond(id){
  if(!st.user){const p=new Set(lsGet(LS));p.has(id)?p.delete(id):p.add(id);lsSet(LS,[...p]);return p.has(id)}
  const c=await sb();
  if(st.conds.has(id)){await c.from('user_conditions').delete().eq('condition_id',id);st.conds.delete(id)}
  else{const {error}=await c.from('user_conditions').insert({condition_id:id});if(error){toast('Could not save: '+E(error.message));return}st.conds.add(id)}
  return st.conds.has(id);
}
async function setPref(k,v){const c=await sb();const {error}=await c.from('email_prefs').update({[k]:v,updated_at:new Date().toISOString()}).eq('user_id',st.user.id);
  if(error){toast('Could not update: '+E(error.message));return false} st.prefs[k]=v;toast(v?'On. We will email you when new studies drop.':'Off. No more of those emails.');return true}
document.addEventListener('click',e=>{const b=e.target.closest('[data-save]');if(b){e.preventDefault();toggleSave(b.dataset.save)}});
document.addEventListener('tg:rendered',mark);
const prefsHTML=()=>st.prefs?`<label class="tg"><input type="checkbox" data-pref="alerts" ${st.prefs.alerts?'checked':''}> New-study alerts for my conditions</label><label class="tg"><input type="checkbox" data-pref="digest" ${st.prefs.digest?'checked':''}> Weekly digest in plain words</label><p class="small mute">On by default when you sign up. Every email has a one-click unsubscribe.</p>`:'<p class="small mute">Email settings unavailable right now.</p>';
const bindPrefs=root=>root.querySelectorAll('[data-pref]').forEach(i=>i.onchange=async()=>{if(!await setPref(i.dataset.pref,i.checked))i.checked=!i.checked});
// ---------- /terminal/my/ ----------
async function myPage(){
  const root=$('#my');if(!root)return; let D;
  try{const r=await fetch('/terminal/data/terminal.json',{cache:'no-cache'});if(!r.ok)throw 0;D=await r.json()}catch(e){root.innerHTML='<p class="na">● Study data unavailable right now.</p>';return}
  const N=D.newstudies||{papers:[],by_condition:{},labels:{},grades:{}},C=D.conds||{},SB=Object.fromEntries((D.scoreboard||[]).map(r=>[r.id,r])),SCI=Object.fromEntries(((D.scientist||{}).conditions||[]).map(c=>[c.id,c]));
  const P=Object.fromEntries(N.papers.map(p=>[p.pmid,p])),ids=Object.keys(C),F=Object.fromEntries((D.findings||[]).map(f=>[f.slug,f]));
  const pend=new Set(lsGet(LS)); let sel=new URLSearchParams(location.search).get('c')||localStorage.getItem('tg_last_c')||'';
  if(!C[sel]) sel=st.user&&st.conds.size?[...st.conds][0]:'';
  const mine=id=>st.user?st.conds.has(id):pend.has(id);
  const view=id=>{const c=C[id],s=SB[id],sci=SCI[c.sci],np=(N.by_condition[id]||[]).map(i=>P[i]).filter(Boolean);
    const cta=st.user?`<div class="card"><div class="lbl" style="margin-top:0">Alerts for ${E(c.label)}</div><p class="small">${mine(id)?'★ In your conditions. You will get new studies for this.':'Not in your conditions yet.'}</p><button class="btn sm ${mine(id)?'ghost':''}" data-mine="${E(id)}" type="button">${mine(id)?'Remove from my conditions':'★ Add to my conditions'}</button></div>`
      :`<div class="cta-alert dcta"><h3>Sign up free to get alerts when new studies drop for this</h3><p>We check PubMed for ${E(c.label.toLowerCase())} studies and email you the new ones in plain words, graded honestly. No spam, no selling. Unsubscribe anytime.</p><a class="btn" href="/terminal/account/#signup" data-pend="${E(id)}">Sign up free</a></div>`;
    const mcta=st.user?'':`<a class="mcta" href="/terminal/account/#signup" data-pend="${E(id)}"><b>🔔 Sign up free to get alerts when new studies drop for this</b><span>Free · no spam · unsubscribe anytime</span></a>`;
    return`<div class="cview" id="cv"><div>${mcta}
      <div class="ph" style="margin:6px 0 10px"><h2 style="font-size:22px;margin:0">${E(c.emoji)} ${E(c.label)}</h2><span class="upd" style="font-size:11px">Last updated ${E(c.newest||'no new papers')}</span></div>
      <div class="lbl">New studies, last 30 days · ${np.length}</div>${np.length?'<div class="nsgrid" style="grid-template-columns:1fr">'+np.map(p=>window.TG.paper(p,N.grades,N.labels)).join('')+'</div>':'<p class="small mute">No new cannabis studies on PubMed for this in the last 30 days. That is the honest answer.</p>'}
      <div class="lbl">Most relevant 2025–26 studies · ${c.matches} on PubMed</div><ul class="cites recent">${c.recent.map(x=>`<li><span class="tag t-${E(x.tag)}">${E(x.tag)}</span><a href="https://pubmed.ncbi.nlm.nih.gov/${E(x.pmid)}/" target="_blank" rel="noopener">${E(x.title)}</a> <span class="mute small">${E(x.first_author)} · ${E(x.journal)} · ${E(x.date)}</span>${x.says?`<span class="cc">${E(x.says)}</span>`:''}</li>`).join('')}</ul>
    </div><div style="display:grid;gap:12px">${cta}
      <div class="card"><div class="lbl" style="margin-top:0">Evidence scoreboard</div>${s?`<dl class="kv"><dt>Rank</dt><dd class="mono">#${s.rank} of ${Object.keys(SB).length}</dd><dt>Evidence</dt><dd><span class="badge ev-${E(s.evidence)}">${E(String(s.evidence).toUpperCase())}</span></dd><dt>2025–26</dt><dd class="mono">${s.recent_high.meta} SR/MA · ${s.recent_high.rct} RCT</dd><dt>New 30 d</dt><dd class="mono">${s.new_30d} (${s.new_rct_meta_30d} RCT/MA, ${s.new_mice_30d} animal)</dd></dl>${s.latest?`<p class="small" style="margin:8px 0 0"><b>What changed:</b> <a href="${E(s.latest.url)}" target="_blank" rel="noopener">${E(s.latest.title)}</a> <span class="mono mute">${E(s.latest.date)}</span></p>`:''}`:'<p class="small mute">unavailable</p>'}<a class="small" href="/terminal/#scoreboard">Full scoreboard →</a></div>
      ${sci?`<div class="card"><div class="lbl" style="margin-top:0">What studies suggest</div><p class="small">${E(sci.evidence_note||'')}</p><p class="small dim">${E(sci.mechanism||'')}</p><a class="small" href="/terminal/#cond-${E(sci.id)}">Open in the Scientist →</a></div>`:''}
      <button class="btn ghost sm save" type="button" data-save="condition:${E(id)}">☆ Save this condition</button>
    </div></div>`};
  const savedHTML=()=>{const rows=st.saveRows||[];if(!rows.length)return'<p class="small mute">Nothing saved yet. Tap ☆ Save on a study, finding or condition.</p>';
    return'<ul class="cites">'+rows.map(r=>{if(r.kind==='paper'){const p=P[r.item_id];return`<li><span class="tag">PAPER</span><a href="https://pubmed.ncbi.nlm.nih.gov/${E(r.item_id)}/" target="_blank" rel="noopener">${E(p?p.title:'PubMed '+r.item_id)}</a> <button class="btn sm ghost save" data-save="paper:${E(r.item_id)}">★</button></li>`}
      if(r.kind==='finding'){const f=F[r.item_id];return`<li><span class="tag">FINDING</span><a href="${E(f?f.path:'/terminal/findings/')}">${E(f?f.headline:r.item_id)}</a> <button class="btn sm ghost save" data-save="finding:${E(r.item_id)}">★</button></li>`}
      const c=C[r.item_id];return`<li><span class="tag">CONDITION</span><a href="?c=${E(r.item_id)}">${E(c?c.label:r.item_id)}</a> <button class="btn sm ghost save" data-save="condition:${E(r.item_id)}">★</button></li>`}).join('')+'</ul>'};
  const draw=()=>{
    const head=st.user?`<p class="lede" style="margin:0">Your conditions, the new studies for them, and what you saved. Tap a condition to add it (★) or open it.</p>`
      :`<p class="lede" style="margin:0">Tap a condition to see its newest studies right now, graded honestly. No account needed. <a href="/terminal/account/#signup">Sign up free</a> to get alerts when new studies drop.</p>`;
    const forYou=st.user?(()=>{const l=[...new Set([...st.conds].flatMap(id=>N.by_condition[id]||[]))].map(i=>P[i]).filter(Boolean).sort((a,b)=>(b.date||'').localeCompare(a.date||''));
      return`<div class="cview" style="margin-top:6px"><div class="card"><div class="ph"><h2>New studies for you</h2><span class="meta">${l.length} · last 30 d</span></div>${st.conds.size?(l.length?'<div class="nsgrid" style="grid-template-columns:1fr">'+l.slice(0,6).map(p=>window.TG.paper(p,N.grades,N.labels)).join('')+'</div>':'<p class="small mute">No new studies for your conditions in the last 30 days.</p>'):'<p class="small mute">Add a condition below (tap it, then ★ Add) to see new studies here.</p>'}</div>
      <div style="display:grid;gap:12px"><div class="card"><div class="ph"><h2>Email</h2></div><div id="prefs">${prefsHTML()}</div></div><div class="card"><div class="ph"><h2>Saved</h2><span class="meta">${(st.saveRows||[]).length}</span></div>${savedHTML()}</div></div></div>`})():'';
    root.innerHTML=head+forYou+`<div class="lbl" style="margin-top:18px">${st.user?'Your conditions (★) · tap to open':'Pick a condition'}</div><div class="chips" role="list">${ids.map(id=>`<button class="chip ${mine(id)?'mine':''}" role="listitem" type="button" data-c="${E(id)}" aria-pressed="${id===sel}"><span class="e">${E(C[id].emoji)}</span>${E(C[id].label)}<span class="c">${(N.by_condition[id]||[]).length} new</span></button>`).join('')}</div>`+(sel?view(sel):'<p class="small mute">Pick one above to see its studies.</p>');
    const pf=$('#prefs');if(pf)bindPrefs(pf); mark(); window.TG.E&&0;
  };
  window.TGMY_refresh=async()=>{if(st.user){const c=await sb();const b=await c.from('user_saves').select('kind,item_id,created_at').order('created_at',{ascending:false});st.saveRows=b.data||[]}draw()};
  root.addEventListener('click',async e=>{const ch=e.target.closest('[data-c]');if(ch){sel=ch.dataset.c;localStorage.setItem('tg_last_c',sel);history.replaceState(null,'','?c='+sel);draw();const v=$('#cv');if(v&&innerWidth<760)v.scrollIntoView({behavior:'smooth',block:'start'});return}
    const m=e.target.closest('[data-mine]');if(m){await toggleCond(m.dataset.mine);draw();toast(st.conds.has(m.dataset.mine)?'Added. You will get alerts for this.':'Removed.');return}
    const p=e.target.closest('[data-pend]');if(p){const s=new Set(lsGet(LS));s.add(p.dataset.pend);lsSet(LS,[...s])}});
  draw();
}
// ---------- account page: My research block ----------
function acct(){const el=$('#myresearch');if(!el||!st.user)return;
  el.innerHTML=`<div class="lbl" style="margin-top:0">My research</div><p class="small">${st.conds.size} condition${st.conds.size===1?'':'s'} · ${st.saves.size} saved · <a href="/terminal/my/">Open My Condition →</a></p><div class="lbl">Email</div>${prefsHTML()}`;bindPrefs(el)}
(async()=>{try{await load()}catch(e){console.warn('my.js',e)} st.ready=true; mark(); await myPage(); acct();})();
