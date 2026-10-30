/* Product Checker: reads a COA (PDF or photo) and/or a label photo INSIDE the browser and checks it with plain rules.
   Nothing is uploaded or stored: files are read with pdf.js (text layer) and tesseract.js (OCR for photos/scans), QR codes
   with jsQR. Libraries load from jsDelivr only when you press Check. Lab lists + action limits: /terminal/data/labs.json,
   refreshed weekly by tools/terminal/agents/labs.py from state regulators and A2LA. Not medical or legal advice. */
(function(){
const LIB={pdf:'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.min.mjs',pdfw:'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.worker.min.mjs',
  ocr:'https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js',qr:'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js'};
const E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const DAY=864e5,TODAY=()=>new Date();
const f2=(x,d=2)=>x==null||isNaN(x)?'?':(+x).toLocaleString('en-US',{maximumFractionDigits:d});
const fmtD=d=>d?d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):'?';
// ---------------- lazy libraries ----------------
const once={};function script(u,g){return once[u]||(once[u]=new Promise((ok,no)=>{if(window[g])return ok(window[g]);const s=document.createElement('script');s.src=u;s.async=true;s.crossOrigin='anonymous';s.onload=()=>ok(window[g]);s.onerror=()=>no(new Error('could not load '+u));document.head.appendChild(s)}))}
let pdfjs;async function PDF(){if(!pdfjs){pdfjs=await import(LIB.pdf);pdfjs.GlobalWorkerOptions.workerSrc=LIB.pdfw}return pdfjs}
let ocrW;async function OCR(img,progress){const T=await script(LIB.ocr,'Tesseract');if(!ocrW)ocrW=await T.createWorker('eng',1,{logger:m=>{if(m.status==='recognizing text'&&progress)progress(Math.round(m.progress*100))}});
  const r=await ocrW.recognize(img);return r.data.text}
async function QR(canvas){try{const jsQR=await script(LIB.qr,'jsQR');const c=canvas.getContext('2d',{willReadFrequently:true}),d=c.getImageData(0,0,canvas.width,canvas.height);const q=jsQR(d.data,d.width,d.height,{inversionAttempts:'attemptBoth'});return q&&q.data?q.data:null}catch(e){return null}}
let LABS=null;const labsP=()=>LABS?Promise.resolve(LABS):fetch('/terminal/data/labs.json',{cache:'no-cache'}).then(r=>r.ok?r.json():null).then(j=>LABS=j).catch(()=>null);
// ---------------- reading files ----------------
function linesFromItems(items){ // rebuild reading-order lines from pdf.js text items using their x/y positions
  const it=items.filter(i=>i.str&&i.str.trim()).map(i=>({s:i.str,x:i.transform[4],y:i.transform[5],w:i.width||0,h:Math.abs(i.transform[3])||8,f:i.fontName})).map((i,k)=>(i.k=k,i));
  it.sort((a,b)=>b.y-a.y||a.x-b.x);const L=[];
  for(const i of it){const l=L.length&&Math.abs(L[L.length-1].y-i.y)<=Math.max(2,Math.min(i.h,L[L.length-1].h)*.45)?L[L.length-1]:null;if(l)l.items.push(i);else L.push({y:i.y,h:i.h,items:[i]})}
  return L.map(l=>{l.items.sort((a,b)=>a.x-b.x);const kept=[],ov=[];const isN=s=>/\d/.test(s);
    for(const i of l.items){const p=kept[kept.length-1];const o=p?Math.min(p.x+p.w,i.x+i.w)-Math.max(p.x,i.x):0;
      if(p&&p.w>0&&i.w>0&&o>0.5*Math.min(p.w,i.w)&&isN(p.s)&&isN(i.s)&&p.s.trim()!==i.s.trim()){ov.push(i.k>p.k?[i.s.trim(),p.s.trim()]:[p.s.trim(),i.s.trim()]);if(i.k>p.k)kept[kept.length-1]=i;continue} // later-drawn text sits on top
      if(p&&o>0.8*Math.min(p.w,i.w)&&p.s===i.s)continue; // fake-bold duplicate
      kept.push(i)}
    let t='',end=null;for(const i of kept){t+=(end!=null&&i.x-end>1?' ':'')+i.s;end=i.x+i.w}return{t:t.replace(/\s+/g,' ').trim(),items:kept,ov}})}
async function readPdf(file,say){
  const lib=await PDF(),doc=await lib.getDocument({data:new Uint8Array(await file.arrayBuffer()),isEvalSupported:false}).promise;
  const meta=await doc.getMetadata().catch(()=>null),info=(meta&&meta.info)||{};const out={kind:'pdf',name:file.name,pages:doc.numPages,lines:[],items:[],overlaps:[],links:[],qr:[],info,ocr:false};
  const N=Math.min(doc.numPages,10);
  for(let p=1;p<=N;p++){say(`Reading page ${p} of ${N}…`);const pg=await doc.getPage(p);const tc=await pg.getTextContent();const ls=linesFromItems(tc.items);
    out.lines.push(...ls.map(l=>l.t));ls.forEach(l=>out.overlaps.push(...l.ov));out.items.push(...ls.flatMap(l=>l.items.map(i=>({s:i.s,f:i.f,line:l.t}))));
    (await pg.getAnnotations().catch(()=>[])).forEach(a=>{if(a.url)out.links.push(a.url)});
    if(p<=3||ls.length<5){const vp=pg.getViewport({scale:2});const cv=document.createElement('canvas');cv.width=vp.width;cv.height=vp.height;await pg.render({canvasContext:cv.getContext('2d'),viewport:vp}).promise;
      const q=await QR(cv);if(q)out.qr.push(q);
      if(ls.length<5){say(`Page ${p} is a scan: reading it with OCR…`);const t=await OCR(cv,n=>say(`OCR page ${p}: ${n}%`));out.lines.push(...t.split('\n').map(s=>s.trim()).filter(Boolean));out.ocr=true}}}
  await doc.destroy();return out}
async function readImage(file,say){
  const bmp=await createImageBitmap(file);const k=Math.min(1,2400/Math.max(bmp.width,bmp.height));const cv=document.createElement('canvas');cv.width=Math.round(bmp.width*k);cv.height=Math.round(bmp.height*k);cv.getContext('2d').drawImage(bmp,0,0,cv.width,cv.height);
  const q=await QR(cv);say(`Reading ${file.name} with OCR…`);const t=await OCR(cv,n=>say(`OCR ${file.name}: ${n}%`));
  return{kind:'image',name:file.name,lines:t.split('\n').map(s=>s.trim()).filter(Boolean),items:[],links:[],qr:q?[q]:[],info:{},ocr:true}}
const isCOA=d=>{const t=d.lines.join(' ').toLowerCase();return['certificate of analysis','analyte','loq','lod','limit of','result','sample id','laborator','batch','pass','not detected','nd '].filter(k=>t.includes(k)).length>=3};
// ---------------- parsing ----------------
const NUM=/^[<>]?\d+(?:[.,]\d+)?%?$/;const ND=/^(nd|<loq|<lod|bql|<lq|n\.d\.|not detected|bloq|nr|nt|n\/a)$/i;
const AN=[['total_thc',/^(?:total\s+(?:active\s+)?(?:Δ|∆|delta[-\s]?)?(?:9[-\s]?)?thc|thc\s+total)(?![a-z])(?!\s*(?:per|\/))/i],['total_cbd',/^(?:total\s+(?:active\s+)?cbd|cbd\s+total)(?![a-z])(?!\s*(?:per|\/))/i],
  ['total_cann',/^(?:total\s+cannabinoids|sum\s+of\s+cannabinoids)(?![a-z])(?!\s*(?:per|\/))/i],
  ['thca',/^(?:(?:Δ|∆|delta[-\s]?|d)9[-\s]?)?(?:thc[-\s]?a(?:[-\s]?a)?|tetrahydrocannabinolic acid)(?![a-z0-9])/i],
  ['d9',/^(?:Δ|∆|delta|d)[-\s]?9[-\s]?(?:thc|tetrahydrocannabinol)(?![a-z0-9-])/i],['d8',/^(?:Δ|∆|delta|d)[-\s]?8[-\s]?(?:thc|tetrahydrocannabinol)(?![a-z0-9-])/i],
  ['d10',/^(?:Δ|∆|delta|d)[-\s]?10[-\s]?thc(?![a-z0-9-])/i],['cbda',/^cbd[-\s]?a(?![a-z0-9])/i],['cbd',/^cbd(?![a-z0-9-])/i],['cbn',/^cbn(?![a-z0-9-])/i],['cbg',/^cbg(?![a-z0-9-])/i],
  ['thcv',/^(?:(?:Δ|∆|delta[-\s]?|d)9[-\s]?)?thcv(?![a-z0-9])/i],['hhc',/^(?:9[rs][-\s]?|\(9[rs]\)[-\s]?)?hhc(?![a-z0-9-])/i],['thco',/^(?:(?:Δ|∆|delta[-\s]?|d)[89][-\s]?)?thc[-\s]?o(?:[-\s]acetate)?(?![a-z])/i],['thcp',/^(?:(?:Δ|∆|delta[-\s]?|d)[89][-\s]?)?thc[-\s]?p(?![a-z])/i]];
const ANL={total_thc:'Total THC',total_cbd:'Total CBD',total_cann:'Total cannabinoids',thca:'THCA',d9:'Delta-9 THC',d8:'Delta-8 THC',d10:'Delta-10 THC',cbda:'CBDA',cbd:'CBD',cbn:'CBN',cbg:'CBG',thcv:'THCV',hhc:'HHC',thco:'THC-O',thcp:'THCP'};
function rowVal(rest,firstFirst,hasMU){ // value in % from the tokens after an analyte name
  const tk=rest.split(/\s+/).filter(Boolean);const nums=[],raw=[];let nd=false,pct=null;
  for(const t of tk){const c=t.replace(/[*†]/g,'');if(ND.test(c)){nd=true;nums.push(null);raw.push(null);continue}
    if(NUM.test(c)){if(hasMU&&c.endsWith('%'))continue;const v=parseFloat(c.replace(',','.').replace(/[<>%]/g,''));nums.push(c.startsWith('<')?null:v);raw.push(c);if(c.endsWith('%')&&pct==null)pct=v}}
  if(nd&&nums.length&&(firstFirst?nums[0]:nums[nums.length-1])==null)return{pct:0,nd:true};
  const v=[],rw=[];nums.forEach((x,i)=>{if(x!=null){v.push(x);rw.push(raw[i])}});
  const dec=t=>{const m=String(t).match(/[.,](\d+)/);return m?m[1].length:0};
  for(let i=v.length-1;i>0;i--)for(let j=i-1;j>=0;j--){const a=v[j],b=v[i],lo=Math.min(a,b),hi=Math.max(a,b);if(lo<=0||lo>100)continue;const lr=a<=b?rw[j]:rw[i];
    for(const k of[10,10000]){const tol=k*5*Math.pow(10,-dec(lr)-1)+hi*0.006;if(Math.abs(hi-lo*k)<=tol)return{pct:lo,how:'pair'}}}
  if(pct!=null)return{pct,how:'%'};
  if(nd&&!v.length)return{pct:0,nd:true};
  const vp=v.filter(x=>x<=100); // a % can't exceed 100: the bigger column is mg/g
  if(vp.length===1)return{pct:vp[0],how:'only'};
  if(vp.length>1)return{pct:firstFirst?vp[0]:vp[vp.length-1],how:'col'};
  return null}
const MONTHS={jan:0,feb:1,mar:2,apr:3,may:4,jun:5,jul:6,aug:7,sep:8,oct:9,nov:10,dec:11};
function dates(line){const out=[];let m;const re=/\b(\d{1,2})[\/.-](\d{1,2})[\/.-](\d{4}|\d{2})\b|\b(\d{4})-(\d{2})-(\d{2})\b|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})\b|\b(\d{1,2})[-\s](jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-\s,]+(\d{4})\b/gi;
  while((m=re.exec(line))){let y,mo,d;if(m[1]){mo=+m[1]-1;d=+m[2];y=+m[3];if(y<100)y+=2000;if(mo>11){[mo,d]=[d-1,mo+1]}}else if(m[4]){y=+m[4];mo=+m[5]-1;d=+m[6]}else if(m[7]){y=+m[9];mo=MONTHS[m[7].slice(0,3).toLowerCase()];d=+m[8]}else{y=+m[12];mo=MONTHS[m[11].slice(0,3).toLowerCase()];d=+m[10]}
    const dt=new Date(Date.UTC(y,mo,d));if(y>1999&&y<2100&&!isNaN(dt))out.push({d:dt,pre:line.slice(Math.max(0,m.index-42),m.index).toLowerCase()})}return out}
