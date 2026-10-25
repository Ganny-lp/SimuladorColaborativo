const JSONBIN_API_KEY = __JSONBIN_API_KEY__;
const JSONBIN_BIN_ID  = __JSONBIN_BIN_ID__;
let SYS = __MODEL_JSON__;

// ── State ──
let selNode=null, lkSrc=null, curTool='select';
let isDrag=false, dragNode=null, dragOX=0, dragOY=0;
let panX=60,panY=60,scale=.75,isPan=false,panSX=0,panSY=0;
let saveTimer=null, isMobile=false;

const CAT_CLS={Estado:'cat-estado',Equação:'cat-equacao',Parâmetro:'cat-parametro',Ambiente:'cat-ambiente',Input:'cat-input'};
const CAT_FG={Estado:'fg-estado',Equação:'fg-equacao',Parâmetro:'fg-parametro',Ambiente:'fg-ambiente',Input:'fg-input'};

// ── Save / Load manual ──
function setInd(cls,msg){const e=document.getElementById('save-ind');e.className=cls;e.textContent=msg;}

async function manualSave(){
  if(!JSONBIN_API_KEY||!JSONBIN_BIN_ID){setInd('error','sem credenciais');return;}
  setInd('saving','salvando…');
  try{
    const r=await fetch(`https://api.jsonbin.io/v3/b/${JSONBIN_BIN_ID}`,{method:'PUT',headers:{'Content-Type':'application/json','X-Master-Key':JSONBIN_API_KEY},body:JSON.stringify(SYS)});
    if(r.ok){setInd('saved','salvo');setTimeout(()=>setInd('','pronto'),2500);}
    else setInd('error','erro '+r.status);
  }catch{setInd('error','sem conexão');}
}

async function refreshFromCloud(){
  if(!JSONBIN_API_KEY||!JSONBIN_BIN_ID){alert('Credenciais não configuradas.');return;}
  setInd('saving','carregando…');
  try{
    const r=await fetch(`https://api.jsonbin.io/v3/b/${JSONBIN_BIN_ID}/latest`,{headers:{'X-Master-Key':JSONBIN_API_KEY}});
    if(r.ok){
      const data=await r.json();
      if(data.record && data.record.nodes){
        SYS = data.record;
        selNode=null; lkSrc=null;
        renderAll();
        setInd('saved','recarregado');
        setTimeout(()=>setInd('','pronto'),2500);
      } else throw new Error();
    } else throw new Error();
  }catch{setInd('error','falha');}
}

// ── Zoom ──
function upZoom(){document.getElementById('zoom-chip').textContent=Math.round(scale*100)+'%';}
function applyXform(){document.getElementById('cld-canvas').style.transform=`translate(${panX}px,${panY}px) scale(${scale})`; upZoom(); requestAnimationFrame(renderEdges);}
function setScale(ns,cx,cy){
  const w=document.getElementById('canvas-wrap');
  const mx=cx??w.clientWidth/2, my=cy??w.clientHeight/2;
  panX=mx-(mx-panX)*(ns/scale); panY=my-(my-panY)*(ns/scale); scale=ns;
  applyXform();
}
function zoomIn(){setScale(Math.min(2.5,scale*1.15));}
function zoomOut(){setScale(Math.max(.25,scale*.87));}
function zoomReset(){scale=.75;panX=60;panY=60;applyXform();renderAll();}

// ── Render nodes ──
function renderAll(){
  const cv=document.getElementById('cld-canvas');
  cv.innerHTML='';
  cv.style.transformOrigin='0 0';
  cv.style.transform=`translate(${panX}px,${panY}px) scale(${scale})`;
  for(const[id,nd] of Object.entries(SYS.nodes)){
    const el=document.createElement('div');
    el.className='cld-node';
    el.id='node-'+id;
    el.style.left=nd.x+'px';
    el.style.top=nd.y+'px';
    el.innerHTML=`<div class="node-box ${CAT_CLS[nd.cat]||'cat-estado'}">${id}</div>`;
    if(selNode===id) el.classList.add('selected');
    if(lkSrc===id)  el.classList.add('lk-src');
    el.addEventListener('mousedown', e=>onNDown(e,id));
    el.addEventListener('touchstart',e=>{e.preventDefault();onNDown(e,id);},{passive:false});
    el.addEventListener('click',     e=>onNClick(e,id));
    el.addEventListener('touchend',  e=>{e.preventDefault();onNClick(e,id);});
    cv.appendChild(el);
  }
  requestAnimationFrame(renderEdges);
  upZoom();
}

