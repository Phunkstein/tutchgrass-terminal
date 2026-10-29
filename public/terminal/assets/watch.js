import {sb,signedIn,BASE} from './app.js';
const b=document.getElementById('watch'); if(b){ b.addEventListener('click',async()=>{ const slug=b.dataset.slug;
  if(!signedIn()){ localStorage.setItem('tt_watch',slug); location.href=BASE+'account/?watch='+slug; return; }
  const c=await sb(); const {error}=await c.from('brand_watches').insert({brand_slug:slug});
  b.textContent=(!error||error.code==='23505')?'👀 Watching ✓':'Try again'; }); }