const normN=s=>(' '+String(s||'').toLowerCase().replace(/&/g,' and ').replace(/\b(llc|l\.l\.c|inc|incorporated|corp|corporation|co|ltd|pbc|pllc|lp|the|dba)\b/g,' ').replace(/[^a-z0-9]+/g,' ').trim()+' ');
const keyB=s=>String(s||'').toUpperCase().replace(/[^A-Z0-9]/g,'');
const PANELS=[['pesticides','Pesticides',/pesticide/i,/\b(abamectin|bifenthrin|myclobutanil|imidacloprid|malathion|permethrin|spinosad|chlorpyrifos|acephate|azoxystrobin)\b/i],
  ['heavy_metals','Heavy metals',/heavy metal|elemental impurit|\bmetals\b/i,/^(arsenic|cadmium|lead|mercury)\b/i],
  ['microbials','Microbials',/microbial|microbiolog|\bmicro\b/i,/(salmonella|e\.?\s?coli|stec|shiga|aspergillus|yeast|mold|coliform)/i],
  ['mycotoxins','Mycotoxins',/mycotoxin/i,/(aflatoxin|ochratoxin)/i],
  ['residual_solvents','Residual solvents',/residual solvent|\bsolvents\b/i,/^(butane|propane|ethanol|acetone|hexanes?|heptane|methanol|isopropanol|benzene|toluene|xylenes?|chloroform)\b/i]];