// ── Render edges ──
function renderEdges(){
  const svg=document.getElementById('cld-svg');
  const wrap=document.getElementById('canvas-wrap');
  const W=wrap.clientWidth, H=wrap.clientHeight;
  if(W===0||H===0){setTimeout(renderEdges,50);return;}
  svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  svg.setAttribute('width',W);
  svg.setAttribute('height',H);
  svg.innerHTML=`<defs>
    <marker id="a+" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M1 2L9 5L1 8" fill="none" style="stroke:var(--green)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
    <marker id="a-" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M1 2L9 5L1 8" fill="none" style="stroke:var(--coral)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>`;
  for(const lk of SYS.links){
    const fn=SYS.nodes[lk.from], tn=SYS.nodes[lk.to];
    if(!fn||!tn) continue;
    const fEl=document.getElementById('node-'+lk.from);
    const tEl=document.getElementById('node-'+lk.to);
    if(!fEl||!tEl) continue;
    const fx=fn.x*scale+panX, fy=fn.y*scale+panY;
    const tx=tn.x*scale+panX, ty=tn.y*scale+panY;
    const fw=fEl.offsetWidth*scale, fh=fEl.offsetHeight*scale;
    const tw=tEl.offsetWidth*scale, th=tEl.offsetHeight*scale;
    const dx=tx-fx, dy=ty-fy, dist=Math.hypot(dx,dy)||1;
    const ux=dx/dist, uy=dy/dist;
    const x1=fx+ux*Math.min(fw/2+2,Math.abs(fw/2/ux)||fw/2);
    const y1=fy+uy*Math.min(fh/2+2,Math.abs(fh/2/uy)||fh/2);
    const x2=tx-ux*Math.min(tw/2+6,Math.abs(tw/2/ux)||tw/2);
    const y2=ty-uy*Math.min(th/2+6,Math.abs(th/2/uy)||th/2);
    const cx=(x1+x2)/2-uy*20, cy=(y1+y2)/2+ux*20;
    const col=lk.sign==='+'?'var(--green)':'var(--coral)';
    const p=document.createElementNS('http://www.w3.org/2000/svg','path');
    p.setAttribute('d',`M${x1},${y1} Q${cx},${cy} ${x2},${y2}`);
    p.setAttribute('fill','none');p.style.stroke=col;
    p.setAttribute('stroke-width','1.5');p.setAttribute('stroke-opacity','.65');
    p.setAttribute('marker-end',`url(#a${lk.sign})`);
    const t=document.createElementNS('http://www.w3.org/2000/svg','text');
    t.setAttribute('x',cx);t.setAttribute('y',cy-5);
    t.setAttribute('text-anchor','middle');t.setAttribute('font-size','11');
    t.setAttribute('font-family','DM Mono,monospace');t.setAttribute('font-weight','700');
    t.style.fill=col;t.setAttribute('opacity','.95');
    t.textContent=lk.sign;
    svg.appendChild(p);svg.appendChild(t);
  }
}

// ── ResizeObserver: re-render edges when canvas-wrap changes size ──
const _ro=new ResizeObserver(()=>{requestAnimationFrame(renderEdges);});
_ro.observe(document.getElementById('canvas-wrap'));

// ── Pointer helpers ──
function pxy(e){
  if(e.touches&&e.touches.length>0) return[e.touches[0].clientX,e.touches[0].clientY];
  if(e.changedTouches&&e.changedTouches.length>0) return[e.changedTouches[0].clientX,e.changedTouches[0].clientY];
  return[e.clientX,e.clientY];
}

function onNDown(e,id){
  if(curTool!=='select') return;
  e.stopPropagation();
  isDrag=false;dragNode=id;
  const[cx,cy]=pxy(e);
  const r=document.getElementById('canvas-wrap').getBoundingClientRect();
  dragOX=(cx-r.left-panX)/scale-SYS.nodes[id].x;
  dragOY=(cy-r.top-panY)/scale-SYS.nodes[id].y;
}

function onNClick(e,id){
  if(isDrag) return;
  e.stopPropagation();
  if(curTool==='link'){
    if(!lkSrc){
      lkSrc=id;
      document.getElementById('node-'+id)?.classList.add('lk-src');
      document.getElementById('link-hint').textContent=`Origem: "${id}" — selecione o destino abaixo.`;
      document.getElementById('lk-from').value=id;
      fillLinkTo(id);
      openModal('modal-link');
    }else if(lkSrc!==id){
      document.getElementById('lk-to').value=id;
      confirmLink();
    }
    return;
  }
  selectNode(id);
}

