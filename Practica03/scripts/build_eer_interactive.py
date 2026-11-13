"""Build a self-contained interactive EER explorer from the dated SQL dump."""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "backups" / "respaldo13112026.sql"
OUT = ROOT / "eer.html"
sys.path.insert(0, str(ROOT / "scripts"))
from build_eer import parse as parse_base  # schema and exact INSERT tuple counts


def split_top(text):
    out, start, depth, quote, esc = [], 0, 0, None, False
    for i, ch in enumerate(text):
        if quote:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == quote: quote = None
        elif ch in "'\"`": quote = ch
        elif ch == "(": depth += 1
        elif ch == ")": depth -= 1
        elif ch == "," and depth == 0:
            out.append(text[start:i].strip()); start = i + 1
    if text[start:].strip(): out.append(text[start:].strip())
    return out


def tuples_from(tail, limit=5):
    """Read a few VALUES tuples without splitting commas inside strings/functions."""
    result, quote, esc, depth, start = [], None, False, 0, None
    for i, ch in enumerate(tail):
        if quote:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == quote:
                if i + 1 < len(tail) and tail[i + 1] == quote: esc = True
                else: quote = None
        elif ch in "'\"`": quote = ch
        elif ch == "(":
            if depth == 0: start = i + 1
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start is not None:
                result.append(split_top(tail[start:i])); start = None
                if len(result) >= limit: break
        elif ch == ";" and depth == 0: break
    return result


def sample_value(value):
    value = value.strip()
    if value.upper() == "NULL": return None
    if value.lower().startswith("_binary "): value = value[8:].strip()
    if len(value) >= 2 and value[0] in "'\"" and value[-1] == value[0]:
        value = value[1:-1].replace("\\'", "'").replace("\\\\", "\\").replace("''", "'")
    return value[:180]