const DEVICES=/\b(lightlab|orange photonics|gemmacert|mydx|purpl|tcheck)\b/i;
const EDITORS=/photoshop|illustrator|indesign|sejda|smallpdf|ilovepdf|pdfescape|pdf-xchange|nitro|foxit (phantom|editor)|acrobat pro|pdffiller|dochub|canva|inkscape|gimp|pixelmator|affinity/i;
const OFFICE=/microsoft.*word|google docs|libreoffice|openoffice|pages|wps/i;
function parse(doc){
  const L=doc.lines,T=L.join('\n'),low=T.toLowerCase();const r={an:{},anHow:{},dates:[],panels:{},fails:[],notes:[]};
  const hdr=L.find(l=>/\bresult\b/i.test(l)&&/\blo[qd]\b/i.test(l));const hasMU=L.some(l=>l.length<80&&/\bMU\b/.test(l));const firstFirst=hdr?hdr.toLowerCase().indexOf('result')<hdr.toLowerCase().search(/\blo[qd]\b/):false;
  for(const l of L){for(const[k,re]of AN){const m=l.match(re);if(!m)continue;const v=rowVal(l.slice(m[0].length),firstFirst,hasMU);if(!v)break;
      const prev=r.anHow[k];if(prev==null||(prev!=='pair'&&v.how==='pair')){r.an[k]=v.pct;r.anHow[k]=v.how||'nd'}break}}
  // per-package / per-serving THC (summary blocks like "per Package 330 mg")
  for(let i=0;i<L.length;i++){const l=L[i];if(/^(?:total\s+(?:active\s+)?)?(?:Δ|∆|delta[-\s]?|d)?9?[-\s]?thc\b/i.test(l)){for(const n of [L[i+1]||'',L[i+2]||'']){const p=n.match(/^per\s+(package|container|unit)\s+([\d.,]+)\s*mg/i),s=n.match(/^per\s+serving\s+([\d.,]+)\s*mg/i);
      if(p&&r.mgPkg==null)r.mgPkg=parseFloat(p[2].replace(',',''));if(s&&r.mgSrv==null)r.mgSrv=parseFloat(s[1].replace(',',''))}}}
  const mc=T.match(/total\s+(?:Δ9-)?thc\s+per\s+(?:container|package|unit)[^\d\n]{0,12}([\d.,]+)\s*mg/i);if(mc&&r.mgPkg==null)r.mgPkg=parseFloat(mc[1].replace(',',''));
  const um=T.match(/unit\s+mass\s*\(g\)\s*:?\s*([\d.]+)/i)||T.match(/net\s+(?:weight|wt\.?)(?:\s+per\s+(?:package|unit))?\s*:?\s*([\d.]+)\s*g\b/i);if(um)r.grams=parseFloat(um[1]);
  const vol=T.match(/volume\s*:?\s*([\d.]+)\s*ml/i),den=T.match(/density\s*:?\s*([\d.]+)\s*g\s*\/\s*ml/i);if(!r.grams&&vol)r.grams=parseFloat(vol[1])*(den?parseFloat(den[1]):1);
  const mo=T.match(/moisture(?:\s+content)?\s*:?\s*(?:[^\n%]{0,40}?\s)?([\d.]+)\s*%/i);if(mo&&+mo[1]<60)r.moisture=parseFloat(mo[1]);
  r.dry=/dry[-\s]weight|dry basis/i.test(T)&&!/as received|wet weight/i.test(T);r.asReceived=/as received|wet weight|sample weight with the applicable moisture|based on a sample weight/i.test(T);
  // dates
  for(const l of L)for(const d of dates(l)){const p=d.pre;d.kind=/expir|best by|use by|calibration|exp\b|exp:/.test(p)?'exp':/(complet|report|tested|analy[sz]|issued|releas|finali[sz]|approv|certif|qa by|date tested)/.test(p)?'test':/(^|\s)date\s*:?\s*$/.test(p)?'date':/(collect|sampl|receiv|order)/.test(p)?'collect':/(produc|manufact|harvest|batch date|packag|born)/.test(p)?'made':'other';r.dates.push(d)}
  const now=TODAY(),ok=r.dates.filter(d=>d.d<=new Date(now.getTime()+DAY));const pick=k=>ok.filter(d=>d.kind===k).sort((a,b)=>b.d-a.d)[0];
  const tdt=pick('test')||pick('date')||pick('collect')||ok.filter(d=>d.kind==='other').sort((a,b)=>b.d-a.d)[0];if(tdt){r.testDate=tdt.d;r.testDateHow=tdt.kind}
  r.future=r.dates.filter(d=>d.kind!=='exp'&&d.d>new Date(now.getTime()+2*DAY)).map(d=>d.d);
  // batch / lot
  const bre=/\b(?:batch|lot)(?:\s*\/\s*lot)?\s*(?:#|no\.?|number|id|code)?\s*(?:\(s\))?\s*[:#]?\s*([A-Za-z0-9][A-Za-z0-9_\-.\/]{0,40})/gi;let bm;
  for(const l of L){bre.lastIndex=0;while((bm=bre.exec(l))){const v=bm[1].replace(/[.,;]$/,'');if(!/\d/.test(v)||/^(date|size|data|weight|complete|lic|type)/i.test(v)||/:$/.test(v)||/^\d{1,2}\/\d{1,2}\/\d{2,4}$/.test(v))continue;if(/(lab|order)\s+batch/i.test(l.slice(Math.max(0,bm.index-6),bm.index+5)))continue;(r.batches=r.batches||[]).includes(v)||(r.batches=r.batches||[]).push(v)}}
  // panels
  for(const[k,nm,re,are]of PANELS){let st=null,rows=0,line=null;for(const l of L){if(are.test(l))rows++;const m=l.match(re);if(!m)continue;const after=l.slice(m.index,m.index+90);
      if(/pass\s*\/\s*fail|pass or fail/i.test(after)&&!/\b(pass|fail)(ed)?\s*$/i.test(after))continue;
      const s=/\bfail(ed)?\b/i.test(after)?'fail':/\bpass(ed)?\b/i.test(after)?'pass':/\bnot\s+tested\b|\bNT\b/.test(after)?'not tested':/\b(complete|tested|ND|not detected|none detected)\b/i.test(after)?'tested':null;
      const rank={fail:4,pass:3,tested:2,'not tested':1};if(s&&(!st||rank[s]>rank[st])){st=s;line=l}}
    if(!st&&rows>=2)st='tested';r.panels[k]={st:st||'missing',line,rows,nm}}
  for(const l of L){const m=l.match(/\bfail(ed|s)?\b/i);if(m&&!/pass\s*\/\s*fail|pass or fail|fail to|failure|pass\/fail|=\s*fail|\bp\/f\b/i.test(l))r.fails.push(l.slice(0,140))}
  r.microHit=L.filter(l=>/(salmonella|stec|shiga|e\.?\s?coli|aspergillus)/i.test(l)&&/\bdetected\b/i.test(l)&&!/not\s+detected|\bND\b|none detected|<\s?1|absent/i.test(l)).slice(0,3);
  // lab
  r.iso=/iso\s*\/?\s*iec\s*17025|iso\s*17025/i.test(T);r.bodies=[...new Set((T.match(/\b(A2LA|ANAB|PJLA|Perry Johnson|IAS|ORELAP|NELAP)\b/g)||[]).map(x=>x==='Perry Johnson'?'PJLA':x))];
  r.certs=[...new Set(T.match(/\b\d{4}\.\d{2}\b/g)||[])];r.licenses=[...new Set((T.match(/\b(C8-\d{7}-LIC|CMTL-\d{4}|405-\d{5}|IL28\d{4}|010-[0-9A-F]{9,})\b/gi)||[]).map(x=>x.toUpperCase()))];
  const st=(L.slice(0,25).join('\n').match(/,\s*([A-Z]{2})\s+\d{5}\b/)||[])[1];r.addrState=st||null;
  r.device=(T.match(DEVICES)||[])[0]||null;
  r.labLine=(()=>{for(const l of L.slice(0,30)){if(/sample|batch|matrix|client|produced|^test\b|lightlab/i.test(l))continue;const m=l.match(/([A-Z][\w&.'’-]*(?:\s+[A-Z&][\w&.'’-]*){0,5}?\s+(?:Lab|Labs|Laboratory|Laboratories|Analytical|Analytics|Testing)\b(?:,?\s+(?:Inc|LLC|Corp)\.?)?)/);if(m)return m[1].trim()}return null})();
  r.name=(()=>{for(const l of L.slice(0,40)){const m=l.match(/^(?:sample|product|item)\s*(?:name|id)?\s*:\s*(.{3,80})/i);if(m){const v=m[1].replace(/\s+(produced|method|matrix|client)\b.*$/i,'').trim();if(/\s/.test(v)&&!/\d/.test(v.split(' ')[0])&&!/^(hemp|flower|edible|concentrate|plant)$/i.test(v))return v}}return null})();
  r.title=L.slice(0,12).find(l=>l.length>3&&l.length<70&&/[a-z]/i.test(l)&&!/:|\b(labs?|laborator\w*|analytic\w*|www|http|lic|license|dea|phone|page|certi\w*|test\w*|batch|summary|llc|inc|warehouse)\b|\(\d{3}\)|,\s*[A-Z]{2}\b/i.test(l)&&!/^\d/.test(l)&&!/^(hemp|extract|ingestion|inhalation|flower|plant|edible|concentrate|topical|sample matrix)$/i.test(l.trim()))||null;
  r.hemp=/\bhemp\b|farm bill|0\.3\s*%/i.test(T);r.inhal=/flower|plant|pre-?roll|vape|cartridge|concentrate|inhal|smok/i.test(T)?true:/edible|gumm|tincture|syrup|beverage|drink|ingest|topical|capsule|chocolate|oral/i.test(T)?false:null;
  r.urls=[...new Set([...(T.match(/https?:\/\/[^\s)]+|www\.[^\s)]+/gi)||[]),...doc.links])];r.verifyText=/scan (?:for|to) (?:authentic|verif)|verify (?:this|at|online)|authentic/i.test(T);
  return r}
