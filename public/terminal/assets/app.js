// Tutchgrass Terminal: tiny shared JS (no framework)
export const SB_URL='https://ckauuurdpltrqjimjgbt.supabase.co';
export const SB_KEY='sb_publishable_hPcyV-d9mcWJdcYO44Bavw_3bjgCn22';
export const BASE='/terminal/';
let _sb;
export async function sb(){ if(_sb) return _sb;
  const m=await import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm');
  _sb=m.createClient(SB_URL,SB_KEY,{auth:{persistSession:true,detectSessionInUrl:true,flowType:'pkce'}}); return _sb; }
export const signedIn=()=>Object.keys(localStorage).some(k=>/^sb-.*-auth-token$/.test(k));
// REST insert without loading the SDK (fast path for anonymous forms)
export async function restInsert(table,row){
  const r=await fetch(`${SB_URL}/rest/v1/${table}`,{method:'POST',headers:{apikey:SB_KEY,Authorization:`Bearer ${SB_KEY}`,'Content-Type':'application/json',Prefer:'return=minimal'},body:JSON.stringify(row)});
  if(!r.ok){let j={};try{j=await r.json()}catch(e){} const e=new Error(j.message||r.statusText); e.code=j.code; throw e;} return true; }
// animated counters
const io='IntersectionObserver' in window? new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){count(e.target);io.unobserve(e.target)}})):null;
function count(el){const to=+el.dataset.count,dec=+(el.dataset.dec||0),t0=performance.now(),d=1100;
  const step=t=>{const k=Math.min(1,(t-t0)/d),v=to*(1-Math.pow(1-k,3));el.textContent=v.toFixed(dec);if(k<1)requestAnimationFrame(step)};requestAnimationFrame(step)}
document.querySelectorAll('[data-count]').forEach(el=>io?io.observe(el):count(el));
// account chip
const chip=document.getElementById('acct'); if(chip&&signedIn()) chip.textContent='👤 My account';
// newsletter forms
document.querySelectorAll('form[data-newsletter]').forEach(f=>f.addEventListener('submit',async ev=>{
  ev.preventDefault(); const msg=f.querySelector('.msg'); const fd=new FormData(f);
  if(!fd.get('optin')||!fd.get('age')){msg.textContent='Tick both boxes to join (opt-in + 21+).';msg.className='msg dn';return}
  msg.textContent='Sending…';msg.className='msg muted';
  try{await restInsert('newsletter_signups',{email:String(fd.get('email')).trim(),opted_in:true,is_21_plus:true,source:f.dataset.newsletter,consent_text:f.querySelector('.consent').textContent.trim()});
    msg.textContent='🧪 Almost done! Check your inbox for a confirmation link. You are not subscribed until you click it.';msg.className='msg ok';f.reset();}
  catch(e){ if(e.code==='23505'){msg.textContent='That email is already on the list. 🌿';msg.className='msg ok'} else {msg.textContent='Hmm, that did not go through. Try again in a minute.';msg.className='msg dn'} }
}));
// tabs ([data-tabs] > button[aria-controls])
document.querySelectorAll('[data-tabs]').forEach(t=>{const bs=[...t.querySelectorAll('button')];bs.forEach(b=>b.addEventListener('click',()=>{bs.forEach(x=>{const on=x===b;x.setAttribute('aria-selected',on);document.getElementById(x.getAttribute('aria-controls')).classList.toggle('hide',!on)})}))});
// list filter ([data-filter] input filters [data-items] > [data-k])
document.querySelectorAll('[data-filter]').forEach(inp=>{const list=document.querySelector(inp.dataset.filter);const chips=document.querySelectorAll('[data-chip]');let chip='';
  const run=()=>{const q=inp.value.trim().toLowerCase();let n=0;list.querySelectorAll('[data-k]').forEach(el=>{const show=(!q||el.dataset.k.includes(q))&&(!chip||el.dataset.v===chip||el.dataset.m===chip);el.classList.toggle('hide',!show);if(show)n++});const c=document.querySelector('#count');if(c)c.textContent=n};
  inp.addEventListener('input',run);chips.forEach(b=>b.addEventListener('click',()=>{chip=b.dataset.chip;chips.forEach(x=>x.setAttribute('aria-pressed',x===b));run()}));});
