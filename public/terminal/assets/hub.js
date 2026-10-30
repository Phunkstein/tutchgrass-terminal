// Hub extras: countdown, copy-link, chip filter, Lab Duel, Terp Quiz. No network calls.
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const SITE='https://tutchgrass.com/terminal/';
// countdown
$$('[data-countdown]').forEach(el=>{const t=new Date(el.dataset.countdown).getTime();const u=k=>el.querySelector(`[data-u="${k}"]`);
  const tick=()=>{let d=Math.max(0,t-Date.now());const D=Math.floor(d/864e5);d-=D*864e5;const H=Math.floor(d/36e5);d-=H*36e5;const M=Math.floor(d/6e4);const S=Math.floor((d-M*6e4)/1e3);
    u('d').textContent=D;u('h').textContent=String(H).padStart(2,'0');u('m').textContent=String(M).padStart(2,'0');u('s').textContent=String(S).padStart(2,'0')};tick();setInterval(tick,1000)});
// copy link
$$('[data-copy]').forEach(b=>b.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(b.dataset.copy);b.textContent='✓ Copied'}catch(e){prompt('Copy this link',b.dataset.copy)}}));
// chip filter
$$('[data-chipfilter]').forEach(box=>{const list=$(box.dataset.chipfilter);const bs=$$('button',box);bs.forEach(b=>b.addEventListener('click',()=>{bs.forEach(x=>x.setAttribute('aria-pressed',x===b));$$('[data-k]',list).forEach(el=>el.classList.toggle('hide',!!b.dataset.chip&&el.dataset.k!==b.dataset.chip))}))});
function intent(text,url){return 'https://x.com/intent/post?text='+encodeURIComponent(text)+'&url='+encodeURIComponent(url)}
function card(cv,kick,big,lines,accent){const g=cv.getContext('2d');const W=1200,H=675;
  const gr=g.createRadialGradient(600,0,50,600,0,900);gr.addColorStop(0,'#15305a');gr.addColorStop(1,'#06101d');g.fillStyle=gr;g.fillRect(0,0,W,H);
  for(let x=-40;x<W+40;x+=44){g.fillStyle='#ffc21a';g.beginPath();g.moveTo(x,0);g.lineTo(x+22,0);g.lineTo(x+4,22);g.lineTo(x-18,22);g.fill()}
  g.fillStyle=accent||'#b4ff2a';g.font='italic 800 40px BC,"Barlow Condensed",Arial Narrow,sans-serif';g.fillText(kick.toUpperCase(),60,100);
  g.fillStyle='#fff';g.font='italic 900 120px BC,"Barlow Condensed",Arial Narrow,sans-serif';g.fillText(big.toUpperCase(),60,240);
  g.font='600 34px B,Barlow,system-ui,sans-serif';g.fillStyle='#cfd8e3';lines.forEach((l,i)=>g.fillText(l,60,320+i*52));
  g.fillStyle='#b4ff2a';g.font='italic 900 44px BC,"Barlow Condensed",sans-serif';g.fillText('TUTCHGRASS TERMINAL',60,620);g.fillStyle='#93a6c1';g.font='700 26px BC,"Barlow Condensed",sans-serif';g.fillText('tutchgrass.com/terminal · real COA numbers',560,618);return cv.toDataURL('image/png')}
