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
