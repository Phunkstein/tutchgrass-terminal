import {SB_URL,SB_KEY} from './app.js';
const p=new URLSearchParams(location.search),m=document.getElementById('nlmsg'); const a=p.get('a'),t=p.get('t');
if(a&&t){ const fn=a==='confirm'?'newsletter_confirm':'newsletter_unsubscribe';
  const r=await fetch(`${SB_URL}/rest/v1/rpc/${fn}`,{method:'POST',headers:{apikey:SB_KEY,Authorization:`Bearer ${SB_KEY}`,'Content-Type':'application/json'},body:JSON.stringify({token:t})});
  const ok=r.ok&&(await r.json())===true;
  m.textContent=ok?(a==='confirm'?'✅ Confirmed. The Weekly COA drop is on its way.':'👋 You are unsubscribed. No more emails.'):'That link is invalid or already used.'; m.className='msg '+(ok?'ok':'dn'); }
