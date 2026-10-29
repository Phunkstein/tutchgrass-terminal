import {SB_URL,SB_KEY,sb,signedIn,restInsert} from './app.js';
document.querySelectorAll('form[data-submit]').forEach(f=>f.addEventListener('submit',async e=>{ e.preventDefault(); const m=f.querySelector('.msg'),fd=new FormData(f);
  const kind=f.dataset.submit; const file=fd.get('file'); let file_path=null;
  const url=String(fd.get('coa_url')||'').trim()||null;
  if(kind==='coa'&&!url&&!(file&&file.size)){m.textContent='Add a COA link or upload the PDF/photo.';m.className='msg dn';return}
  if(!fd.get('confirm')){m.textContent='Please confirm the COA is public and unedited.';m.className='msg dn';return}
  m.textContent='Uploading…';m.className='msg muted';
  try{
    if(file&&file.size){ if(file.size>10485760) throw new Error('File is over 10 MB');
      const ext=(file.name.split('.').pop()||'pdf').toLowerCase().replace(/[^a-z0-9]/g,''); file_path=`pending/${crypto.randomUUID()}.${ext}`;
      const r=await fetch(`${SB_URL}/storage/v1/object/coa-uploads/${file_path}`,{method:'POST',headers:{apikey:SB_KEY,Authorization:`Bearer ${SB_KEY}`,'Content-Type':file.type||'application/pdf'},body:file});
      if(!r.ok) throw new Error('Upload failed. PDF, PNG, JPG or WEBP only.'); }
    const row={kind,brand:String(fd.get('brand')).trim(),product:String(fd.get('product')).trim(),coa_url:url,file_path,label_claim:String(fd.get('label_claim')||'').trim()||null,notes:String(fd.get('notes')||'').trim()||null};
    if(signedIn()){ const c=await sb(); const {error}=await c.from('submissions').insert(row); if(error) throw error; } else await restInsert('submissions',row);
    m.textContent=kind==='coa'?'🧪 Got it! It went into the moderation queue. A human checks every COA before anything is published.':'Thanks. A human will review your correction request.'; m.className='msg ok'; f.reset();
  }catch(err){ m.textContent='Could not submit: '+(err.message||'error'); m.className='msg dn'; } }));
