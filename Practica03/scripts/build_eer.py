import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "backups" / "respaldo20261111.sql"
OUT = ROOT / "eer.html"


def split_sql_items(body):
    items, start, depth, quote, escape = [], 0, 0, None, False
    for i, ch in enumerate(body):
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            items.append(body[start:i].strip())
            start = i + 1
    if body[start:].strip():
        items.append(body[start:].strip())
    return items


def tuple_count(statement_tail):
    depth = 0
    quote = None
    escape = False
    count = 0
    for ch in statement_tail:
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif ch == "(":
            if depth == 0:
                count += 1
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == ";" and depth == 0:
            break
    return count


def parse(sql):
    tables = {}
    create_re = re.compile(r"CREATE TABLE\s+`([^`]+)`\s*\((.*?)\)\s*ENGINE=", re.I | re.S)
    for match in create_re.finditer(sql):
        name, body = match.group(1), match.group(2)
        table = {"name": name, "columns": [], "indexes": [], "foreignKeys": []}
        for item in split_sql_items(body):
            col = re.match(r"`([^`]+)`\s+(.+)$", item, re.S)
            if col:
                colname, spec = col.groups()
                typem = re.match(r"([A-Za-z]+(?:\s*\([^)]*\))?(?:\s+(?:unsigned|signed|zerofill))?(?:\s+precision)?)", spec, re.I)
                dtype = typem.group(1).strip() if typem else ""
                nullable = "NULL" if re.search(r"\bNULL\b", spec, re.I) and not re.search(r"\bNOT\s+NULL\b", spec, re.I) else "NOT NULL"
                defaultm = re.search(r"\bDEFAULT\s+((?:'[^']*')|(?:b'[^']*')|(?:[^\s,]+))", spec, re.I)
                table["columns"].append({"name": colname, "type": dtype, "nullable": nullable,
                    "auto": bool(re.search(r"\bAUTO_INCREMENT\b", spec, re.I)),
                    "default": defaultm.group(1) if defaultm else None,
                    "attributes": [x.upper() for x in re.findall(r"\b(?:unsigned|signed|zerofill)\b", spec, re.I)] + (["ON UPDATE " + re.search(r"ON UPDATE\s+(CURRENT_TIMESTAMP(?:\(\d+\))?)", spec, re.I).group(1).upper()] if re.search(r"ON UPDATE\s+(CURRENT_TIMESTAMP(?:\(\d+\))?)", spec, re.I) else []),
                    "pk": False, "fk": False, "indexes": []})
                continue
            pm = re.match(r"PRIMARY KEY\s*\((.*?)\)", item, re.I | re.S)
            if pm:
                primary_cols = re.findall(r"`([^`]+)`", pm.group(1))
                table["indexes"].append({"name": "PRIMARY", "columns": primary_cols, "unique": True, "type": "BTREE", "primary": True})
                for c in primary_cols:
                    found = next((x for x in table["columns"] if x["name"] == c), None)
                    if found:
                        found["pk"] = True
                continue
            im = re.match(r"(?:(UNIQUE|FULLTEXT|SPATIAL)\s+)?(?:KEY|INDEX)\s+`([^`]+)`\s*\((.*?)\)(.*)", item, re.I | re.S)
            if im:
                idx_kind, idx_name, idx_cols, idx_tail = im.groups()
                cols = re.findall(r"`([^`]+)`", idx_cols)
                unique = idx_kind and idx_kind.upper() == "UNIQUE"
                method = (re.search(r"USING\s+(BTREE|HASH)", idx_tail, re.I) or [None, "BTREE"])[1].upper()
                table["indexes"].append({"name": idx_name, "columns": cols, "unique": bool(unique), "type": (idx_kind.upper() if idx_kind and idx_kind.upper() in ("FULLTEXT", "SPATIAL") else method)})
                for c in cols:
                    found = next((x for x in table["columns"] if x["name"] == c), None)
                    if found: found["indexes"].append(im.group(1))
                continue
            fm = re.match(r"CONSTRAINT\s+`([^`]+)`\s+FOREIGN KEY\s*\((.*?)\)\s+REFERENCES\s+`([^`]+)`\s*\((.*?)\)(.*)", item, re.I | re.S)
            if fm:
                namef, local, target, remote, tail = fm.groups()
                local_cols, remote_cols = re.findall(r"`([^`]+)`", local), re.findall(r"`([^`]+)`", remote)
                table["foreignKeys"].append({"name": namef, "columns": local_cols, "target": target,
                    "targetColumns": remote_cols, "onDelete": (re.search(r"ON DELETE\s+(\w+(?:\s+\w+)?)", tail, re.I) or [None, None])[1],
                    "onUpdate": (re.search(r"ON UPDATE\s+(\w+(?:\s+\w+)?)", tail, re.I) or [None, None])[1]})
                for c in local_cols:
                    found = next((x for x in table["columns"] if x["name"] == c), None)
                    if found: found["fk"] = True
        for column in table["columns"]:
            column["uniqueIndexes"] = [i["name"] for i in table["indexes"] if i["unique"] and not i.get("primary") and column["name"] in i["columns"]]
        tail = sql[match.end():sql.find(";", match.end())]
        table["engine"] = (re.search(r"\bENGINE\s*=\s*(\w+)", tail, re.I) or [None, "No especificado"])[1]
        table["charset"] = (re.search(r"\bDEFAULT\s+CHARSET\s*=\s*([\w]+)", tail, re.I) or re.search(r"\bCHARSET\s*=\s*([\w]+)", tail, re.I) or [None, "No especificado"])[1]
        table["collation"] = (re.search(r"\bCOLLATE\s*=\s*([\w]+)", tail, re.I) or [None, "No especificado"])[1]
        tables[name] = table

    counts = {name: 0 for name in tables}
    trigger_ranges = [m.span() for m in re.finditer(r"\bTRIGGER\b.*?\bEND\s*\*/\s*;?", sql, re.I | re.S)]
    insert_re = re.compile(r"INSERT\s+INTO\s+`([^`]+)`(?:\s*\([^)]*\))?\s+VALUES\s+", re.I)
    for m in insert_re.finditer(sql):
        if any(start <= m.start() < end for start, end in trigger_ranges):
            continue
        name = m.group(1)
        if name in counts:
            counts[name] += tuple_count(sql[m.end():])
    for n, t in tables.items():
        t["count"] = counts[n]

    views = []
    view_re = re.compile(r"\bVIEW\s+`([^`]+)`\s+AS\s+(.*?);", re.I | re.S)
    for m in view_re.finditer(sql):
        definition = m.group(2).strip()
        if re.match(r"SELECT\s+1\s+AS\b", definition, re.I):
            continue
        refs = list(dict.fromkeys(re.findall(r"\b(?:FROM|JOIN)\s+(?:`[^`]+`\s*\.\s*)?`([^`]+)`", definition, re.I)))
        views.append({"name": m.group(1), "sources": refs, "definition": definition})
    views = list({v["name"]: v for v in views}.values())
    return {"database": (re.search(r"CREATE DATABASE\s+IF NOT EXISTS\s+`([^`]+)`", sql, re.I) or [None, ""])[1],
            "tables": list(tables.values()), "views": views}