// claim from label text (OCR) or product name: "400mg Delta 9", "10 mg THC per piece", "25MG CBD"
function claims(t){const out=[];const re=/(\d{1,5}(?:\.\d+)?)\s*mg[\s_-]*(?:of\s+)?(?:(total\s+)?(Δ|∆|delta|d)?[\s_-]?(9|8|10)?[\s_-]*(thc|cbd)?)/gi;let m;
  while((m=re.exec(t))){const an=m[5]?(m[5].toLowerCase()==='cbd'?'cbd':m[4]==='8'?'d8':m[4]==='9'?'d9':m[2]?'total_thc':'thc'):m[4]==='8'?'d8':m[4]==='9'?'d9':null;if(!an)continue;
    const ctx=t.slice(m.index,m.index+60).toLowerCase();out.push({v:parseFloat(m[1]),unit:/per\s+(piece|serving|gumm|tablet|cap|chew)/.test(ctx)?'mg_srv':'mg_pkg',an,raw:m[0].trim()})}
  const p=t.match(/(\d{1,2}(?:\.\d+)?)\s*%\s*(total\s+)?(thc|cbd)/i);if(p)out.push({v:parseFloat(p[1]),unit:'pct',an:p[3].toLowerCase()==='cbd'?'cbd':'total_thc',raw:p[0]});return out}