def analyze(sql):
    data = parse_base(sql)
    by = {t["name"]: t for t in data["tables"]}
    # Keep ALTER TABLE declarations (including FK, unique, CHECK, and indexes).
    for m in re.finditer(r"ALTER\s+TABLE\s+`([^`]+)`\s+(.*?);", sql, re.I | re.S):
        table = by.get(m.group(1))
        if not table: continue
        for part in split_top(m.group(2)):
            fk = re.search(r"(?:CONSTRAINT\s+`([^`]+)`\s+)?FOREIGN\s+KEY\s*\((.*?)\)\s*REFERENCES\s+`([^`]+)`\s*\((.*?)\)(.*)", part, re.I | re.S)
            if fk:
                name, lc, target, rc, tail = fk.groups()
                cols = re.findall(r"`([^`]+)`", lc); targets = re.findall(r"`([^`]+)`", rc)
                entry = {"name": name or "FK_" + "_".join(cols), "columns": cols, "target": target,
                    "targetColumns": targets, "onDelete": (re.search(r"ON DELETE\s+(\w+(?:\s+\w+)?)", tail, re.I) or [None, None])[1],
                    "onUpdate": (re.search(r"ON UPDATE\s+(\w+(?:\s+\w+)?)", tail, re.I) or [None, None])[1]}
                if not any(f["name"] == entry["name"] and f["columns"] == cols for f in table["foreignKeys"]): table["foreignKeys"].append(entry)
                for c in cols:
                    col = next((c0 for c0 in table["columns"] if c0["name"] == c), None)
                    if col: col["fk"] = True
                continue
            ix = re.search(r"(?:(UNIQUE)\s+)?(?:KEY|INDEX)\s+`([^`]+)`\s*\((.*?)\)", part, re.I | re.S)
            if ix:
                cols = re.findall(r"`([^`]+)`", ix.group(3)); unique = bool(ix.group(1))
                item = {"name": ix.group(2), "columns": cols, "unique": unique, "type": "BTREE"}
                if not any(x["name"] == item["name"] for x in table["indexes"]): table["indexes"].append(item)
            ck = re.search(r"(?:CONSTRAINT\s+`([^`]+)`\s+)?CHECK\s*(\(.*\))", part, re.I | re.S)
            if ck: table.setdefault("checks", []).append({"name": ck.group(1), "expression": ck.group(2)})
    # CHECK constraints embedded in CREATE TABLE bodies.
    for m in re.finditer(r"CREATE\s+TABLE\s+`([^`]+)`\s*\((.*?)\)\s*ENGINE=", sql, re.I | re.S):
        table = by.get(m.group(1))
        if table:
            for part in split_top(m.group(2)):
                ck = re.search(r"(?:CONSTRAINT\s+`([^`]+)`\s+)?CHECK\s*(\(.*\))", part, re.I | re.S)
                if ck: table.setdefault("checks", []).append({"name": ck.group(1), "expression": ck.group(2)})
    # A small, honest sample for each column, from the first INSERTed rows.
    for t in data["tables"]:
        for c in t["columns"]: c["samples"] = []
    ins = re.compile(r"INSERT\s+INTO\s+`([^`]+)`(?:\s*\(([^)]*)\))?\s+VALUES\s+", re.I)
    for m in ins.finditer(sql):
        t = by.get(m.group(1))
        if not t: continue
        names = re.findall(r"`([^`]+)`", m.group(2) or "") or [c["name"] for c in t["columns"]]
        for row in tuples_from(sql[m.end():], 5):
            for name, value in zip(names, row):
                col = next((c for c in t["columns"] if c["name"] == name), None)
                val = sample_value(value)
                if col is not None and val not in col["samples"] and len(col["samples"]) < 5: col["samples"].append(val)
    # EER categories: inferred from declared key structure, with labels exposed as heuristics.
    for t in data["tables"]:
        fks = t["foreignKeys"]
        pk = {c["name"] for c in t["columns"] if c["pk"]}
        fkcols = {c for f in fks for c in f["columns"]}
        unique = any(i.get("unique") and set(i["columns"]) <= fkcols for i in t["indexes"])
        if len(fks) >= 2 and (pk <= fkcols or len(pk) == 0 or t["name"].startswith("tbd_")): t["kind"] = "Pivote / asociación"
        elif fks and pk and pk <= fkcols: t["kind"] = "Débil / subtipo (PK compartida)"
        else: t["kind"] = "Entidad fuerte"
        t["recursive"] = any(f["target"] == t["name"] for f in fks)
        for c in t["columns"]:
            c["unique"] = any(i.get("unique") and c["name"] in i["columns"] for i in t["indexes"])
    return data