def main():
    data = parse(SQL.read_text(encoding="utf-8", errors="replace"))
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    OUT.write_text(HTML.replace("__DATA__", payload), encoding="utf-8")
    print(f"{OUT.name}: {len(data['tables'])} tablas, {len(data['views'])} vistas; "
          f"{sum(t['count'] for t in data['tables']):,} filas insertadas")


HTML = r'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Modelo EER · __DB__</title>
<style>
:root{color-scheme:dark;--bg:#0a0e17;--panel:#111827;--line:#283449;--muted:#91a0b8;--text:#e7edf7;--cyan:#6ce5db;--purple:#b69cff;--orange:#ffbd75}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.4 Inter,ui-sans-serif,system-ui,Segoe UI,sans-serif;overflow:hidden}header{height:82px;padding:17px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #1f2a3b;background:#0d1320}header small,.muted{color:var(--muted)}h1{font-size:19px;margin:0 0 3px;letter-spacing:.01em}.eyebrow{font-size:10px;text-transform:uppercase;letter-spacing:.18em;color:var(--cyan);font-weight:700}.stats{display:flex;gap:9px}.stat{background:#141e2d;border:1px solid #28374d;border-radius:10px;padding:8px 12px;font-size:12px;color:#b6c2d4}.stat b{color:#fff;font-size:14px;margin-right:5px}.tools{display:flex;gap:7px}button{border:1px solid #33445d;background:#141e2d;color:#dbe5f3;border-radius:8px;padding:7px 10px;cursor:pointer}button:hover{border-color:var(--cyan);color:#fff}main{height:calc(100vh - 82px);display:grid;grid-template-columns:1fr 300px}#stage{position:relative;overflow:hidden;background-image:radial-gradient(#253249 1px,transparent 1px);background-size:22px 22px;cursor:grab}#stage:active{cursor:grabbing}svg{width:100%;height:100%;display:block}.side{border-left:1px solid #202a3b;background:#0d1320;overflow:auto;padding:15px}.side h2{font-size:12px;text-transform:uppercase;letter-spacing:.13em;color:#9baac0;margin:5px 0 12px}.hint{position:absolute;bottom:13px;left:16px;background:#101827dc;border:1px solid #263349;border-radius:8px;padding:7px 10px;color:#9eacc1;font-size:11px;pointer-events:none}.link{fill:none;stroke:#456074;stroke-width:1.5;opacity:.75;transition:opacity .25s,stroke .25s,stroke-width .25s}.link.active{stroke:var(--cyan);stroke-width:2.5;opacity:1;filter:drop-shadow(0 0 5px #42e5da)}.link.dim{opacity:.09}.link.implicit{stroke-dasharray:5 5;stroke:#a180d5}.flow{fill:none;stroke:#b8fff5;stroke-width:2;stroke-dasharray:3 13;opacity:0;animation:dash 1.1s linear infinite;pointer-events:none}.link.active+.flow{opacity:.8}@keyframes dash{to{stroke-dashoffset:-32}}.node{filter:drop-shadow(0 9px 18px #0007);cursor:move}.card{fill:#111a28;stroke:#2a3c51;stroke-width:1.2;transition:stroke .2s,filter .2s}.node:hover .card,.node.selected .card{stroke:var(--cyan);filter:drop-shadow(0 0 8px #36d6cb55)}.head{fill:#162536}.node-title{fill:#edf5ff;font-size:14px;font-weight:700}.node-count{fill:#90a8b9;font-size:10px}.colname{fill:#d3dfed;font-size:11px}.coltype{fill:#8494aa;font-size:10px}.badge{font-size:8px;font-weight:700}.view-card{fill:#171426;stroke:#4e416c}.view-node .head{fill:#211b34}.view-node .node-title{fill:#d7c5ff}.view-edge{fill:none;stroke:#836bb4;stroke-dasharray:3 6;opacity:.3}.sep{stroke:#263447;stroke-width:.8}.side-card{border:1px solid #27374b;border-radius:10px;padding:10px;margin-bottom:9px;background:#111a28}.side-card b{font-size:12px}.side-card div{font-size:11px;color:#93a3b9;margin-top:4px;overflow-wrap:anywhere}.legend{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 18px;font-size:10px;color:#9baac0}.dot{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:4px;background:var(--cyan)}.key{color:var(--cyan)}.fk{color:var(--purple)}.idx{color:var(--orange)}.col{display:flex;justify-content:space-between;gap:6px;align-items:center}.col-meta{display:flex;gap:4px;white-space:nowrap}.badge-txt{border:1px solid #36485c;border-radius:4px;padding:1px 3px;color:#9eafc4}.pk-b{color:#78e8d8!important;border-color:#367c78}.fk-b{color:#c5aaff!important;border-color:#644d90}.view-toggle{font-size:10px;color:#ae9bdb}
</style></head><body>
<header><div><div class="eyebrow">Esquema relacional · MySQL</div><h1>Modelo EER <small id="db"></small></h1></div><div class="stats" id="stats"></div><div class="tools"><button id="fit">Ajustar</button><button id="zoomin">＋</button><button id="zoomout">−</button><button id="reset">Restablecer</button></div></header>
<main><div id="stage"><svg id="svg"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#6ce5db"/></marker></defs><g id="world"><g id="edges"></g><g id="nodes"></g></g></svg><div class="hint">Arrastra nodos · rueda para zoom · clic para fijar relaciones · doble clic para expandir</div></div><aside class="side"><h2>Relaciones declaradas</h2><div id="relations"></div><h2>Convenciones</h2><div id="legend" class="legend"></div><h2>Vistas del respaldo</h2><div id="views"></div></aside></main>
<script>
const DATA=__DATA__;
document.querySelector('#db').textContent='· '+DATA.database;
const total=DATA.tables.reduce((a,t)=>a+t.count,0);document.querySelector('#stats').innerHTML=`<div class="stat"><b>${DATA.tables.length}</b>tablas</div><div class="stat"><b>${total.toLocaleString('es-MX')}</b>filas insertadas</div><div class="stat"><b>${DATA.views.length}</b>vistas</div>`;
const svg=document.querySelector('#svg'),world=document.querySelector('#world'),edges=document.querySelector('#edges'),nodes=document.querySelector('#nodes'),stage=document.querySelector('#stage');let scale=1,tx=40,ty=30,selected=null,hovered=null,drag=null,panning=null;
const tableBy=Object.fromEntries(DATA.tables.map(t=>[t.name,t]));
const links=[];DATA.tables.forEach(t=>t.foreignKeys.forEach(f=>links.push({source:f.target,target:t.name,fk:f,explicit:true}))); 
// Infer unambiguous conventional ID columns where the dump does not declare an FK.
const singular=s=>s==='people'?'person':s.replace(/ies$/,'y').replace(/s$/,'');const norm=s=>s.toLowerCase().replace(/^(tb|tbd|tbc)_/,'').split('_').map(singular).join('_');
DATA.tables.forEach(t=>t.columns.forEach(c=>{if(c.fk||c.pk)return;let m=c.name.match(/^(?:id_(.+)|(.+)_id)$/i);if(!m)return;let stem=norm(m[1]||m[2]);if(stem==='person')stem='person';let candidates=DATA.tables.filter(x=>x.name!==t.name&&x.columns.some(k=>k.name.toLowerCase()==='id'&&k.pk)).map(x=>({table:x,token:norm(x.name)}));let scored=candidates.map(x=>({table:x.table,score:x.token===stem?100:x.token.endsWith('_'+stem)?75:x.token.includes(stem)?40:0})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score);if(!scored.length||scored.length>1&&scored[0].score===scored[1].score)return;let target=scored[0].table.name;if(!links.some(l=>l.source===target&&l.target===t.name&&l.fk.columns.includes(c.name)))links.push({source:target,target:t.name,fk:{name:c.name,columns:[c.name],targetColumns:['ID']},explicit:false})}));
const positions={};const cols=5,gapX=58,gapY=48,nodeW=260;
DATA.tables.forEach((t,i)=>{let row=Math.floor(i/cols),col=i%cols;positions[t.name]={x:40+col*(nodeW+gapX),y:38+row*390,w:nodeW,h:65+t.columns.length*25+15,expanded:true}});
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function nodeHeight(t){return 56+(positions[t.name].expanded?t.columns.length*25+12:0)}
function render(){edges.innerHTML='';nodes.innerHTML='';
links.forEach((l,i)=>{let a=positions[l.source],b=positions[l.target];if(!a||!b)return;let ax=a.x+a.w/2,ay=a.y+nodeHeight(tableBy[l.source])/2,bx=b.x+b.w/2,by=b.y+nodeHeight(tableBy[l.target])/2,dx=(bx-ax)*.35;let d=`M${ax},${ay} C${ax+dx},${ay} ${bx-dx},${by} ${bx},${by}`;let focus=selected||hovered,active=focus&&(focus===l.source||focus===l.target);edges.insertAdjacentHTML('beforeend',`<path class="link ${l.explicit?'':'implicit'} ${focus?(active?'active':'dim'):''}" d="${d}" marker-end="url(#arrow)"/><path class="flow" d="${d}"/>`) });
DATA.tables.forEach(t=>{let p=positions[t.name],h=nodeHeight(t);let rows=p.expanded?t.columns.map((c,i)=>`<g transform="translate(12,${58+i*25})"><text class="colname ${c.pk?'key':''} ${c.fk?'fk':''}" y="0">${esc(c.name)}</text><text class="coltype" x="111" y="0">${esc(c.type)}</text><text class="coltype" x="111" y="12">${esc(c.nullable)}${c.auto?' · AUTO_INCREMENT':''}${c.default?' · DEFAULT '+esc(c.default):''}</text><g class="col-meta" transform="translate(211,-5)">${c.pk?'<text class="badge pk-badge">PK</text>':''}${c.fk?'<text class="badge fk-badge" x="24">FK</text>':''}${c.indexes.length?'<text class="badge" x="48" fill="#ffbd75">IDX</text>':''}</g><line class="sep" x1="0" y1="17" x2="236" y2="17"/></g>`).join(''):'';
let el=document.createElementNS('http://www.w3.org/2000/svg','g');el.setAttribute('class','node '+(selected===t.name?'selected':''));el.dataset.id=t.name;el.setAttribute('transform',`translate(${p.x},${p.y})`);el.innerHTML=`<rect class="card" width="${p.w}" height="${h}" rx="11"/><path class="head" d="M11 0h238a11 11 0 0 1 11 11v43H0V11A11 11 0 0 1 11 0"/><text class="node-title" x="13" y="23">${esc(t.name)}</text><text class="node-count" x="13" y="41">Total registros: ${t.count.toLocaleString('es-MX')}</text><text class="view-toggle" x="231" y="24">${p.expanded?'−':'+'}</text>${rows}`;nodes.appendChild(el);});
applyTransform()}
function applyTransform(){world.setAttribute('transform',`translate(${tx},${ty}) scale(${scale})`)}
function setSelected(id){selected=selected===id?null:id;render()}
nodes.addEventListener('pointerover',e=>{let n=e.target.closest('.node');if(n&&hovered!==n.dataset.id){hovered=n.dataset.id;render()}});nodes.addEventListener('pointerleave',()=>{hovered=null;render()});
nodes.addEventListener('pointerdown',e=>{let n=e.target.closest('.node');if(!n)return;e.stopPropagation();if(e.detail===2){let p=positions[n.dataset.id];if(tableBy[n.dataset.id])p.expanded=!p.expanded;render();return}setSelected(n.dataset.id);drag={id:n.dataset.id,sx:e.clientX,sy:e.clientY,ox:positions[n.dataset.id].x,oy:positions[n.dataset.id].y};n.setPointerCapture(e.pointerId)});
nodes.addEventListener('pointermove',e=>{if(!drag)return;let p=positions[drag.id];p.x=drag.ox+(e.clientX-drag.sx)/scale;p.y=drag.oy+(e.clientY-drag.sy)/scale;let n=nodes.querySelector(`[data-id="${CSS.escape(drag.id)}"]`);if(n)n.setAttribute('transform',`translate(${p.x},${p.y})`);renderEdges()});nodes.addEventListener('pointerup',()=>drag=null);
function renderEdges(){edges.querySelectorAll('.link,.flow').forEach((el,i)=>{let l=links[Math.floor(i/2)];if(!l)return;let a=positions[l.source],b=positions[l.target],ax=a.x+a.w/2,ay=a.y+nodeHeight(tableBy[l.source])/2,bx=b.x+b.w/2,by=b.y+nodeHeight(tableBy[l.target])/2,dx=(bx-ax)*.35;el.setAttribute('d',`M${ax},${ay} C${ax+dx},${ay} ${bx-dx},${by} ${bx},${by}`)})}
stage.addEventListener('pointerdown',e=>{if(e.target===svg||e.target===world||e.target===edges){panning={sx:e.clientX,sy:e.clientY,tx,ty}}});stage.addEventListener('pointermove',e=>{if(panning){tx=panning.tx+e.clientX-panning.sx;ty=panning.ty+e.clientY-panning.sy;applyTransform()}});stage.addEventListener('pointerup',()=>panning=null);stage.addEventListener('wheel',e=>{e.preventDefault();let old=scale;scale=Math.max(.35,Math.min(2.2,scale*(e.deltaY<0?1.1:.9)));tx=e.offsetX-(e.offsetX-tx)*scale/old;ty=e.offsetY-(e.offsetY-ty)*scale/old;applyTransform()},{passive:false});
function fit(){let box=world.getBBox(),r=stage.getBoundingClientRect();if(!box.width)return;scale=Math.min((r.width-60)/box.width,(r.height-60)/box.height,1);tx=(r.width-box.width*scale)/2-box.x*scale;ty=(r.height-box.height*scale)/2-box.y*scale;applyTransform()}
document.querySelector('#fit').onclick=fit;document.querySelector('#zoomin').onclick=()=>{scale=Math.min(2.2,scale*1.15);applyTransform()};document.querySelector('#zoomout').onclick=()=>{scale=Math.max(.35,scale/1.15);applyTransform()};document.querySelector('#reset').onclick=()=>{selected=null;render();fit()};
const fmt=cols=>cols.join(', '),isUniqueFk=l=>{let t=tableBy[l.target],cols=l.fk.columns;return t.indexes.some(i=>i.unique&&i.columns.length===cols.length&&cols.every(c=>i.columns.includes(c)))||(cols.length===t.columns.filter(c=>c.pk).length&&cols.every(name=>t.columns.find(col=>col.name===name)?.pk))};let m2m=[];DATA.tables.forEach(t=>{let rels=links.filter(l=>l.target===t.name);if(rels.length<2)return;for(let i=0;i<rels.length;i++)for(let j=i+1;j<rels.length;j++)if(rels[i].source!==rels[j].source)m2m.push({a:rels[i].source,b:rels[j].source,via:t.name})});document.querySelector('#relations').innerHTML=links.map(l=>{let oneOne=isUniqueFk(l);return `<div class="side-card"><b>${esc(l.source)} <span class="muted">${oneOne?'1:1':'1:N'}</span> ${esc(l.target)}</b><div>${esc(fmt(l.fk.targetColumns))} → ${esc(fmt(l.fk.columns))}</div><div>${l.explicit?'FOREIGN KEY · '+esc(l.fk.name):'Relación inferida por convención'}</div></div>`}).join('')+m2m.map(r=>`<div class="side-card"><b>${esc(r.a)} <span class="muted">N:M</span> ${esc(r.b)}</b><div>Asociación mediante ${esc(r.via)}</div></div>`).join('')||'<div class="muted">Sin relaciones detectadas</div>';
document.querySelector('#legend').innerHTML='<span><i class="dot"></i> PK</span><span class="fk">◇ FK</span><span class="idx">▤ índice</span><span>— FK declarada</span><span class="fk">┄ relación inferida</span>';
document.querySelector('#views').innerHTML=DATA.views.map(v=>`<div class="side-card"><b>${esc(v.name)}</b><div>${esc(v.sources.join(', ')||'No se detectaron tablas fuente')}</div></div>`).join('');
render();requestAnimationFrame(()=>fit());
</script></body></html>'''.replace("__DB__", "db_test_7b")

if __name__ == "__main__":
    main()