// ---------------- rules ----------------
function check(docs,opt,labs){
  const C=[],add=(lv,title,why,src)=>C.push({lv,title,why,src});const coas=docs.filter(d=>d.role==='coa'),lbls=docs.filter(d=>d.role==='label');
  if(!coas.length){add('fail','No lab report (COA) found in what you added','We could not find a certificate of analysis among the files. Without a COA nothing on the label can be checked. Ask the seller for the full COA for this batch.');return{C,read:null}}
  const d=coas[0],r=parse(d);const A=r.an;const today=TODAY();
  const lbT=lbls.map(x=>x.lines.join(' ')).join(' ');const lbP=lbls.length?parse({lines:lbls.flatMap(x=>x.lines),links:[]}):null;
  const hemp=opt.type==='hemp'?true:opt.type==='licensed'?false:r.hemp||null;const inhal=opt.form==='inhaled'?true:opt.form==='other'?false:r.inhal;
  // ---- lab
  const D=labs||{labs:[],accredited:[]};const T=normN(d.lines.join(' '));let lic=null,acc=null;
  for(const l of r.licenses){lic=D.labs.find(x=>x.license&&keyB(x.license)===keyB(l));if(lic)break}
  const byName=arr=>arr.filter(x=>(x.keys||[]).some(k=>k.length>=6&&T.includes(' '+k+' '))).sort((a,b)=>Math.max(...b.keys.map(k=>k.length))-Math.max(...a.keys.map(k=>k.length)))[0];
  if(!lic)lic=byName(D.labs);for(const c of r.certs){acc=D.accredited.find(a=>a.cert===c);if(acc)break}if(!acc)acc=byName(D.accredited);
  const srcOf=id=>(D.sources||[]).find(s=>s.id===id)||{};const labName=(lic&&(lic.dba||lic.name))||(acc&&acc.name)||r.labLine;
  if(r.device&&!lic&&!acc)add('fail','Tested on an in-house device, not by an independent lab',`The report was made with a benchtop potency tester (${r.device}) run by the seller or brand, not by a licensed testing lab. These reports check potency only and are not third-party testing.`);
  else if(lic){const s=srcOf(lic.source),exp=lic.expires?new Date(lic.expires+'T12:00:00Z'):null;
    add(exp&&exp<today?'warn':'ok',`Lab is on the ${lic.state} regulator's list: ${lic.dba||lic.name}`,`${lic.license?'License '+lic.license+' · ':''}${lic.status||'listed'}${exp?' · license through '+fmtD(exp):''}. Matched by ${r.licenses.length&&lic.license&&r.licenses.map(keyB).includes(keyB(lic.license))?'license number':'name'}.`,{label:s.name||lic.state+' regulator',url:lic.url||s.url});
    if(lic.panels){const off=Object.entries(lic.panels).filter(([k,v])=>v&&!/^\d{4}-/.test(v)&&r.panels[k]&&r.panels[k].st!=='missing');if(off.length)add('warn','Lab is not certified by Colorado for some panels on this report',off.map(([k,v])=>`${r.panels[k].nm}: ${v}`).join(' · '),{label:'Colorado MED certifications',url:lic.url})}}
  if(acc){const exp=acc.expires?new Date(acc.expires+'T12:00:00Z'):null;add(exp&&exp<(r.testDate||today)?'warn':'ok',`ISO/IEC 17025 accredited by A2LA: ${acc.name}`,`Certificate ${acc.cert}${exp?', valid through '+fmtD(exp):''}. Scope: ${acc.programs.join(', ')}.`,{label:'A2LA certificate',url:acc.url})}
  else if(r.iso){const b=r.bodies.filter(x=>x!=='A2LA');add('warn','Says ISO 17025 accredited, but we could not confirm it',`The report claims ISO/IEC 17025${b.length?' ('+b.join(', ')+')':''}. We read A2LA's directory and did not find this lab. ANAB and PJLA block automated checks, so look the certificate up yourself.`,{label:b.includes('PJLA')?'PJLA directory':'ANAB directory',url:b.includes('PJLA')?'https://www.pjlabs.com/search-accredited-organizations':'https://search.anab.org/public/'})}
  if(!lic&&!r.device){const cov=(D.counts||{}).states||[];if(!labName)add('fail','No testing lab named on the report','A real COA names the lab, its address and its license or accreditation number.');
    else if(r.addrState&&!cov.includes(r.addrState))add(acc?'info':'warn',`Lab is in ${r.addrState}, a state whose list we do not read yet`,`Named on the report: "${labName}". We check ${cov.join(', ')} regulator lists. Check ${r.addrState}'s regulator or the lab's accreditation certificate.`);
    else add(acc?'info':'fail',`Lab not found on any regulator list we read`,`Named on the report: "${labName}". It is not on the ${cov.join(', ')} license lists${acc?'':' or in the A2LA directory'}. Labs must be licensed to test products for state cannabis markets.`)}
  // ---- potency math
  const thca=A.thca,d9=A.d9,d8=A.d8;const tc=(thca!=null||d9!=null)?(thca||0)*0.877+(d9||0):null;let tot=tc;
  if(tc!=null&&A.total_thc!=null){const diff=Math.abs(A.total_thc-tc),wd8=Math.abs(A.total_thc-tc-(d8||0));
    if(diff<=Math.max(0.03,tc*0.03))add('ok','Total THC math checks out',`THCA ${f2(thca,3)}% × 0.877 + Delta-9 ${f2(d9,3)}% = ${f2(tc,3)}%; the report says ${f2(A.total_thc,3)}%.`,{label:'7 CFR 990.1 (USDA total THC)',url:'https://www.ecfr.gov/current/title-7/subtitle-B/chapter-IX/part-990/subpart-A/section-990.1'});
    else if(d8&&wd8<=Math.max(0.03,tc*0.03))add('info','Lab adds Delta-8 into its Total THC',`The federal formula is THCA × 0.877 + Delta-9 = ${f2(tc,3)}%. The report adds Delta-8 too (${f2(A.total_thc,3)}%).`);
    else add('warn',"Total THC doesn't match the report's own numbers",`THCA ${f2(thca,3)}% × 0.877 + Delta-9 ${f2(d9,3)}% = ${f2(tc,3)}%, but the report prints ${f2(A.total_thc,3)}%. That can be a typo, a different formula, or an edited number.`,{label:'7 CFR 990.1',url:'https://www.ecfr.gov/current/title-7/subtitle-B/chapter-IX/part-990/subpart-A/section-990.1'})}
  if(tot==null&&A.total_thc!=null)tot=A.total_thc;
  const m=r.moisture,dryF=(!r.dry&&m!=null&&m>0&&m<60)?1/(1-m/100):1;const totDry=tot!=null?tot*dryF:null,d9Dry=d9!=null?d9*dryF:null;
  // ---- hemp limits
  const dec11={label:'CRS IF13136 (Dec 11, 2026 hemp rule)',url:'https://www.congress.gov/crs-product/IF13136'};
  if(totDry!=null){const lim=0.3,flower=inhal&&/flower|plant|pre-?roll|bud/i.test(d.lines.join(' '));
    const basis=dryF>1?` (${f2(tot,2)}% as tested, ${f2(totDry,2)}% dry weight at ${f2(m,1)}% moisture)`:'';
    if(totDry>lim){if(hemp===true){if(flower||d9Dry>lim)add('fail','Over the federal hemp THC limit',`Total THC is ${f2(totDry,2)}%${basis}. Hemp must be 0.3% or less. USDA counts THCA in total THC for hemp plants, and from Dec 11, 2026 that applies to all hemp products.`,{label:'7 CFR 990.1',url:'https://www.ecfr.gov/current/title-7/subtitle-B/chapter-IX/part-990/subpart-A/section-990.1'});
        else add('warn','Over the new hemp limit that starts Dec 11, 2026',`Delta-9 is ${f2(d9Dry,3)}% dry weight (under 0.3%), but total THC including THCA is ${f2(totDry,2)}%${basis}. From Dec 11, 2026 that is not hemp under federal law.`,dec11)}
      else add(hemp===false?'info':'warn',hemp===false?'High THC: fine for a state-licensed product':'THC is far above the hemp limit',`Total THC is ${f2(totDry,2)}%${basis}. ${hemp===false?'That is normal for licensed cannabis.':'If this is sold as hemp (online, smoke shops, gas stations) it is over the 0.3% federal limit. It is only legal as state-licensed cannabis.'}`,{label:'7 CFR 990.1',url:'https://www.ecfr.gov/current/title-7/subtitle-B/chapter-IX/part-990/subpart-A/section-990.1'})}
    else if(hemp!==false)add('ok','Under 0.3% total THC by dry weight',`Total THC ${f2(totDry,3)}%${dryF>1?' dry weight':''}.`,{label:'7 CFR 990.1',url:'https://www.ecfr.gov/current/title-7/subtitle-B/chapter-IX/part-990/subpart-A/section-990.1'})}
  let mgPkg=r.mgPkg;if(mgPkg==null&&r.grams&&tot!=null)mgPkg=+(tot*10*r.grams).toFixed(1);
  if(hemp!==false&&mgPkg!=null&&mgPkg>0.4)add('warn','Will not count as hemp after Dec 11, 2026',`This package has about ${f2(mgPkg,1)} mg THC. From Dec 11, 2026, a final hemp product with more than 0.4 mg total THC per container is excluded from the federal hemp definition.`,dec11);
  const syn=['hhc','thco','thcp','d10'].filter(k=>A[k]>0);if(syn.length||d8>0.05)add('info','Contains converted or rare cannabinoids',`${[...(d8>0.05?['Delta-8 THC '+f2(d8,3)+'%']:[]),...syn.map(k=>ANL[k]+' '+f2(A[k],3)+'%')].join(', ')}. These are usually made by converting CBD. From Nov 12, 2026 cannabinoids the plant cannot make naturally, or that are made outside the plant, are excluded from federal hemp.`,dec11);
  // ---- label vs COA
  let cl=null;if(opt.claim&&opt.claim.v>0)cl=Object.assign({from:'what you entered'},opt.claim);
  if(!cl){const c=claims(lbT)[0];if(c)cl=Object.assign({from:'the label photo'},c)}
  if(!cl){const nm=[r.name,r.title,...(r.batches||[])].filter(Boolean).join(' ');const c=claims(nm.replace(/_/g,' '))[0];if(c)cl=Object.assign({from:'the product name on the report'},c)}
  const nameT=[r.name,r.title,...(r.batches||[]),lbT].filter(Boolean).join(' ');
  const saysD8=/(Δ|∆|delta|\bd)[\s_-]?8\b/i.test(nameT),saysD9=/(Δ|∆|delta|\bd)[\s_-]?9\b/i.test(nameT);
  if(saysD8&&d8!=null&&d8<0.01&&(d9||0)>0.01)add('fail','Sold as Delta-8, but the lab found Delta-9, not Delta-8',`Delta-8 ${d8?f2(d8,3)+'%':'not detected'}; Delta-9 ${f2(d9,3)}%.`);
  else if(saysD9&&!saysD8&&(d8||0)>(d9||0)*2&&d8>0.05)add('fail','Sold as Delta-9, but it is mostly Delta-8',`Delta-8 ${f2(d8,3)}%; Delta-9 ${f2(d9,3)}%.`);
  else if((saysD8||saysD9)&&(d8!=null||d9!=null))add('ok',`The ${saysD8?'Delta-8':'Delta-9'} on the name matches what the lab found`,`Delta-9 ${d9!=null?f2(d9,3)+'%':'not reported'} · Delta-8 ${d8!=null?(d8?f2(d8,3)+'%':'not detected'):'not reported'}.`);
  if(cl){const an=cl.an==='thc'?(A.total_thc!=null||tc!=null?'total_thc':'d9'):cl.an;let got=null,unit='';
    if(cl.unit==='pct'){got=an==='total_thc'?tot:A[an];unit='%'}else if(cl.unit==='mg_srv'){got=r.mgSrv!=null&&/thc|d9/.test(an)?r.mgSrv:null;unit=' mg per serving'}else{got=(/thc|d9|d8/.test(an)&&r.mgPkg!=null)?r.mgPkg:(r.grams&&A[an]!=null)?A[an]*10*r.grams:an==='total_thc'?mgPkg:null;unit=' mg per package'}
    if(got==null)add('info',`Label claim ${cl.v}${unit.replace(' per package',' ').trim()?unit:''} ${ANL[an]||an}: could not compare`,`We could not find a matching ${unit.trim()||'number'} on the report. Compare it by hand.`);
    else{const pd=(got-cl.v)/cl.v*100,ad=Math.abs(pd);
      add(ad>15?'fail':ad>10?'warn':'ok',ad<=10?`Potency matches the label (${pd>=0?'+':''}${f2(pd,1)}%)`:`Potency is ${f2(ad,1)}% ${pd<0?'below':'above'} the label`,`Claim from ${cl.from}: ${f2(cl.v,2)}${unit} ${ANL[an]||an}. The lab found ${f2(got,2)}${unit}. Within 10% is a match; over 15% is a fail here (many states allow ±10–15%).`)}}
  else add('info','No label claim to compare','Add the potency printed on the package (or a label photo) to check it against the report.');
  // ---- safety panels
  const need=['pesticides','heavy_metals','microbials','mycotoxins'].concat(inhal===false&&!/extract|concentrate|vape|distillate|oil/i.test(d.lines.join(' '))?[]:['residual_solvents']);
  const P=r.panels,fl=need.filter(k=>P[k].st==='fail'),miss=need.filter(k=>P[k].st==='missing'||P[k].st==='not tested'),okp=need.filter(k=>P[k].st==='pass'||P[k].st==='tested');
  if(fl.length)add('fail',`Failed: ${fl.map(k=>P[k].nm).join(', ')}`,`The lab marked ${fl.length>1?'these panels':'this panel'} as failed: "${P[fl[0]].line.slice(0,120)}"`);
  if(r.microHit.length)add('fail','A harmful microbe was detected',r.microHit[0].slice(0,140)+'. California requires Salmonella and STEC E. coli to be not detected in 1 g.',{label:'4 CCR § 15720',url:'https://www.law.cornell.edu/regulations/california/4-CCR-15720'});
  if(miss.length===need.length)add('warn','Potency only: no safety testing on this report',`We found no ${need.map(k=>P[k].nm.toLowerCase()).join(', ')} results. A full-panel COA shows these. Ask the seller for it.`,{label:'California required tests (4 CCR § 15719–15723)',url:'https://www.law.cornell.edu/regulations/california/4-CCR-15723'});
  else if(miss.length)add('warn',`Missing panels: ${miss.map(k=>P[k].nm).join(', ')}`,`The report has ${okp.map(k=>P[k].nm.toLowerCase()).join(', ')||'other'} results but not these.`);
  if(okp.length)add('ok',`${okp.length===need.length?'All safety panels':'Some panels'} reported: ${okp.map(k=>P[k].nm+(P[k].st==='pass'?' (pass)':' (results shown)')).join(', ')}`,okp.some(k=>P[k].st==='tested')?'Where no pass/fail is printed we only confirm the results are there. Compare them with the limits below.':'As marked by the lab.');
  const other=r.fails.filter(l=>!need.some(k=>PANELS.find(p=>p[0]===k)[2].test(l)));if(other.length&&!fl.length)add('fail','The report shows a FAIL',`"${other[0]}"`);
  // ---- test date
  if(r.testDate){const age=Math.floor((today-r.testDate)/DAY),mo=Math.round(age/30.4);const how=r.testDateHow==='test'?'Tested/reported':r.testDateHow==='date'?'Report date':r.testDateHow==='collect'?'Sampled':'Newest date on report';
    add(age>365?'fail':age>180?'warn':'ok',age>365?`Test is over a year old (${fmtD(r.testDate)})`:age>180?`Test is ${mo} months old`:`Recent test (${fmtD(r.testDate)})`,`${how}: ${fmtD(r.testDate)}, ${age} days ago. Products change between batches, so an old report may not describe what you are buying.`)}
  else add('warn','No test date found','A COA should show when the sample was collected and when results were reported.');
  if(r.future.length)add('warn','The report has a date in the future',`${fmtD(r.future[0])}. That can be a typo or an edit.`);
  // ---- batch
  const want=(opt.batch||'').trim()||((lbP&&lbP.batches)||[])[0]||'';
  if(!(r.batches||[]).length)add('warn','No batch or lot number on the report','Without a batch number you cannot tell whether this report belongs to the package in your hand.');
  else if(want){const w=keyB(want),src=`Package: ${want}${(opt.batch||'').trim()?'':' (read from the label photo)'} · report: ${r.batches.join(', ')}.`;
    const full=r.batches.some(b=>keyB(b)===w||(w.length>=6&&(keyB(b).includes(w)||w.includes(keyB(b)))&&Math.min(w.length,keyB(b).length)/Math.max(w.length,keyB(b).length)>=0.6));
    const part=!full&&r.batches.some(b=>w.length>=4&&(keyB(b).includes(w)||w.includes(keyB(b))));
    if(full)add('ok','Batch matches the package',src);else if(part)add('warn','Batch only partly matches',src+' Compare the full number on the package by eye.');else add('fail','Batch on the package is not on this report',src)}
  else add('info',`Report batch: ${r.batches.join(', ')}`,'Check that the same number is printed on your package.');
  // ---- verification + edits
  const q=[...new Set(coas.flatMap(x=>x.qr))];
  if(q.length)add('ok','Has a QR code',`It opens: ${q[0].slice(0,120)}. Open it and make sure it goes to the lab's own website and shows the same numbers.`,/^https?:/i.test(q[0])?{label:'Open the QR link (leaves this site)',url:q[0]}:null);
  else if(r.urls.some(u=>/coa|verify|lims|report|result|portal|qr/i.test(u)))add('info','No QR code read, but there is a verification link',r.urls.filter(u=>/coa|verify|lims|report|result|portal|qr/i.test(u))[0].slice(0,120));
  else add('warn','No QR code or verification link found',r.verifyText?'The report mentions a scan-to-verify code, but we could not read one. Scan it with your phone and check it opens the lab\'s site.':'Most real lab reports have a QR code or link that opens the original on the lab\'s website.');
  const I=d.info||{},prod=[I.Producer,I.Creator].filter(Boolean).join(' / ');const pd=s=>{const m=String(s||'').match(/D:(\d{4})(\d\d)(\d\d)(\d\d)?(\d\d)?/);return m?new Date(Date.UTC(+m[1],m[2]-1,+m[3],+(m[4]||0),+(m[5]||0))):null};
  const cd=pd(I.CreationDate),md=pd(I.ModDate);const edits=[];
  if(EDITORS.test(prod))edits.push(`the file was last saved by an editing tool (${prod})`);
  if(cd&&md&&md-cd>DAY)edits.push(`it was modified ${Math.round((md-cd)/DAY)} days after it was created`);
  if(d.items&&d.items.length){ // a result number in a different font from the other numbers on the SAME table row
    const rows={};d.items.forEach(i=>{if(/^[<>]?\d+(\.\d+)?%?$/.test(i.s.trim())&&AN.some(([,re])=>re.test(i.line))&&!/^(total|sum of)/i.test(i.line))(rows[i.line]=rows[i.line]||[]).push(i)});
    const cnt={};Object.values(rows).flat().forEach(i=>cnt[i.f]=(cnt[i.f]||0)+1);const odd=[];
    Object.values(rows).forEach(r=>{if(r.length<3)return;const fc={};r.forEach(i=>fc[i.f]=(fc[i.f]||0)+1);const main=Object.entries(fc).sort((a,b)=>b[1]-a[1])[0][0];r.forEach(i=>{if(i.f!==main&&fc[i.f]===1&&cnt[i.f]<=2)odd.push(i.s)})});
    if(odd.length)edits.push(`${odd.length===1?'one result number uses':'a few result numbers use'} a different font from the rest of its row (${odd.slice(0,3).join(', ')})`)}
  const ovl=d.overlaps||[];
  if(ovl.length)add('fail','A number on the report is printed on top of another number',`We found ${ovl.slice(0,3).map(([top,under])=>`"${top}" drawn over "${under}"`).join(', ')}. Lab software does not do this; it is what a cover-and-retype edit leaves behind. We read the top value. Get the report from the lab or its QR link.${edits.length?' Also: '+edits.join('; ')+'.':''}`);
  else if(edits.length)add(edits.length>=2?'fail':'warn',edits.length>=2?'Several signs the file was edited':'Signs the file may have been edited',edits.join('; ')+'. This is a hint, not proof: ask the lab to confirm.');
  else if(d.kind==='pdf')add('ok','No signs of editing in the file','We checked the PDF\'s tool and dates and the fonts of the result numbers. This cannot rule out every edit.');
  else add('info','Photo: edits cannot be checked','A photo or screenshot hides how the report was made. Get the PDF from the lab or the QR link.');
  if(d.ocr)add('info','Read with OCR','Some text was read from an image, so numbers may be misread. Check the key numbers by eye.');
  const read={lab:labName,labState:(lic&&lic.state)||r.addrState,licenses:r.licenses,product:r.name||r.title,batches:r.batches||[],testDate:r.testDate,an:A,tc,tot,totDry,moisture:m,mgPkg,mgSrv:r.mgSrv,claim:cl,hemp,inhal,panels:r.panels,qr:q,producer:prod};
  return{C,read}}