function selectNode(id){
  document.querySelectorAll('.cld-node').forEach(e=>e.classList.remove('selected'));
  selNode=id;
  document.getElementById('node-'+id)?.classList.add('selected');
  const html=buildDetail(id);
  document.getElementById('panel-content').innerHTML=html;
  document.getElementById('sheet-body').innerHTML=html;
  document.getElementById('fab').classList.add('node-sel');
  if(isMobile) openSheet();
}

function deselect(){
  document.querySelectorAll('.cld-node').forEach(e=>e.classList.remove('selected'));
  selNode=null;
  const ph='<div class="ph"><span class="mark ico" role="img" aria-label=""><i></i><b></b></span><p>Clique em um nó para ver seus detalhes.</p></div>';
  document.getElementById('panel-content').innerHTML=ph;
  document.getElementById('sheet-body').innerHTML=ph;
  document.getElementById('fab').classList.remove('node-sel');
}

function fillLinkTo(excl){
  document.getElementById('lk-to').innerHTML=
    Object.keys(SYS.nodes).filter(n=>n!==excl).map(n=>`<option value="${n}">${n}</option>`).join('');
}

// ── Detail builder ──
function buildDetail(id){
  const nd=SYS.nodes[id]; if(!nd) return '';
  const out=SYS.links.filter(l=>l.from===id);
  const inc=SYS.links.filter(l=>l.to===id);
  const fgCls=CAT_FG[nd.cat]||'';
  const fmtVal=v=>typeof v==='number'?v.toPrecision(6).replace(/(\.\d*?)0+$/,'$1').replace(/\.$/,''):v;
  let h=`<div class="dn-name">${id}</div><div class="dn-cat ${fgCls}">${nd.cat}</div>`;
  h+=`<div class="dl">Descrição</div><div class="dd">${nd.desc||'—'}</div>`;
  h+=`<div class="dl">Valor Atual</div><div class="dv">${fmtVal(nd.val)}</div>`;
  if(nd.expr) h+=`<div class="dl">Equação</div><div class="deq">${nd.expr}</div>`;
  if(inc.length){
    h+=`<div class="dl">Causas (${inc.length})</div>`;
    inc.forEach(l=>h+=`<div class="rel-row"><span class="rsgn ${l.sign==='+'?'rpos':'rneg'}">${l.sign}</span><span style="color:var(--text2)">${l.from}</span></div>`);
  }
  if(out.length){
    h+=`<div class="dl">Efeitos (${out.length})</div>`;
    out.forEach(l=>h+=`<div class="rel-row"><span class="rsgn ${l.sign==='+'?'rpos':'rneg'}">${l.sign}</span><span style="color:var(--text2)">${l.to}</span></div>`);
  }
  h+=`<div class="dact">
    <button class="bi" onclick="openEditModal('${id}')"><svg class="ic" aria-hidden="true"><use href="#i-pencil"/></svg>Editar</button>
    <button class="bi" onclick="startLinkFrom('${id}')"><svg class="ic" aria-hidden="true"><use href="#i-link"/></svg>Link</button>
    <button class="bd" onclick="deleteNode('${id}')"><svg class="ic" aria-hidden="true"><use href="#i-trash"/></svg>Excluir</button>
  </div>`;
  return h;
}

// ── Canvas pan/drag ──
const wrap=document.getElementById('canvas-wrap');

function onWrapDown(e){
  const t=e.target;
  const isBackground=t===wrap||t===document.getElementById('cld-canvas')||t===document.getElementById('cld-svg')||t.closest('#cld-svg');
  if(isBackground){
    isPan=true;
    const[cx,cy]=pxy(e);
    panSX=cx-panX;panSY=cy-panY;
    deselect();
    if(isMobile) closeSheet();
  }
}
wrap.addEventListener('mousedown',onWrapDown);
wrap.addEventListener('touchstart',e=>{e.preventDefault();onWrapDown(e);},{passive:false});