// anonymous usage counts → public.page_views (insert-only). Fire-and-forget: never blocks, never throws, skips localhost.
// Sends only: path (no query string), tab, referrer HOSTNAME, utm_source, mobile/desktop, and a random ID that changes daily.
// Never sends cookies, IPs, user agents, ZIPs, cities or coordinates.
const T=(()=>{try{const h=location.hostname;
  if(location.protocol==='file:'||/^(localhost|127\.|0\.0\.0\.0|\[?::1\]?$)|\.local$/.test(h)||navigator.doNotTrack==='1'||navigator.globalPrivacyControl===true)return null;
  const today=new Date().toISOString().slice(0,10);let vd;
  try{const s=JSON.parse(localStorage.getItem('tg_vd')||'null');if(s&&s.d===today&&/^[0-9a-f]{32}$/.test(s.id))vd=s.id;
    else{vd=[...crypto.getRandomValues(new Uint8Array(16))].map(b=>b.toString(16).padStart(2,'0')).join('');localStorage.setItem('tg_vd',JSON.stringify({d:today,id:vd}))}}catch(e){vd=null}
  const cut=(v,n)=>v==null||v===''?null:String(v).slice(0,n);
  let rh=null;try{const r=document.referrer&&new URL(document.referrer).hostname;if(r&&r!==h)rh=r}catch(e){}
  const utm=cut((new URLSearchParams(location.search).get('utm_source')||'').replace(/[^\w.\-]/g,''),60);
  const dev=matchMedia('(pointer:coarse)').matches||innerWidth<760?'mobile':'desktop';let n=0,first=true;
  return(event,label,path)=>{try{if(++n>60)return;const row={path:cut(path||location.pathname,200)||'/',event:cut(event,60),label:cut(label,120),visitor_day:vd,device:dev,utm_source:utm,referrer_host:first?cut(rh,120):null};first=false;
    fetch(`${SB_URL}/rest/v1/page_views`,{method:'POST',keepalive:true,credentials:'omit',referrerPolicy:'no-referrer',headers:{apikey:SB_KEY,Authorization:`Bearer ${SB_KEY}`,'Content-Type':'application/json',Prefer:'return=minimal'},body:JSON.stringify(row)}).catch(()=>{})}catch(e){}}}catch(e){return null}})();
export const track=(e,l,p)=>{if(T)setTimeout(()=>T(e,l,p),0)};
if(T)try{const P=location.pathname.replace(/index\.html$/,''),HOME=P===BASE;let lastTab=null;
  // home tabs: agents.js fires tg:tab on every route (deduped here); other pages: one view on load
  if(HOME){document.addEventListener('tg:tab',e=>{const t=String(e.detail||'all');if(t===lastTab)return;lastTab=t;track('view',t,P+(t==='all'?'':'#'+t))});
    addEventListener('DOMContentLoaded',()=>setTimeout(()=>{if(lastTab==null){lastTab=document.body.dataset.tab||'all';track('view',lastTab,P+(lastTab==='all'?'':'#'+lastTab))}},0))}
  else track('view',null,P);
  const host=a=>{try{return new URL(a.href).hostname}catch(e){return null}};
  document.addEventListener('submit',e=>{const f=e.target;if(!f||!f.id)return;
    if(f.id==='dl-search'||f.id==='th-deals'){const q=(f.querySelector('input[type=search]')||{}).value||'';track('deal_search',(/^\s*\d{5}/.test(q)?'zip':'city')+(f.id==='th-deals'?' · top':''))}   // only the kind of search, never the value
    else if(f.id==='signup')track('signup_start','email')},true);
  document.addEventListener('click',e=>{const t=e.target;if(!t||!t.closest)return;
    if(t.closest('#dl-near,#th-near'))return track('deal_near',t.closest('#th-near')?'top':'deals');
    if(t.closest('#google'))return track('signup_start','google');
    const c=t.closest('[data-c]');if(c&&P===BASE+'my/')return track('condition',c.dataset.c);
    const a=t.closest('a[href]');if(!a)return;
    if(a.closest('#deals')&&a.target==='_blank')return track(a.closest('.item.dl')?'deal_open':'store_open',host(a));
    if(/\/terminal\/account\/#signup$/.test(a.getAttribute('href')||''))track('signup_click',a.closest('header')?'header':'page')},true);
}catch(e){}