// ---------------- UI ----------------
const IC={fail:'✕',warn:'!',ok:'✓',info:'i'};
function verdict(C){const n=k=>C.filter(c=>c.lv===k).length;const f=n('fail'),w=n('warn');
  return f?{cls:'red',t:"Don't rely on this product yet",s:`${f} problem${f>1?'s':''}${w?` and ${w} thing${w>1?'s':''} to check`:''}`}:w?{cls:'amber',t:'Check these things before you buy',s:`${w} thing${w>1?'s':''} to check · ${n('ok')} checks passed`}:{cls:'green',t:'This report looks consistent',s:`${n('ok')} checks passed`}}
function limitsHtml(L){const l=(L&&L.limits)||[];const m=l.find(x=>x.id==='ca_metals'),y=l.find(x=>x.id==='ca_myco');if(!m)return'';
  const row=(k,n)=>`<tr><td>${n}</td><td class="num">${m.inhalable[k]}</td><td class="num">${m.non_inhalable[k]}</td></tr>`;
  return`<details class="pc-lim"><summary>Reference limits we use (California, the strictest common standard)</summary><table class="pc-tb"><thead><tr><th>Heavy metal (µg/g)</th><th>Smoked/vaped</th><th>Other</th></tr></thead><tbody>${row('cadmium','Cadmium')}${row('lead','Lead')}${row('arsenic','Arsenic')}${row('mercury','Mercury')}</tbody></table>
   <p class="dim">Mycotoxins: total aflatoxins B1+B2+G1+G2 ≤ ${y?y.all.total_aflatoxins:20} µg/kg, ochratoxin A ≤ ${y?y.all.ochratoxin_a:20} µg/kg. Microbes: no Salmonella or STEC E. coli in 1 g; for smoked or vaped products, no Aspergillus fumigatus, flavus, niger or terreus in 1 g.</p>
   <p class="pc-src">${l.map(x=>`<a href="${E(x.url.replace('/api/renderer/v1/content/enhanced/current/title-7?part=990&section=990.1','/current/title-7/subtitle-B/chapter-IX/part-990/subpart-A/section-990.1'))}" target="_blank" rel="noopener">${E(x.cite)}</a> <span class="dim">(${E(x.status)} ${E(x.verified||'')})</span>`).join(' · ')}</p></details>`}