// ---------- Lab Duel
const dd=$('#duel-data');
if(dd){const deck=JSON.parse(dd.textContent);let st=+(localStorage.tgDuelStreak||0)*0,best=+(localStorage.tgDuelBest||0),played=0,pair=[],done=false;
  const cards=$$('.dcard');const S=()=>{$('#d-streak').textContent=st;$('#d-best').textContent=best;$('#d-played').textContent=played};
  const pick=()=>{let a,b,n=0;do{a=deck[Math.random()*deck.length|0];b=deck[Math.random()*deck.length|0];n++}while((a.b===b.b||Math.abs(Math.abs(a.dev)-Math.abs(b.dev))<2)&&n<500);return[a,b]};
  const show=()=>{pair=pick();done=false;$('#d-res').classList.add('hide');cards.forEach((c,i)=>{const x=pair[i];c.className='dcard';c.disabled=false;
    c.innerHTML=`<span class="dt">${esc(x.t)}</span><b>${esc(x.b)}</b><span class="dp">${esc(x.p)}</span><span class="dl">LABEL SAYS</span><span class="dv">${x.cl} <small>${esc(x.u)}</small></span><span class="dr hide">LAB: <b>${x.lab}</b> · ${x.dev>0?'+':''}${x.dev}%</span>`})};
  cards.forEach((c,i)=>c.addEventListener('click',()=>{if(done)return;done=true;played++;const w=Math.abs(pair[0].dev)<=Math.abs(pair[1].dev)?0:1,ok=i===w;
    st=ok?st+1:0;best=Math.max(best,st);localStorage.tgDuelBest=best;S();
    cards.forEach((cc,j)=>{cc.classList.add(j===w?'win':'lose');cc.querySelector('.dr').classList.remove('hide');cc.insertAdjacentHTML('beforeend',`<a class="dcoa" href="${esc(pair[j].coa)}" target="_blank" rel="noopener nofollow">COA ↗</a>`)});
    $('#d-verdict').innerHTML=ok?`<span class="ok">✓ Correct!</span> ${esc(pair[w].b)} was ${Math.abs(pair[w].dev)}% off vs ${Math.abs(pair[1-w].dev)}%`:`<span class="dn">✗ Nope.</span> ${esc(pair[w].b)} was closer (${Math.abs(pair[w].dev)}% vs ${Math.abs(pair[1-w].dev)}%)`;
    $('#d-res').classList.remove('hide');
    const url=card($('#d-card'),'⚔ Lab Duel',`Streak ${st}`,[`Best: ${best} · Played: ${played}`,'Whose label was closer to the lab result?','Real hemp COAs. Can you beat me?'],'#ffc21a');$('#d-dl').href=url}));
  $('#d-next').addEventListener('click',show);
  $('#d-share').addEventListener('click',()=>open(intent(`⚔️ Lab Duel: I'm on a ${st}-in-a-row streak (best ${best}) guessing whose hemp label was closer to the lab result. Real COA numbers.`,SITE+'duel/'),'_blank'));
  S();show()}
// ---------- Terp quiz
const qd=$('#quiz-data');
if(qd){const Q=JSON.parse(qd.textContent);const box=$('#qz');let i=0;const sc={};
  const ask=()=>{const q=Q.q[i];const opts=[...q.o].sort(()=>Math.random()-.5);
    box.innerHTML=`<div class="qp">Question ${i+1} / ${Q.q.length}</div><div class="qbar"><i style="width:${i/Q.q.length*100}%"></i></div><h2>${esc(q.q)}</h2><div class="qopts">${opts.map(o=>`<button class="btn qo" data-k="${o.k}">${esc(o.t)}</button>`).join('')}</div>`;
    $$('.qo',box).forEach(b=>b.addEventListener('click',()=>{sc[b.dataset.k]=(sc[b.dataset.k]||0)+1;i++;i<Q.q.length?ask():res()}))};
  const res=()=>{const k=Object.keys(sc).sort((a,b)=>sc[b]-sc[a]||Math.random()-.5)[0];const r=Q.r[k];const url=SITE+'quiz/'+k+'/';
    box.innerHTML=`<div class="qp">Your terp personality</div><h2 class="qr">${esc(r.name)}<br><span style="color:var(--g)">${esc(r.title)}</span></h2><p>${esc(r.blurb)}</p><p class="small muted">Aroma: ${esc(r.aroma)} · Also in: ${esc(r.also)}</p>
    <div class="card"><b>What studies looked at:</b> ${r.n} recent studies we read mention ${esc(r.name)} (${esc(r.goals.join(', ').toLowerCase())}); ${r.h} in humans. Example: ${esc(r.hl)} <a href="https://pubmed.ncbi.nlm.nih.gov/${r.hlp}/" target="_blank" rel="noopener">PMID ${r.hlp} ↗</a></div>
    <img class="sharecard" src="/terminal/share/hub/quiz_${k}.png" alt="Your result card"><div class="row" style="flex-wrap:wrap;justify-content:center"><a class="btn p" target="_blank" rel="noopener" href="${intent(`I got ${r.name}: ${r.title} 🌿 Which terpene are you?`,url)}">𝕏 Share result</a><a class="btn ghost" href="/terminal/share/hub/quiz_${k}.png" download>⬇ Card</a><button class="btn ghost" id="qa">↻ Retake</button></div>`;
    $('#qa').addEventListener('click',()=>{i=0;for(const x in sc)delete sc[x];ask()})};
  ask()}