PAGE = r'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Explorador EER — __DB__</title>
<style>
:root{color-scheme:dark;--bg:#0b1018;--panel:#111a26;--panel2:#151f2d;--line:#273548;--muted:#93a2b6;--text:#e9f0f8;--mint:#73e3d2;--violet:#c3a5ff;--gold:#f4c27c;--red:#fc8f95}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:13px/1.45 Inter,Segoe UI,system-ui,sans-serif}header{height:74px;display:flex;align-items:center;gap:22px;padding:0 22px;border-bottom:1px solid var(--line);background:#0e1520}.brand{min-width:235px}.eyebrow{font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:var(--mint);font-weight:750}h1{font-size:18px;margin:2px 0}.stats{display:flex;gap:8px}.stat{padding:7px 10px;border:1px solid var(--line);border-radius:9px;background:var(--panel);font-size:11px;color:var(--muted)}.stat b{color:white;font-size:14px;margin-right:5px}.controls{display:flex;gap:7px;align-items:center;flex:1;justify-content:flex-end}input,select,button{background:var(--panel2);border:1px solid #34455b;border-radius:8px;color:var(--text);padding:8px 10px;font:inherit}input{width:225px}button{cursor:pointer}button:hover{border-color:var(--mint)}main{height:calc(100vh - 74px);display:grid;grid-template-columns:minmax(0,1fr) 340px}#stage{position:relative;overflow:hidden;background-color:#0b1018;background-image:radial-gradient(#273344 1px,transparent 1px);background-size:22px 22px;touch-action:none;cursor:grab}#stage:active{cursor:grabbing}svg{width:100%;height:100%;display:block}.side{border-left:1px solid var(--line);background:#0e1520;padding:16px;overflow:auto}.side h2{font-size:11px;text-transform:uppercase;letter-spacing:.13em;color:#a7b5c7;margin:1px 0 12px}.card{fill:#121c29;stroke:#304157;stroke-width:1.2;filter:drop-shadow(0 9px 13px #0006);transition:stroke .2s,opacity .2s}.node{cursor:grab}.node:hover .card,.node.focus .card{stroke:var(--mint);stroke-width:1.7}.node.dim{opacity:.22}.node-title{fill:#edf4fb;font-size:14px;font-weight:700}.node-kind{fill:#9baac0;font-size:9px}.count{fill:#92a6bb;font-size:10px}.colname{fill:#d5e0eb;font-size:10px}.dtype{fill:#8496ab;font-size:9px}.pill{font-size:8px;font-weight:bold}.separator{stroke:#263549;stroke-width:.7}.edge{fill:none;stroke:#567083;stroke-width:1.35;opacity:.78;transition:all .2s}.edge.active{stroke:var(--mint);stroke-width:2.4;opacity:1;filter:drop-shadow(0 0 4px #67e3d4)}.edge.dim{opacity:.08}.edge.inferred{stroke:var(--violet);stroke-dasharray:5 5}.flow{fill:none;stroke:#d4fff7;stroke-width:2.2;stroke-dasharray:2 13;opacity:0;animation:flow 1s linear infinite;pointer-events:none}.edge.active+.flow{opacity:.85}@keyframes flow{to{stroke-dashoffset:-30}}.toolbar{position:absolute;top:13px;left:13px;display:flex;gap:6px}.mini{position:absolute;bottom:14px;right:14px;width:170px;height:112px;border:1px solid #3a4b60;border-radius:9px;background:#111a26dd;cursor:pointer}.hint{position:absolute;bottom:16px;left:15px;color:#91a2b8;background:#101925dd;padding:7px 9px;border:1px solid var(--line);border-radius:7px;font-size:10px;pointer-events:none}.box{padding:10px;margin:0 0 9px;background:var(--panel);border:1px solid var(--line);border-radius:9px}.box b{font-size:12px}.sub{color:var(--muted);font-size:10px;margin-top:4px;overflow-wrap:anywhere}.badge{display:inline-block;padding:1px 4px;margin-right:3px;border:1px solid #3a4c62;border-radius:4px;color:#a8b9cb;font-size:8px}.pk{color:var(--mint);border-color:#30746e}.fk{color:var(--violet);border-color:#654e8b}.uk{color:var(--gold);border-color:#7b633b}.sample{font-family:ui-monospace,Consolas,monospace;color:#c5d4e5}.empty{color:var(--muted);padding:12px;font-size:12px}.legend{display:flex;gap:7px;flex-wrap:wrap;color:var(--muted);font-size:10px;margin:12px 0}.node.hidden,.edge.hidden{display:none}@media(max-width:900px){header{height:auto;min-height:74px;flex-wrap:wrap;padding:10px}.stats{display:none}.controls{flex-wrap:wrap}main{height:calc(100vh - 105px);grid-template-columns:minmax(0,1fr) 285px}}@media(max-width:650px){main{grid-template-columns:1fr}.side{display:none}.brand{min-width:unset}.controls input{width:145px}}
.node.weak .card{stroke:#805fc0;stroke-dasharray:5 3}.node.pivot .card{stroke:#a47b39}.edge-label{fill:#b8c8d7;font-size:9px;paint-order:stroke;stroke:#0b1018;stroke-width:4px;stroke-linejoin:round}
</style></head><body>
<header><div class="brand"><div class="eyebrow">EER · MySQL · __DB__</div><h1>Explorador del esquema</h1></div><div class="stats"><div class="stat"><b>__TABLES__</b>tablas</div><div class="stat"><b>__ROWS__</b>registros</div><div class="stat"><b>__FKS__</b>FK</div></div><div class="controls"><input id="search" placeholder="Buscar tabla o columna…"><select id="type"><option value="">Todos los tipos</option></select><label class="stat"><input id="nonzero" type="checkbox" style="width:auto;vertical-align:middle"> Solo con registros</label></div></header>
<main><div id="stage"><div class="toolbar"><button id="fit">Auto-organizar / centrar</button><button id="minus">−</button><button id="plus">+</button></div><svg id="svg"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4 0 8z" fill="#73e3d2"/></marker><marker id="crow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M1 1L8 5 1 9M8 1L1 5 8 9" fill="none" stroke="#73e3d2"/></marker></defs><g id="world"><g id="edges"></g><g id="nodes"></g></g></svg><svg class="mini" id="mini"><g id="miniWorld"></g></svg><div class="hint">Arrastra el lienzo para mover · rueda para zoom · selecciona una tabla para explorar relaciones · clic en atributo para ver detalles</div></div><aside class="side"><div id="inspect"><h2>Inspección de esquema</h2><div class="box"><b>__TABLES__ tablas · __ROWS__ registros</b><div class="sub">El contador se calcula sumando todas las tuplas de INSERT del respaldo. Las muestras provienen de sus primeras filas insertadas.</div></div><div id="legend" class="legend"></div><h2>Relaciones</h2><div id="relations"></div><h2>Restricciones CHECK</h2><div id="checks"></div></div></aside></main>
<script>const D=__DATA__,by=Object.fromEntries(D.tables.map(t=>[t.name,t])),stage=document.querySelector('#stage'),world=document.querySelector('#world'),edges=document.querySelector('#edges'),nodes=document.querySelector('#nodes');let scale=1,tx=30,ty=25,active=null,hover=null,pan=null,drag=null;
const links=[];for(const t of D.tables)for(const f of t.foreignKeys)links.push({source:f.target,target:t.name,fk:f,explicit:true});
const pos={};const W=290,gx=58,gy=48,cols=4;D.tables.forEach((t,i)=>{const row=Math.floor(i/cols),col=i%cols;pos[t.name]={x:35+col*(W+gx),y:35+row*470,w:W,h:62+t.columns.length*26+30}});
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function colType(c){return (c.type||'').split('(')[0].trim().toLowerCase()}
const typeSet=[...new Set(D.tables.flatMap(t=>t.columns.map(colType)))].sort();for(const x of typeSet){const o=document.createElement('option');o.value=x;o.textContent=x;document.querySelector('#type').append(o)}
function render(){edges.innerHTML='';nodes.innerHTML='';for(const l of links){const a=pos[l.source],b=pos[l.target];if(!a||!b)continue;const sx=a.x+a.w,sy=a.y+31,ex=b.x,ey=b.y+31,mid=(sx+ex)/2,d=`M${sx},${sy} H${mid} V${ey} H${ex}`,focus=active||hover,rel=focus&&(focus===l.source||focus===l.target),child=by[l.target],fc=l.fk.columns.map(n=>child.columns.find(c=>c.name===n)),one=fc.every(c=>c&&c.unique),opt=fc.some(c=>c&&c.nullable==='NULL');edges.insertAdjacentHTML('beforeend',`<path class="edge ${focus?(rel?'active':'dim'):''}" d="${d}" marker-end="url(#crow)"/><path class="flow" d="${d}"/><text class="edge-label" x="${mid+3}" y="${(sy+ey)/2-4}">${one?'1:1':'1:N'} · ${opt?'0..':'1..'}</text>`)}
for(const t of D.tables){const p=pos[t.name],h=p.h;let rows=t.columns.map((c,i)=>{const marks=`${c.pk?'<tspan class="pill" fill="#73e3d2"> PK</tspan>':''}${c.fk?'<tspan class="pill" fill="#c3a5ff"> FK</tspan>':''}${c.unique?'<tspan class="pill" fill="#f4c27c"> UK</tspan>':''}`;return `<g class="attribute" data-table="${esc(t.name)}" data-col="${esc(c.name)}" transform="translate(12,${62+i*26})" style="cursor:pointer"><text class="colname" y="0">${esc(c.name)}${marks}</text><text class="dtype" x="2" y="13">${esc(c.type)} · ${esc(c.nullable)}${c.auto?' · AUTO_INCREMENT':''}${c.default!==null?' · DEFAULT '+esc(c.default):''}</text><line class="separator" x1="0" y1="19" x2="266" y2="19"/></g>`}).join('');let kc=t.kind.startsWith('Débil')?' weak':t.kind.startsWith('Pivote')?' pivot':'';let cls='node'+kc+(active===t.name?' focus':'')+(hover&&hover!==t.name?' dim':'');nodes.insertAdjacentHTML('beforeend',`<g class="${cls}" data-id="${esc(t.name)}" transform="translate(${p.x},${p.y})"><rect class="card" width="${p.w}" height="${h}" rx="11"/><text class="node-title" x="12" y="20">${esc(t.name)}</text><text class="node-kind" x="12" y="36">${esc(t.kind)}${t.recursive?' · recursiva':''}</text><text class="count" x="12" y="51">${t.count.toLocaleString('es-MX')} registros · ${t.columns.length} columnas</text>${rows}</g>`)}apply();drawMini();bindNodes()}
function apply(){world.setAttribute('transform',`translate(${tx},${ty}) scale(${scale})`)}function focusTable(id){active=active===id?null:id;inspectTable(id);render()}
function bindNodes(){nodes.querySelectorAll('.node').forEach(el=>{el.addEventListener('pointerenter',()=>{hover=el.dataset.id;render()});el.addEventListener('pointerleave',()=>{hover=null;render()});el.addEventListener('click',e=>{const a=e.target.closest('.attribute');if(a){e.stopPropagation();inspectColumn(a.dataset.table,a.dataset.col)}else focusTable(el.dataset.id)});el.addEventListener('pointerdown',e=>{if(e.target.closest('.attribute'))return;e.stopPropagation();drag={id:el.dataset.id,x:e.clientX,y:e.clientY,ox:pos[el.dataset.id].x,oy:pos[el.dataset.id].y}})})}
function inspectTable(id){const t=by[id];if(!t)return;document.querySelector('#inspect').innerHTML=`<h2>${esc(t.name)}</h2><div class="box"><b>${t.count.toLocaleString('es-MX')} registros</b><div class="sub">${esc(t.kind)} · ${t.columns.length} columnas · ${t.foreignKeys.length} FK${t.recursive?' · relación recursiva':''}</div></div><h2>Restricciones de tabla</h2>${t.indexes.map(i=>`<div class="box"><b>${i.primary?'PK':i.unique?'UK':'Índice'} · ${esc(i.name)}</b><div class="sub">${esc(i.columns.join(', '))} · ${esc(i.type||'BTREE')}</div></div>`).join('')||'<div class="empty">Sin índices declarados.</div>'}<h2>Relaciones</h2>${links.filter(l=>l.source===id||l.target===id).map(l=>{let f=l.fk;const child=by[l.target],lc=f.columns.map(n=>child.columns.find(c=>c.name===n)),one=lc.every(c=>c&&c.unique);return `<div class="box"><b>${esc(l.source)} ${one?'1:1':'1:N'} ${esc(l.target)}</b><div class="sub">${esc(f.targetColumns.join(', '))} → ${esc(f.columns.join(', '))} · ${esc(f.name||'FK')}</div><div class="sub">Opcionalidad en FK: ${lc.some(c=>c.nullable==='NULL')?'opcional (NULL permitido)':'obligatoria'}</div></div>`}).join('')||'<div class="empty">Sin claves foráneas declaradas.</div>'}<div class="legend"><span class="badge pk">PK</span><span class="badge fk">FK</span><span class="badge uk">UK</span></div>`}
function inspectColumn(table,name){const t=by[table],c=t.columns.find(x=>x.name===name),fk=t.foreignKeys.find(f=>f.columns.includes(name));document.querySelector('#inspect').innerHTML=`<h2>${esc(table)} · ${esc(name)}</h2><div class="box"><b>${esc(c.type)}</b><div class="sub">${esc(c.nullable)}${c.auto?' · AUTO_INCREMENT':''}${c.default!==null?' · DEFAULT '+esc(c.default):''}</div><div style="margin-top:8px">${c.pk?'<span class="badge pk">PK</span>':''}${c.fk?'<span class="badge fk">FK</span>':''}${c.unique?'<span class="badge uk">UK</span>':''}${c.attributes.map(x=>'<span class="badge">'+esc(x)+'</span>').join('')}</div>${c.indexes.length?`<div class="sub">Índice: ${esc(c.indexes.join(', '))}</div>`:''}${fk?`<div class="sub">Referencia: ${esc(fk.target)}(${esc(fk.targetColumns.join(', '))}) · ON DELETE ${esc(fk.onDelete||'NO ACTION')} · ON UPDATE ${esc(fk.onUpdate||'NO ACTION')}</div>`:''}</div><h2>Muestra del respaldo</h2><div class="box">${c.samples.length?c.samples.map(v=>`<div class="sub sample">${esc(v===null?'NULL':JSON.stringify(v))}</div>`).join(''):'<div class="sub">No hay valores insertados para esta columna.</div>'}</div><button id="back">Volver a ${esc(table)}</button>`;document.querySelector('#back').onclick=()=>inspectTable(table)}
function drawMini(){const g=document.querySelector('#miniWorld');g.innerHTML='';let maxX=Math.max(...D.tables.map(t=>pos[t.name].x+W)),maxY=Math.max(...D.tables.map(t=>pos[t.name].y+pos[t.name].h)),sx=150/maxX,sy=90/maxY,s=Math.min(sx,sy);for(const t of D.tables){let p=pos[t.name];g.insertAdjacentHTML('beforeend',`<rect x="${8+p.x*s}" y="${8+p.y*s}" width="${W*s}" height="${Math.max(2,p.h*s)}" rx="2" fill="${active===t.name?'#73e3d2':'#536981'}"/>`)}}
function fit(){let maxX=Math.max(...D.tables.map(t=>pos[t.name].x+W)),maxY=Math.max(...D.tables.map(t=>pos[t.name].y+pos[t.name].h)),r=stage.getBoundingClientRect();scale=Math.min((r.width-60)/maxX,(r.height-65)/maxY,1);tx=(r.width-maxX*scale)/2;ty=30;apply()}
document.querySelector('#fit').onclick=fit;document.querySelector('#plus').onclick=()=>{scale=Math.min(2,scale*1.15);apply()};document.querySelector('#minus').onclick=()=>{scale=Math.max(.25,scale/1.15);apply()};stage.addEventListener('wheel',e=>{e.preventDefault();let old=scale;scale=Math.max(.25,Math.min(2.2,scale*(e.deltaY<0?1.1:.9)));tx=e.offsetX-(e.offsetX-tx)*scale/old;ty=e.offsetY-(e.offsetY-ty)*scale/old;apply()},{passive:false});stage.addEventListener('pointerdown',e=>{if(e.target===stage||e.target.tagName==='svg')pan={x:e.clientX,y:e.clientY,tx,ty}});stage.addEventListener('pointermove',e=>{if(drag){pos[drag.id].x=drag.ox+(e.clientX-drag.x)/scale;pos[drag.id].y=drag.oy+(e.clientY-drag.y)/scale;const n=nodes.querySelector(`[data-id="${CSS.escape(drag.id)}"]`);n?.setAttribute('transform',`translate(${pos[drag.id].x},${pos[drag.id].y})`);renderEdges();drawMini()}else if(pan){tx=pan.tx+e.clientX-pan.x;ty=pan.ty+e.clientY-pan.y;apply()}});stage.addEventListener('pointerup',()=>{drag=null;pan=null});function renderEdges(){edges.querySelectorAll('.edge,.flow').forEach((el,i)=>{let l=links[Math.floor(i/2)],a=pos[l.source],b=pos[l.target],sx=a.x+W,sy=a.y+31,ex=b.x,ey=b.y+31,mid=(sx+ex)/2;el.setAttribute('d',`M${sx},${sy} H${mid} V${ey} H${ex}`)})}
document.querySelector('#search').addEventListener('input',e=>{let q=e.target.value.toLowerCase();nodes.querySelectorAll('.node').forEach(n=>{let t=by[n.dataset.id],hit=t.name.toLowerCase().includes(q)||t.columns.some(c=>c.name.toLowerCase().includes(q));n.classList.toggle('dim',!!q&&!hit);n.classList.toggle('focus',!!q&&hit)});edges.querySelectorAll('.edge,.flow').forEach(x=>x.classList.toggle('dim',!!q))});document.querySelector('#type').onchange=e=>{const ty=e.target.value;nodes.querySelectorAll('.node').forEach(n=>{const t=by[n.dataset.id];n.querySelectorAll('.attribute').forEach((a,i)=>{a.style.opacity=!ty||colType(t.columns[i])===ty?'1':'.12'})})};document.querySelector('#nonzero').onchange=e=>nodes.querySelectorAll('.node').forEach(n=>n.style.display=e.target.checked&&by[n.dataset.id].count===0?'none':'');
const pivots=D.tables.filter(t=>t.kind.startsWith('Pivote'));let many=[];for(const t of pivots){const refs=[...new Set(t.foreignKeys.map(f=>f.target))];for(let i=0;i<refs.length;i++)for(let j=i+1;j<refs.length;j++)many.push(`<div class="box"><b>${esc(refs[i])} N:M ${esc(refs[j])}</b><div class="sub">Asociación mediante ${esc(t.name)}</div></div>`)}document.querySelector('#relations').innerHTML=links.map(l=>`<div class="box"><b>${esc(l.source)} → ${esc(l.target)}</b><div class="sub">${esc(l.fk.name)} · ${esc(l.fk.columns.join(', '))}</div></div>`).join('')+many.join('')||'<div class="empty">No se encontraron relaciones.</div>';document.querySelector('#checks').innerHTML=D.tables.flatMap(t=>(t.checks||[]).map(c=>`<div class="box"><b>${esc(t.name)} · ${esc(c.name||'CHECK')}</b><div class="sub">${esc(c.expression)}</div></div>`)).join('')||'<div class="empty">El respaldo no declara CHECK.</div>';document.querySelector('#legend').innerHTML='<span class="badge pk">Entidad fuerte</span><span class="badge fk">Débil / subtipo</span><span class="badge uk">Pivote / asociación</span>';render();requestAnimationFrame(fit);
document.querySelector('#mini').addEventListener('pointerdown',e=>{e.stopPropagation();const maxX=Math.max(...D.tables.map(t=>pos[t.name].x+W)),maxY=Math.max(...D.tables.map(t=>pos[t.name].y+pos[t.name].h)),s=Math.min(150/maxX,90/maxY),wx=(e.offsetX-8)/s,wy=(e.offsetY-8)/s,r=stage.getBoundingClientRect();tx=r.width/2-wx*scale;ty=r.height/2-wy*scale;apply()});</script></body></html>'''


def main():
    sql = SQL.read_text(encoding="utf-8", errors="replace")
    data = analyze(sql)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    total = sum(t["count"] for t in data["tables"])
    page = PAGE.replace("__DATA__", payload).replace("__DB__", html.escape(data["database"]))
    page = page.replace("__TABLES__", f"{len(data['tables']):,}").replace("__ROWS__", f"{total:,}").replace("__FKS__", str(sum(len(t['foreignKeys']) for t in data['tables'])))
    OUT.write_text(page, encoding="utf-8")
    print(f"{OUT.name}: {len(data['tables'])} tablas, {total:,} registros, {sum(len(t['foreignKeys']) for t in data['tables'])} FK")


if __name__ == "__main__": main()