function render(res,docs){const v=verdict(res.C),R=res.read,ord={fail:0,warn:1,ok:2,info:3};const C=[...res.C].sort((a,b)=>ord[a.lv]-ord[b.lv]);
  const an=R?Object.entries(R.an).filter(([k,x])=>x!=null).map(([k,x])=>`${ANL[k]} ${x?f2(x,3)+'%':'ND'}`).join(' · '):'';
  return`<div class="pc-verdict v-${v.cls}"><span class="pc-vi" aria-hidden="true">${v.cls==='red'?'✕':v.cls==='amber'?'!':'✓'}</span><div><b>${E(v.t)}</b><small>${E(v.s)}</small></div></div>
  <ol class="pc-checks">${C.map(c=>`<li class="c-${c.lv}"><span class="ci" aria-label="${c.lv}">${IC[c.lv]}</span><div><b>${E(c.title)}</b><p>${E(c.why)}${c.src&&c.src.url?` <a href="${E(c.src.url)}" target="_blank" rel="noopener">${E(c.src.label)}</a>`:''}</p></div></li>`).join('')}</ol>
  ${R?`<details class="pc-readout"><summary>What we read from the report</summary><dl class="kv"><dt>Files</dt><dd>${docs.map(d=>E(d.name)+' ('+(d.role==='coa'?'lab report':'label')+(d.ocr?', OCR':'')+')').join(', ')}</dd><dt>Lab</dt><dd>${E(R.lab||'not found')}${R.labState?' · '+E(R.labState):''}${R.licenses.length?' · '+E(R.licenses.join(', ')):''}</dd>
  <dt>Product</dt><dd>${E(R.product||'?')}</dd><dt>Batch</dt><dd>${E(R.batches.join(', ')||'none')}</dd><dt>Test date</dt><dd>${E(fmtD(R.testDate))}</dd><dt>Cannabinoids</dt><dd>${E(an||'none found')}</dd>
  <dt>Total THC</dt><dd>${R.tot!=null?E(f2(R.tot,3)+'%'+(R.totDry!=null&&R.totDry!==R.tot?' · '+f2(R.totDry,3)+'% dry weight':'')):'?'}${R.mgPkg!=null?' · '+E(f2(R.mgPkg,1))+' mg per package':''}</dd><dt>File made by</dt><dd>${E(R.producer||'not stated')}</dd></dl></details>`:''}
  ${limitsHtml(LABS)}
  <p class="pc-disc"><b>Not medical or legal advice.</b> This is an automated reading of the files you chose, checked against public lists and rules. It can misread a report and cannot prove a report is genuine. Confirm with the lab, and check your state's rules before you buy or use cannabis or hemp. 21+.</p>`}