function onMove(e){
  const[cx,cy]=pxy(e);
  if(dragNode){
    const r=wrap.getBoundingClientRect();
    SYS.nodes[dragNode].x=(cx-r.left-panX)/scale-dragOX;
    SYS.nodes[dragNode].y=(cy-r.top-panY)/scale-dragOY;
    isDrag=true;
    renderAll();
  }else if(isPan){
    panX=cx-panSX;panY=cy-panSY;
    document.getElementById('cld-canvas').style.transform=`translate(${panX}px,${panY}px) scale(${scale})`;
    requestAnimationFrame(renderEdges);
  }
}
function onUp(){dragNode=null;isPan=false;setTimeout(()=>{isDrag=false;},50);}
document.addEventListener('mousemove',onMove);
document.addEventListener('mouseup',onUp);
document.addEventListener('touchmove',e=>{e.preventDefault();onMove(e);},{passive:false});
document.addEventListener('touchend',onUp);

// Pinch zoom
let pinchD=null;
wrap.addEventListener('touchstart',e=>{if(e.touches.length===2)pinchD=null;},{passive:true});
wrap.addEventListener('touchmove',e=>{
  if(e.touches.length!==2) return;
  e.preventDefault();
  const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);
  if(pinchD!==null){
    const r=wrap.getBoundingClientRect();
    const cx=(e.touches[0].clientX+e.touches[1].clientX)/2-r.left;
    const cy=(e.touches[0].clientY+e.touches[1].clientY)/2-r.top;
    setScale(Math.max(.25,Math.min(2.5,scale*(d/pinchD))),cx,cy);
  }
  pinchD=d;
},{passive:false});

// Mouse wheel
wrap.addEventListener('wheel',e=>{
  e.preventDefault();
  const r=wrap.getBoundingClientRect();
  setScale(Math.max(.25,Math.min(2.5,scale*(e.deltaY>0?.9:1.1))),e.clientX-r.left,e.clientY-r.top);
},{passive:false});

// ── Tools ──
function setTool(t){
  curTool=t;lkSrc=null;
  document.querySelectorAll('.cld-node').forEach(e=>e.classList.remove('lk-src'));
  document.querySelectorAll('.tbtn[id^="tool-"]').forEach(b=>b.classList.remove('active'));
  document.getElementById('tool-'+t)?.classList.add('active');
  const badge=t==='select'?'SELECIONAR':'CRIAR LINK';
  document.getElementById('panel-badge').textContent=badge;
  if(t==='link'){
    document.getElementById('lk-from').value='';
    fillLinkTo('');
    openModal('modal-link');
  }
}
function deleteSelected(){if(selNode)deleteNode(selNode);}
function deleteNode(id){
  delete SYS.nodes[id];
  SYS.links=SYS.links.filter(l=>l.from!==id&&l.to!==id);
  selNode=null;
  const ph='<div class="ph"><span class="mark ico" role="img" aria-label=""><i></i><b></b></span><p>Nó excluído.</p></div>';
  document.getElementById('panel-content').innerHTML=ph;
  document.getElementById('sheet-body').innerHTML=ph;
  document.getElementById('fab').classList.remove('node-sel');
  renderAll();
  if(isMobile)closeSheet();
}
function startLinkFrom(id){
  lkSrc=id;
  document.getElementById('lk-from').value=id;
  document.getElementById('link-hint').textContent=`Origem: "${id}" — selecione o destino.`;
  fillLinkTo(id);
  openModal('modal-link');
}

// ── Panel (desktop) ──
let panelVisible=true;
function togglePanel(){
  panelVisible=!panelVisible;
  const rp=document.getElementById('right-panel');
  const btn=document.getElementById('toggle-panel-btn');
  if(panelVisible){rp.classList.remove('panel-hidden');btn.classList.add('active');}
  else{rp.classList.add('panel-hidden');btn.classList.remove('active');}
  setTimeout(renderEdges,300);
}

// ── Mobile sheet ──
function openSheet(){document.getElementById('mobile-sheet').classList.add('open');document.getElementById('sheet-backdrop').classList.add('open');}
function closeSheet(){document.getElementById('mobile-sheet').classList.remove('open');document.getElementById('sheet-backdrop').classList.remove('open');}

// ── Modals ──
function openModal(id){document.getElementById(id).classList.add('open');}
function closeModal(id){
  document.getElementById(id).classList.remove('open');
  if(id==='modal-link'){
    lkSrc=null;
    document.querySelectorAll('.cld-node').forEach(e=>e.classList.remove('lk-src'));
    if(curTool==='link')setTool('select');
  }
}
document.querySelectorAll('.modal-overlay').forEach(o=>{
  o.addEventListener('click',e=>{if(e.target===o)closeModal(o.id);});
});

