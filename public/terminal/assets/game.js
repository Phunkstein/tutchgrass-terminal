import {sb,signedIn,BASE} from './app.js';
const $=s=>document.querySelector(s);
const R=await (await fetch(BASE+'data/guess_the_coa.json')).json();
const LS='tt_game_v1'; const st=Object.assign({streak:0,best:0,played:0,correct:0,i:0},JSON.parse(localStorage.getItem(LS)||'{}'));
const save=()=>localStorage.setItem(LS,JSON.stringify(st));
const label={'under-label':'Under label','on-label':'On label','over-label':'Over label'};
let cur,answered=false;
const r1=v=>{if(v==null)return 'n/a';v=+v;if(v!==0&&Math.abs(v)<0.05)return '<0.1';const r=Math.round(v*10)/10;return Number.isInteger(r)?String(r):r.toFixed(1)};
const sg=v=>(v>0?'+':'')+r1(v);
const F=new FontFace('BCk',`url(${BASE}assets/fonts/BarlowCondensed-BlackItalic.woff)`),F2=new FontFace('BCb',`url(${BASE}assets/fonts/BarlowCondensed-Bold.woff)`);
const fontsReady=Promise.all([F.load(),F2.load()]).then(f=>f.forEach(x=>document.fonts.add(x))).catch(()=>{});
function show(){ answered=false; cur=R[st.i%R.length];
  $('#q-brand').textContent=cur.brand; $('#q-product').textContent=cur.product;
  $('#q-claim').innerHTML=`${r1(cur.label_claim.value)}<small>${cur.label_claim.unit}</small>`;
  $('#q-num').textContent=`Round ${(st.i%R.length)+1} / ${R.length}`;
  $('#reveal').classList.add('hide'); $('#after').classList.add('hide');
  document.querySelectorAll('.choices .btn').forEach(b=>{b.disabled=false;b.style.opacity=1});
  hud(); }
function hud(){ $('#streak').textContent=st.streak; $('#best').textContent=st.best; $('#acc').textContent=st.played?Math.round(st.correct/st.played*100)+'%':'–'; }
async function pick(v,btn){ if(answered) return; answered=true; const ok=v===cur.answer;
  st.played++; if(ok){st.correct++;st.streak++;st.best=Math.max(st.best,st.streak);confetti();btn.classList.add('pop')} else {st.streak=0;btn.classList.add('shake')}
  save(); hud(); document.querySelectorAll('.choices .btn').forEach(b=>{b.disabled=true;if(b!==btn)b.style.opacity=.45});
  const d=cur.tested_result.deviation_pct; const cls=Math.abs(d)<=10?'ok':d<0?'dn':'up';
  $('#r-verdict').innerHTML=(ok?'<span class="ok">Nailed it!</span> ':'<span class="dn">Not quite.</span> ')+`It's <b class="${cls}">${label[cur.answer]}</b>`;
  $('#r-claim').textContent=r1(cur.label_claim.value); $('#r-lab').textContent=r1(cur.tested_result.value);
  $('#r-unit').textContent=cur.label_claim.unit+' · exact COA value '+cur.tested_result.value;
  $('#r-dev').textContent=sg(d)+'% vs label'; $('#r-dev').className='verdict flip d2 '+cls;
  document.querySelectorAll('#reveal .flip').forEach(e=>{e.style.animation='none';e.offsetWidth;e.style.animation=''});
  $('#r-meta').textContent=[cur.lab,cur.test_date,cur.batch&&('batch '+cur.batch)].filter(Boolean).join(' · ');
  $('#r-coa').href=cur.coa_url; $('#r-brand').href=BASE+cur.brand_slug+'/';
  $('#reveal').classList.remove('hide'); $('#after').classList.remove('hide');
  $('#save-streak').classList.toggle('hide',signedIn());
  drawCard(ok,d); syncScore();
  $('#reveal').scrollIntoView({behavior:'smooth',block:'start'}); }
document.querySelectorAll('.choices .btn').forEach(b=>b.addEventListener('click',()=>pick(b.dataset.v,b)));
$('#next').addEventListener('click',()=>{st.i++;save();show();window.scrollTo({top:0,behavior:'smooth'})});
async function syncScore(){ if(!signedIn()) return; try{ const c=await sb(); const {data:{user}}=await c.auth.getUser(); if(!user) return;
  const {data:row}=await c.from('game_scores').select('*').eq('user_id',user.id).maybeSingle();
  const best=Math.max(st.best,row?.best_streak||0);
  await c.from('game_scores').upsert({user_id:user.id,best_streak:best,current_streak:st.streak,rounds_played:Math.max(st.played,row?.rounds_played||0),correct:Math.max(st.correct,row?.correct||0),updated_at:new Date().toISOString()}); }catch(e){} }
