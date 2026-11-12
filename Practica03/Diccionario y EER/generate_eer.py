import importlib.util
import re
from pathlib import Path


WORK = Path(__file__).resolve().parent
PROJECT = WORK.parent
SQL = PROJECT / "backups" / "respaldo20261211.sql"
SOURCE = PROJECT / "scripts" / "build_eer.py"
OUT = WORK / "Modelo_EER.html"

spec = importlib.util.spec_from_file_location("eer_source", SOURCE)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
builder.SQL = SQL
builder.OUT = OUT

html = builder.HTML
html = re.sub(
    r'<div class="tools">.*?</div>',
    '<div class="tools"><input id="search" type="search" placeholder="Buscar tabla o columna..." aria-label="Buscar tabla o columna"><button id="details">Colapsar atributos</button><button id="layout">Orden jerarquico</button><button id="fit">Centrar diagrama</button><button id="zoomin">+</button><button id="zoomout">-</button><button id="reset">Restablecer</button></div>',
    html,
    count=1,
    flags=re.S,
)
html = html.replace(
    '<marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#6ce5db"/></marker>',
    '<marker id="one" markerWidth="9" markerHeight="12" refX="2" refY="6" orient="auto"><path d="M2,1 L2,11" stroke="#6ce5db" stroke-width="1.5"/></marker><marker id="many" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1,1 L10,6 L1,11 M1,6 L10,6" fill="none" stroke="#6ce5db" stroke-width="1.4"/></marker>'
)
html = html.replace(
    '.view-toggle{font-size:10px;color:#ae9bdb}',
    '.view-toggle{font-size:10px;color:#ae9bdb}.tools input{width:190px;border:1px solid #33445d;background:#101827;color:#e7edf7;border-radius:8px;padding:8px 10px;outline:none}.tools input:focus{border-color:var(--cyan)}.attribute{cursor:pointer}.attribute:hover .colname,.attribute.search-hit .colname{fill:#fff;font-weight:700}.entity-kind{fill:#91a0b8;font-size:8px;font-weight:700;letter-spacing:.06em}.empty-search{fill:#91a0b8;font-size:18px}'
)
html = html.replace(
    'let scale=1,tx=40,ty=30,selected=null,hovered=null,drag=null,panning=null;',
    'let scale=1,tx=40,ty=30,selected=null,hovered=null,drag=null,panning=null,query="",allExpanded=true,fieldFocus=null,displayedLinks=[];'
)
html = html.replace(
    'function render(){edges.innerHTML=\'\';nodes.innerHTML=\'\';\nlinks.forEach((l,i)=>{let a=positions[l.source],b=positions[l.target];if(!a||!b)return;',
    'function visibleTable(t){return !query||t.name.toLowerCase().includes(query)||t.columns.some(c=>(c.name+" "+c.type).toLowerCase().includes(query))}\nfunction render(){edges.innerHTML=\'\';nodes.innerHTML=\'\';\nlinks.forEach((l,i)=>{if(!visibleTable(tableBy[l.source])||!visibleTable(tableBy[l.target]))return;let a=positions[l.source],b=positions[l.target];if(!a||!b)return;'
)
html = html.replace(
    'let focus=selected||hovered,active=focus&&(focus===l.source||focus===l.target);edges.insertAdjacentHTML(\'beforeend\',`<path class="link ${l.explicit?\'\':\'implicit\'} ${focus?(active?\'active\':\'dim\'):ę}" d="${d}" marker-end="url(#arrow)"/><path class="flow" d="${d}"/>`) });',
    'let focus=selected||hovered,active=fieldFocus?(fieldFocus.table===l.target&&l.fk.columns.includes(fieldFocus.column)):focus&&(focus===l.source||focus===l.target);edges.insertAdjacentHTML(\'beforeend\',`<path class="link ${l.explicit?\'\':\'implicit\'} ${focus?(active?\'active\':\'dim\'):ę}" d="${d}" marker-start="url(#one)" marker-end="url(#${isUniqueFk(l)?\'one\':\'many\'})"/><path class="flow" d="${d}"/>`) });'
)
# The template has a compact focus expression; replace it independently to avoid
# coupling the edits above to its localized CSS/text.
html = html.replace(
    'let focus=selected||hovered,active=focus&&(focus===l.source||focus===l.target);edges.insertAdjacentHTML(\'beforeend\',`<path class="link ${l.explicit?\'\':\'implicit\'} ${focus?(active?\'active\':\'dim\'):\'\'}" d="${d}" marker-end="url(#arrow)"/><path class="flow" d="${d}"/>`) });',
    'let focus=selected||hovered,active=fieldFocus?(fieldFocus.table===l.target&&l.fk.columns.includes(fieldFocus.column)):focus&&(focus===l.source||focus===l.target);edges.insertAdjacentHTML(\'beforeend\',`<path class="link ${l.explicit?\'\':\'implicit\'} ${focus?(active?\'active\':\'dim\'):\'\'}" d="${d}" marker-start="url(#one)" marker-end="url(#${isUniqueFk(l)?\'one\':\'many\'})"/><path class="flow" d="${d}"/>`) });'
)
html = html.replace(
    'DATA.tables.forEach(t=>{let p=positions[t.name],h=nodeHeight(t);let rows=p.expanded?t.columns.map((c,i)=>`<g transform="translate(12,${58+i*25})">',
    'DATA.tables.forEach(t=>{if(!visibleTable(t))return;let p=positions[t.name],h=nodeHeight(t);let rows=p.expanded?t.columns.map((c,i)=>`<g class="attribute ${query&&(c.name+" "+c.type).toLowerCase().includes(query)?\'search-hit\':\'\'}" data-column="${esc(c.name)}" transform="translate(12,${58+i*25})">'
)
html = html.replace(
    'el.innerHTML=`<rect class="card" width="${p.w}" height="${h}" rx="11"/><path class="head" d="M11 0h238a11 11 0 0 1 11 11v43H0V11A11 11 0 0 1 11 0"/><text class="node-title" x="13" y="23">${esc(t.name)}</text><text class="node-count" x="13" y="41">Total registros: ${t.count.toLocaleString(\'es-MX\')}</text><text class="view-toggle" x="231" y="24">${p.expanded?\'âˆ’\':\'+\'}</text>${rows}`;',
    'let pks=t.columns.filter(c=>c.pk).map(c=>c.name),fks=t.foreignKeys;let kind=fks.some(f=>f.columns.length===pks.length&&f.columns.every(c=>pks.includes(c)))?\'SUBTIPO 1:1 (POSIBLE)\':fks.length>=2&&pks.length&&pks.every(c=>fks.some(f=>f.columns.includes(c)))?\'PIVOTE\':fks.some(f=>f.columns.some(c=>pks.includes(c))&&pks.length>1)?\'DÉBIL (POSIBLE)\':\'\';el.innerHTML=`<rect class="card" width="${p.w}" height="${h}" rx="11"/><path class="head" d="M11 0h238a11 11 0 0 1 11 11v43H0V11A11 11 0 0 1 11 0"/><text class="node-title" x="13" y="23">${esc(t.name)}</text><text class="entity-kind" x="13" y="53">${kind}</text><text class="node-count" x="13" y="41">Total registros: ${t.count.toLocaleString(\'es-MX\')}</text><text class="view-toggle" x="231" y="24">${p.expanded?\'âˆ’\':\'+\'}</text>${rows}`;'
)
html = html.replace(
    'nodes.addEventListener(\'pointerdown\',e=>{let n=e.target.closest(\'.node\');if(!n)return;e.stopPropagation();if(e.detail===2){',
    'nodes.addEventListener(\'pointerdown\',e=>{let n=e.target.closest(\'.node\');if(!n)return;e.stopPropagation();let attr=e.target.closest(\'.attribute\');if(attr){fieldFocus={table:n.dataset.id,column:attr.dataset.column};selected=n.dataset.id;render()}else fieldFocus=null;if(e.detail===2){'
)
html = html.replace(
    'document.querySelector(\'#fit\').onclick=fit;',
    'document.querySelector(\'#search\').addEventListener(\'input\',e=>{query=e.target.value.trim().toLowerCase();selected=null;hovered=null;fieldFocus=null;render();requestAnimationFrame(fit)});document.querySelector(\'#details\').onclick=()=>{allExpanded=!allExpanded;DATA.tables.forEach(t=>positions[t.name].expanded=allExpanded);document.querySelector(\'#details\').textContent=allExpanded?\'Colapsar atributos\':\'Expandir atributos\';render();requestAnimationFrame(fit)};document.querySelector(\'#layout\').onclick=()=>{let level=Object.fromEntries(DATA.tables.map(t=>[t.name,0]));for(let pass=0;pass<DATA.tables.length;pass++)links.forEach(l=>{level[l.target]=Math.max(level[l.target],level[l.source]+1)});let ordered=[...DATA.tables].sort((a,b)=>level[a.name]-level[b.name]||a.name.localeCompare(b.name));ordered.forEach((t,i)=>{let col=i%cols,row=Math.floor(i/cols);positions[t.name].x=40+col*(nodeW+gapX);positions[t.name].y=38+row*390});render();requestAnimationFrame(fit)};document.querySelector(\'#fit\').onclick=fit;'
)