function empty(){const L=LABS,c=L&&L.counts;return`<div class="pc-empty"><b>What it checks</b><ol>
  <li>Label potency vs the report (within 10% passes, over 15% fails)</li><li>Total THC = THCA × 0.877 + Delta-9, and dry weight vs the 0.3% hemp limit</li><li>Delta-8 vs Delta-9: does the lab find what the label says?</li><li>Pass/fail on pesticides, heavy metals, microbes, mycotoxins and residual solvents, and missing panels</li>
  <li>How old the test is, and whether the batch number matches your package</li><li>Whether the lab is licensed by a state regulator or ISO 17025 accredited</li><li>Red flags: no QR code or link, signs of an edited PDF, totals that don't add up, the Dec 11, 2026 hemp rule</li></ol>
  <p class="dim">${c?`Lab lists: ${c.state_labs} licensed labs (${c.states.join(', ')}) and ${c.accredited} A2LA-accredited labs, updated ${E(L.generated)}. `:''}<a href="/terminal/data/labs.json">See the data</a></p></div>`}
function ui(){const app=document.getElementById('pc-app');if(!app)return;let files=[];
  app.innerHTML=`<div class="pc-grid"><div class="pc-in">
   <label class="pc-drop" for="pc-file"><b>Add a COA or a label photo</b><span>PDF, JPG or PNG. Add both for the best check.</span><span class="pc-btn">Choose files</span><input id="pc-file" type="file" accept="application/pdf,image/*" multiple></label>
   <ul class="pc-files" id="pc-files"></ul>
   <details class="pc-more"><summary>What does the package say? (optional)</summary><div class="pc-f">
    <label>Sold as<select id="pc-type"><option value="">Not sure</option><option value="hemp">Hemp (online, smoke shop, gas station)</option><option value="licensed">State-licensed dispensary</option></select></label>
    <label>Used by<select id="pc-form"><option value="">Not sure</option><option value="inhaled">Smoking or vaping</option><option value="other">Eating, drinking or on skin</option></select></label>
    <label>Label potency<span class="pc-row"><input id="pc-cv" type="number" min="0" step="any" inputmode="decimal" placeholder="e.g. 10"><select id="pc-cu"><option value="mg_pkg">mg per package</option><option value="mg_srv">mg per serving</option><option value="pct">%</option></select><select id="pc-ca"><option value="total_thc">Total THC</option><option value="d9">Delta-9 THC</option><option value="d8">Delta-8 THC</option><option value="cbd">CBD</option></select></span></label>
    <label>Batch or lot on the package<input id="pc-batch" type="text" autocomplete="off" placeholder="e.g. B-2311"></label></div></details>
   <div class="pc-act"><button class="btn" id="pc-go" type="button" disabled>Check product</button><button class="btn ghost" id="pc-clear" type="button">Clear</button></div>
   <p class="pc-priv">Files stay on this device. They are read inside this browser tab, never uploaded or saved, and gone when you press Clear or leave. Text-reading tools load from jsDelivr the first time.</p>
   <p class="pc-say" id="pc-say" aria-live="polite"></p></div><div class="pc-out" id="pc-out" aria-live="polite">${empty()}</div></div>`;
  const $=id=>document.getElementById(id),inp=$('pc-file'),go=$('pc-go'),say=t=>$('pc-say').textContent=t;
  const list=()=>{$('pc-files').innerHTML=files.map((f,i)=>`<li><span>${f.type==='application/pdf'?'📄':'🖼️'} ${E(f.name)}</span><button type="button" data-rm="${i}" aria-label="Remove ${E(f.name)}">Remove</button></li>`).join('');go.disabled=!files.length};
  inp.addEventListener('change',()=>{files=files.concat([...inp.files]).slice(0,6);inp.value='';list()});
  $('pc-files').addEventListener('click',e=>{const b=e.target.closest('[data-rm]');if(b){files.splice(+b.dataset.rm,1);list()}});
  const drop=app.querySelector('.pc-drop');['dragover','dragenter'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.add('on')}));['dragleave','drop'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.remove('on')}));
  drop.addEventListener('drop',e=>{files=files.concat([...e.dataTransfer.files].filter(f=>/pdf|image/.test(f.type))).slice(0,6);list()});
  $('pc-clear').addEventListener('click',()=>{files=[];list();['pc-cv','pc-batch'].forEach(i=>$(i).value='');['pc-type','pc-form'].forEach(i=>$(i).value='');say('');$('pc-out').innerHTML=empty();window.__pc=null});
  go.addEventListener('click',async()=>{go.disabled=true;const t0=Date.now();try{await labsP();const docs=[];
      for(const f of files){say(`Opening ${f.name}…`);const d=f.type==='application/pdf'||/\.pdf$/i.test(f.name)?await readPdf(f,say):await readImage(f,say);d.role=isCOA(d)?'coa':'label';docs.push(d)}
      docs.sort((a,b)=>(a.role==='coa'?0:1)-(b.role==='coa'?0:1)||(a.kind==='pdf'?0:1)-(b.kind==='pdf'?0:1));
      const cv=parseFloat($('pc-cv').value);const opt={type:$('pc-type').value,form:$('pc-form').value,batch:$('pc-batch').value,claim:cv>0?{v:cv,unit:$('pc-cu').value,an:$('pc-ca').value}:null};
      const res=check(docs,opt,LABS);window.__pc={res,docs:docs.map(d=>({name:d.name,role:d.role,kind:d.kind,ocr:d.ocr,qr:d.qr,lines:d.lines.length}))};
      $('pc-out').innerHTML=render(res,docs);say(`Checked in ${((Date.now()-t0)/1000).toFixed(1)} s. Nothing was uploaded.`);
      if(matchMedia('(max-width:860px)').matches)$('pc-out').scrollIntoView({block:'start',behavior:'smooth'})}
    catch(e){say('Could not read that file: '+e.message+'. Try a PDF from the lab, or a sharper photo.')}finally{go.disabled=!files.length}});
  labsP().then(L=>{if(!L)return;const m=document.getElementById('pc-meta');if(m)m.textContent=`${L.counts.state_labs} licensed + ${L.counts.accredited} accredited labs · in your browser`;if(!window.__pc)$('pc-out').innerHTML=empty()})}
window.TGProduct={parse,check,claims,rowVal,linesFromItems,readPdf};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ui);else ui();
})();