// ── CRUD Nodes ──
function openAddModal(){openModal('modal-add');}
function addNode(){
  const name=document.getElementById('nn-name').value.trim();
  if(!name){alert('Nome é obrigatório.');return;}
  if(SYS.nodes[name]){alert(`"${name}" já existe.`);return;}
  SYS.nodes[name]={
    cat:document.getElementById('nn-cat').value,
    val:parseFloat(document.getElementById('nn-val').value)||0,
    expr:document.getElementById('nn-eq').value.trim(),
    desc:document.getElementById('nn-desc').value.trim()||'Sem descrição.',
    x:400+Math.random()*200,y:280+Math.random()*120
  };
  closeModal('modal-add');
  ['nn-name','nn-eq','nn-desc'].forEach(i=>document.getElementById(i).value='');
  document.getElementById('nn-val').value='0';
  renderAll();selectNode(name);
}
function openEditModal(id){
  const nd=SYS.nodes[id];
  document.getElementById('en-id').value=id;
  document.getElementById('en-name').value=id;
  document.getElementById('en-cat').value=nd.cat;
  document.getElementById('en-val').value=nd.val;
  document.getElementById('en-eq').value=nd.expr||'';
  document.getElementById('en-desc').value=nd.desc||'';
  openModal('modal-edit');
}
function saveEdit(){
  const oldId=document.getElementById('en-id').value;
  const newName=document.getElementById('en-name').value.trim();
  if(!newName){alert('Nome é obrigatório.');return;}
  if(newName!==oldId&&SYS.nodes[newName]){alert('Nome já existe.');return;}
  const nd=SYS.nodes[oldId];
  nd.cat=document.getElementById('en-cat').value;
  nd.val=parseFloat(document.getElementById('en-val').value)||0;
  nd.expr=document.getElementById('en-eq').value.trim();
  nd.desc=document.getElementById('en-desc').value.trim()||'Sem descrição.';
  if(newName!==oldId){
    SYS.nodes[newName]=nd;delete SYS.nodes[oldId];
    SYS.links.forEach(l=>{if(l.from===oldId)l.from=newName;if(l.to===oldId)l.to=newName;});
    selNode=newName;
  }
  closeModal('modal-edit');
  renderAll();
  if(selNode){
    const h=buildDetail(selNode);
    document.getElementById('panel-content').innerHTML=h;
    document.getElementById('sheet-body').innerHTML=h;
  }
}
function confirmLink(){
  const from=document.getElementById('lk-from').value||lkSrc;
  const to=document.getElementById('lk-to').value;
  const sign=document.getElementById('lk-sign').value;
  const desc=document.getElementById('lk-desc').value.trim()||`${from} ${sign==='+'?'reforça':'reduz'} ${to}`;
  if(!from||!to||from===to){alert('Origem e destino devem ser diferentes.');return;}
  const ex=SYS.links.find(l=>l.from===from&&l.to===to);
  if(ex){ex.sign=sign;ex.desc=desc;}
  else SYS.links.push({from,to,sign,desc});
  document.getElementById('lk-desc').value='';
  closeModal('modal-link');lkSrc=null;setTool('select');
  renderAll();
}

// ── Keyboard ──
document.addEventListener('keydown',e=>{
  if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)) return;
  if(e.key==='s'||e.key==='S') setTool('select');
  if(e.key==='l'||e.key==='L') setTool('link');
  if(e.key==='n'||e.key==='N') openAddModal();
  if(e.key==='r'||e.key==='R') zoomReset();
  if(e.key==='Delete'||e.key==='Backspace') deleteSelected();
  if(e.key==='Escape'){document.querySelectorAll('.modal-overlay.open').forEach(m=>closeModal(m.id));closeSheet();}
});

// ── Responsive init ──
function initResponsive(){
  isMobile=window.innerWidth<700;
  if(isMobile){
    document.getElementById('fab').classList.add('show');
    document.getElementById('toggle-panel-btn').style.display='none';
    document.getElementById('mobile-sheet').style.display='flex';
    document.getElementById('right-panel').style.display='none';
  }else{
    document.getElementById('fab').classList.remove('show');
    document.getElementById('toggle-panel-btn').style.display='';
    document.getElementById('mobile-sheet').style.display='none';
    document.getElementById('right-panel').style.display='flex';
  }
}
window.addEventListener('resize',()=>{
  initResponsive();
  requestAnimationFrame(renderEdges);
});
initResponsive();
renderAll();