// share card (canvas → PNG), scoreboard style
async function drawCard(ok,d){ await fontsReady; const c=$('#card'),x=c.getContext('2d'),W=1200,H=675; c.width=W;c.height=H;
  const g=x.createLinearGradient(0,0,0,H); g.addColorStop(0,'#0a1a2f'); g.addColorStop(1,'#06101d'); x.fillStyle=g; x.fillRect(0,0,W,H);
  haz(x,0,0,W,22); haz(x,0,H-22,W,22);
  x.fillStyle='#b4ff2a'; x.font='italic 900 44px BCk,sans-serif'; x.fillText('GUESS THE COA',56,92);
  x.fillStyle='#93a6c1'; x.font='700 28px BCb,sans-serif'; x.fillText('TUTCHGRASS LABS · LABEL VS LAB',56,128);
  x.fillStyle='#f3f7fc'; x.font='italic 900 50px BCk,sans-serif'; wrap(x,`${cur.brand.toUpperCase()}: ${cur.product}`,56,200,W-112,54,2);
  // panels
  const P=(X,lbl,val,col)=>{x.fillStyle='#0d1d33';x.fillRect(X,268,500,210);x.strokeStyle=col;x.lineWidth=4;x.strokeRect(X,268,500,210);
    x.fillStyle='#93a6c1';x.font='700 30px BCb,sans-serif';x.fillText(lbl,X+28,312);x.fillStyle=col;x.font='italic 900 120px BCk,sans-serif';x.fillText(val,X+28,440)};
  P(56,'LABEL',r1(cur.label_claim.value),'#f3f7fc'); P(644,'LAB (COA)',r1(cur.tested_result.value),'#ffc21a');
  x.fillStyle='#ff3b4a'; x.font='italic 900 56px BCk,sans-serif'; x.fillText('VS',570,392);
  x.fillStyle='#93a6c1'; x.font='700 26px BCb,sans-serif'; x.fillText(cur.label_claim.unit,56,512);
  const col=Math.abs(d)<=10?'#b4ff2a':d<0?'#ff3b4a':'#ff8f1f';
  x.fillStyle=col; x.font='italic 900 54px BCk,sans-serif'; x.fillText(`${sg(d)}% · ${label[cur.answer].toUpperCase()}`,56,575);
  x.fillStyle='#ffc21a'; x.font='italic 900 34px BCk,sans-serif'; x.fillText(`${ok?'GOT IT':'MISSED'} · STREAK ${st.streak} · BEST ${st.best}`,56,630);
  x.fillStyle='#f3f7fc'; x.font='700 28px BCb,sans-serif'; x.textAlign='right'; x.fillText('tutchgrass.com/terminal',W-56,630); x.textAlign='left';
  const u=c.toDataURL('image/png'); $('#card-img').src=u; $('#dl').href=u; }
function haz(x,X,Y,w,h){x.save();x.beginPath();x.rect(X,Y,w,h);x.clip();x.fillStyle='#ffc21a';x.fillRect(X,Y,w,h);x.fillStyle='#06101d';for(let i=-h;i<w+h;i+=36){x.beginPath();x.moveTo(X+i,Y+h);x.lineTo(X+i+18,Y+h);x.lineTo(X+i+18+h,Y);x.lineTo(X+i+h,Y);x.fill()}x.restore()}
function wrap(x,t,X,Y,w,lh,max){const ws=t.split(' ');let l='',n=0;for(const s of ws){const tt=l?l+' '+s:s;if(x.measureText(tt).width>w&&l){x.fillText(l,X,Y);Y+=lh;l=s;if(++n>=max-1){l=ws.slice(ws.indexOf(s)).join(' ');while(x.measureText(l+'…').width>w)l=l.slice(0,-1);x.fillText(l+(l.length<t.length?'…':''),X,Y);return}}else l=tt}x.fillText(l,X,Y)}
$('#share').addEventListener('click',async()=>{ const text=`I'm on a ${st.streak}-round streak at Guess the COA 🧪 Label said ${r1(cur.label_claim.value)}, the lab said ${r1(cur.tested_result.value)}. Can you beat me?`;
  const url=location.origin+BASE+'game/'; try{ if(navigator.share){await navigator.share({text,url});return} }catch(e){}
  await navigator.clipboard?.writeText(text+' '+url); $('#share').textContent='Copied! ✓'; });
// confetti: tiny canvas burst
function confetti(){ const cv=$('#confetti'),x=cv.getContext('2d');cv.width=innerWidth;cv.height=innerHeight;
  const C=['#b4ff2a','#ffc21a','#f3f7fc','#b4ff2a','#ffc21a'];const P=Array.from({length:120},()=>({x:innerWidth/2,y:innerHeight*.45,vx:(Math.random()-.5)*14,vy:-Math.random()*14-4,s:Math.random()*8+4,c:C[Math.random()*5|0],r:Math.random()*6}));
  let f=0;(function loop(){x.clearRect(0,0,cv.width,cv.height);P.forEach(p=>{p.vy+=.45;p.x+=p.vx;p.y+=p.vy;p.r+=.2;x.save();x.translate(p.x,p.y);x.rotate(p.r);x.fillStyle=p.c;x.fillRect(-p.s/2,-p.s/4,p.s,p.s/2);x.restore()});if(++f<90)requestAnimationFrame(loop);else x.clearRect(0,0,cv.width,cv.height)})(); }
show();
// public leaderboard (usernames only, no emails)
import('./app.js').then(async({SB_URL,SB_KEY})=>{ try{ const r=await fetch(`${SB_URL}/rest/v1/game_leaderboard?select=username,best_streak,correct&limit=10`,{headers:{apikey:SB_KEY,Authorization:`Bearer ${SB_KEY}`}});
  const rows=await r.json(); const el=document.querySelector('#glb'); el.classList.add('board','solo'); el.innerHTML=rows.length?rows.map((x,i)=>`<div class="brow"><div class="rk${i<3?' med m'+(i+1):''}">${i+1}</div><div class="nm">@${esc(x.username)}<small>${+x.correct||0} correct</small></div><div></div><div class="gr gr-A">${+x.best_streak||0}</div></div>`).join(''):'<p class="muted">No one on the board yet. Sign in, play, and be first. 🏁</p>'; }catch(e){} });

function esc(t){return String(t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
