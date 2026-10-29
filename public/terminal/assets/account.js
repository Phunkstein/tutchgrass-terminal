import {sb,BASE} from './app.js';
const $=s=>document.querySelector(s); const c=await sb();
const redirect=location.origin+BASE+'account/';
const say=(el,t,cls='ok')=>{el.textContent=t;el.className='msg '+cls};
async function render(){ const {data:{session}}=await c.auth.getSession(); $('#out').classList.toggle('hide',!!session); $('#in').classList.toggle('hide',!session);
  if(!session) return; const u=session.user; $('#who').textContent=u.email;
  // age flag recorded at sign-up
  const {data:prof}=await c.from('profiles').select('*').eq('id',u.id).maybeSingle();
  if(!prof && localStorage.getItem('tt_age21')==='1'){ await c.from('profiles').insert({id:u.id,is_21_plus:true}); }
  $('#age-late').classList.toggle('hide',!!prof||localStorage.getItem('tt_age21')==='1');
  const {data:pp}=await c.from('public_profiles').select('*').eq('id',u.id).maybeSingle();
  const pend=localStorage.getItem('tt_username'); if(!pp&&pend){ await c.from('public_profiles').insert({id:u.id,username:pend}); localStorage.removeItem('tt_username'); return render(); }
  $('#uname').value=pp?.username||''; $('#handle').textContent=pp?.username?'@'+pp.username:'(no username yet)';
  const {data:subs}=await c.from('submissions').select('brand,product,status,created_at,kind').order('created_at',{ascending:false});
  const n=(subs||[]).filter(s=>s.kind==='coa').length;
  const badges=[n>=1&&'🧪 First COA',n>=5&&'🔬 Lab Rat',n>=20&&'🏆 COA Hunter'].filter(Boolean);
  $('#badges').innerHTML=badges.length?badges.map(b=>`<span class="stk honest">${b}</span>`).join(''):'<span class="muted small">Submit a COA to earn your first badge. (Badges are a beta stub and get granted after moderator approval at launch.)</span>';
  $('#subs').innerHTML=(subs||[]).map(s=>`<li>${esc(s.brand)} · ${esc(s.product)} · <span class="pill">${s.status}</span></li>`).join('')||'<li class="muted">None yet.</li>';
  const {data:w}=await c.from('brand_watches').select('brand_slug');
  $('#watches').innerHTML=(w||[]).map(x=>`<li><a href="${BASE}${x.brand_slug}/">${x.brand_slug}</a> <button class="btn ghost" style="min-height:36px;padding:4px 10px" data-unwatch="${x.brand_slug}">Remove</button></li>`).join('')||'<li class="muted">Tap "Watch this brand" on any brand page.</li>';
  document.querySelectorAll('[data-unwatch]').forEach(b=>b.onclick=async()=>{await c.from('brand_watches').delete().eq('brand_slug',b.dataset.unwatch);render()});
  const pw=localStorage.getItem('tt_watch'); if(pw){localStorage.removeItem('tt_watch');await c.from('brand_watches').insert({brand_slug:pw});render();}
  const g=JSON.parse(localStorage.getItem('tt_game_v1')||'{}'); const {data:sc}=await c.from('game_scores').select('*').eq('user_id',u.id).maybeSingle();
  const best=Math.max(g.best||0,sc?.best_streak||0); $('#best').textContent=best;
  if(g.best&&(!sc||g.best>sc.best_streak)) await c.from('game_scores').upsert({user_id:u.id,best_streak:best,current_streak:g.streak||0,rounds_played:Math.max(g.played||0,sc?.rounds_played||0),correct:Math.max(g.correct||0,sc?.correct||0)});
}
const esc=s=>String(s).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
$('#signup').addEventListener('submit',async e=>{e.preventDefault(); const f=new FormData(e.target),m=$('#m1');
  if(!f.get('age')) return say(m,'You must confirm you are 21+ to create an account.','dn');
  const un=String(f.get('username')||'').trim(); if(un&&!/^[A-Za-z0-9_]{3,20}$/.test(un)) return say(m,'Usernames: 3–20 letters, numbers or _','dn');
  localStorage.setItem('tt_age21','1'); if(un) localStorage.setItem('tt_username',un);
  say(m,'Sending magic link…','muted');
  const {error}=await c.auth.signInWithOtp({email:String(f.get('email')).trim(),options:{emailRedirectTo:redirect}});
  error?say(m,'Could not send: '+error.message,'dn'):say(m,'✨ Magic link sent! Open it on this device to finish signing in.'); });
$('#google')?.addEventListener('click',async()=>{ if(!$('#age').checked) return say($('#m1'),'Tick the 21+ box first.','dn'); localStorage.setItem('tt_age21','1');
  const {error}=await c.auth.signInWithOAuth({provider:'google',options:{redirectTo:redirect}}); if(error) say($('#m1'),'Google sign-in is not switched on yet. Use the magic link instead.','dn'); });
$('#uform').addEventListener('submit',async e=>{e.preventDefault(); const un=$('#uname').value.trim(),m=$('#m2');
  if(!/^[A-Za-z0-9_]{3,20}$/.test(un)) return say(m,'3–20 letters, numbers or _','dn');
  const {data:{user}}=await c.auth.getUser(); const {error}=await c.from('public_profiles').upsert({id:user.id,username:un});
  error?say(m,error.code==='23505'?'That username is taken.':error.message,'dn'):(say(m,'Saved ✓'),render()); });
$('#agebtn')?.addEventListener('click',async()=>{const {data:{user}}=await c.auth.getUser(); await c.from('profiles').insert({id:user.id,is_21_plus:true}); render();});
$('#signout').addEventListener('click',async()=>{await c.auth.signOut();render()});
$('#delete').addEventListener('click',async()=>{ if(!confirm('Delete your account, username, scores and brand watches? This cannot be undone.')) return;
  const {error}=await c.rpc('delete_my_account'); if(!error){await c.auth.signOut();say($('#m3'),'Your account was deleted.');render()} else say($('#m3'),error.message,'dn'); });
c.auth.onAuthStateChange(()=>render()); render();