# Remove an accidental sentinel in the attempted broad replacement; the precise
# replacement below is the one used by the delivered script.
html = html.replace('):ę}', "):''}")
builder.HTML = html
builder.main()

# Keep the renderer source as the base, then enhance the emitted standalone page.
page = OUT.read_text(encoding="utf-8")
page = re.sub(
    r"function render\(\)\{edges\.innerHTML='';nodes\.innerHTML='';\nlinks\.forEach",
    "function render(){edges.innerHTML='';nodes.innerHTML='';displayedLinks=links.filter(l=>visibleTable(tableBy[l.source])&&visibleTable(tableBy[l.target]));\ndisplayedLinks.forEach",
    page,
    count=1,
)
page = page.replace("let l=links[Math.floor(i/2)]", "let l=displayedLinks[Math.floor(i/2)]")
page = page.replace(
    'function visibleTable(t){return !query||t.name.toLowerCase().includes(query)||t.columns.some(c=>(c.name+" "+c.type).toLowerCase().includes(query))}',
    'function matchesTable(t){return t&&(t.name.toLowerCase().includes(query)||t.columns.some(c=>(c.name+" "+c.type).toLowerCase().includes(query)))}function visibleTable(t){return !query||matchesTable(t)||links.some(l=>l.source===t.name&&matchesTable(tableBy[l.target])||l.target===t.name&&matchesTable(tableBy[l.source]))}',
)
page = page.replace(
    "let el=document.createElementNS('http://www.w3.org/2000/svg','g');",
    "let pks=t.columns.filter(c=>c.pk).map(c=>c.name),fks=t.foreignKeys;let kind=fks.some(f=>f.columns.length===pks.length&&f.columns.every(c=>pks.includes(c)))?'SUBTIPO 1:1 (POSIBLE)':fks.length>=2&&pks.length&&pks.every(c=>fks.some(f=>f.columns.includes(c)))?'PIVOTE':fks.some(f=>f.columns.some(c=>pks.includes(c))&&pks.length>1)?'DEBIL (POSIBLE)':'';let el=document.createElementNS('http://www.w3.org/2000/svg','g');",
)
page = page.replace(
    '<text class="node-title" x="13" y="23">${esc(t.name)}</text><text class="node-count"',
    '<text class="node-title" x="13" y="23">${esc(t.name)}</text><text class="entity-kind" x="13" y="53">${kind}</text><text class="node-count"',
)
page = page.replace(
    "for(let pass=0;pass<DATA.tables.length;pass++)links.forEach(l=>{level[l.target]=Math.max(level[l.target],level[l.source]+1)});",
    "let roots=DATA.tables.filter(t=>!links.some(l=>l.target===t.name)).map(t=>t.name),seen=new Set(roots),queue=[...roots];while(queue.length){let parent=queue.shift();links.filter(l=>l.source===parent).forEach(l=>{if(!seen.has(l.target)){level[l.target]=level[parent]+1;seen.add(l.target);queue.push(l.target)}})};",
)
page = page.replace(
    "nodes.addEventListener('pointerover',e=>{",
    "nodes.addEventListener('click',e=>{let attr=e.target.closest('.attribute');if(attr){let n=attr.closest('.node');fieldFocus={table:n.dataset.id,column:attr.dataset.column};selected=n.dataset.id;render()}});nodes.addEventListener('pointerover',e=>{",
)
page = page.replace(
    "if(attr){fieldFocus={table:n.dataset.id,column:attr.dataset.column};selected=n.dataset.id;render()}else fieldFocus=null;if(e.detail===2)",
    "if(attr){fieldFocus={table:n.dataset.id,column:attr.dataset.column};selected=n.dataset.id}else{fieldFocus=null;selected=selected===n.dataset.id?null:n.dataset.id};if(e.detail===2)",
)
page = page.replace("}setSelected(n.dataset.id);drag={", "}drag={")
page = page.replace("nodes.addEventListener('pointerup',()=>drag=null)", "nodes.addEventListener('pointerup',()=>{drag=null;render()})")
page = page.replace("x.columns.some(k=>k.name.toLowerCase()==='id'&&k.pk)", "x.columns.some(k=>k.pk)")
page = page.replace(
    ".map(x=>({table:x,token:norm(x.name)}))",
    ".map(x=>({table:x,tokens:[norm(x.name),...x.columns.filter(k=>k.pk).map(k=>norm(k.name.replace(/^id_/i,'').replace(/_id$/i,''))).filter(v=>v!=='id')]}))",
)
page = page.replace(
    "score:x.token===stem?100:x.token.endsWith('_'+stem)?75:x.token.includes(stem)?40:0",
    "score:Math.max(...x.tokens.map(token=>token===stem?100:token.endsWith('_'+stem)?75:token.includes(stem)?40:0))",
)
page = page.replace(
    ".pk-b{color:#78e8d8!important;border-color:#367c78}.fk-b{color:#c5aaff!important;border-color:#644d90}",
    ".pk-b{color:#78e8d8!important;border-color:#367c78}.fk-b{color:#c5aaff!important;border-color:#644d90}.colname.key,.pk-badge{fill:#78e8d8}.colname.fk,.fk-badge{fill:#c5aaff}",
)
page = page.replace(
    "const positions={};const cols=5,gapX=58,gapY=48,nodeW=260;",
    "const inferredColumns=new Set(links.filter(l=>!l.explicit).flatMap(l=>l.fk.columns.map(c=>l.target+'.'+c)));const positions={};const cols=5,gapX=58,gapY=48,nodeW=260;",
)
page = page.replace(
    "${c.fk?'<text class=\"badge fk-badge\" x=\"24\">FK</text>':''}",
    "${c.fk?'<text class=\"badge fk-badge\" x=\"24\">FK</text>':inferredColumns.has(t.name+'.'+c.name)?'<text class=\"badge fk-badge\" x=\"24\">FK?</text>':''}",
)
page = page.replace("Relaciones declaradas", "Relaciones y cardinalidad")
page = page.replace("Vistas del respaldo", "Vistas relacionadas")
page = page.replace(
    "links.map(l=>{let oneOne=isUniqueFk(l);return `",
    "links.map(l=>{let oneOne=isUniqueFk(l),optional=l.fk.columns.some(c=>tableBy[l.target].columns.find(x=>x.name===c)?.nullable==='NULL');return `",
)
page = re.sub(
    r"(<div>\$\{l\.explicit\?.*?\}</div>)(</div>`)",
    r"\1<div>${optional?'FK opcional (NULL permitido)':'FK obligatoria (NOT NULL)'}</div>\2",
    page,
    count=1,
)
page = page.replace(
    ".tools input{width:190px;",
    "header{gap:10px}.tools{gap:4px}.tools button{font-size:10px;padding:6px 7px}.tools input{width:155px;",
)
OUT.write_text(page, encoding="utf-8")

