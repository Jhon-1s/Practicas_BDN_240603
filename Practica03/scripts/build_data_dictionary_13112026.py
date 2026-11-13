"""Generate a self-contained dictionary for backups/respaldo13112026.sql."""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "backups" / "respaldo13112026.sql"
OUT = ROOT / "diccionario_datos.html"
sys.path.insert(0, str(ROOT / "scripts"))
from build_eer_interactive import analyze, sample_value, split_top


PURPOSE = {
    "tb_users": "Cuentas de usuario y credenciales de acceso.",
    "tb_people": "Información personal asociada a cuentas de usuario.",
    "tb_products": "Catálogo de productos y sus datos de inventario y precio.",
    "tbc_categories": "Catálogo jerárquico de categorías de productos.",
    "tb_carts": "Carritos de compra creados por usuarios.",
    "tbd_cart_items": "Productos y cantidades agregados a los carritos.",
    "tb_orders": "Órdenes de compra, sus importes y estado.",
    "tbd_order_items": "Renglones de productos incluidos en órdenes.",
    "tb_payments": "Pagos registrados para órdenes de compra.",
    "tb_payment_methods": "Métodos de pago registrados para operaciones.",
    "tbc_payment_methods_types": "Catálogo de tipos de método de pago.",
    "tb_payment_transaction": "Transacciones asociadas a pagos.",
    "tb_refunds": "Reembolsos asociados a pagos.",
    "tb_returns": "Devoluciones de órdenes de compra.",
    "tbd_return_items": "Productos incluidos en devoluciones.",
    "tb_order_cancellations": "Cancelaciones de órdenes y sus motivos o estados.",
    "tbd_cancellation_items": "Productos incluidos en cancelaciones.",
    "tb_shipments": "Envíos de órdenes y su información de seguimiento.",
    "tb_user_addresses": "Direcciones de usuarios para entrega o contacto.",
    "tbd_address_components": "Componentes jerárquicos de una dirección.",
    "tbd_products_categories": "Asociación de muchos a muchos entre productos y categorías.",
    "tbd_products_users_providers": "Asociación entre productos, usuarios y proveedores.",
    "tbd_user_payment_methods": "Métodos de pago tokenizados asociados a usuarios.",
    "tbd_users_wishlist_products": "Productos guardados por usuarios en listas de deseos.",
    "tb_logs": "Bitácora de operaciones registradas en la base de datos.",
}

FIELD_HELP = {
    "email": "Correo electrónico de la cuenta o contacto.", "nick": "Nombre corto o alias público.",
    "password": "Credencial de autenticación almacenada por la aplicación.",
    "name": "Nombre o etiqueta legible del registro.", "given_names": "Nombres de la persona.",
    "family_names": "Apellidos de la persona.", "sku": "Código de inventario o identificación comercial del producto.",
    "description": "Descripción textual del registro.", "current_price": "Precio vigente del producto.",
    "unit_price": "Precio por unidad aplicado al renglón.", "subtotal": "Importe parcial calculado para el renglón.",
    "total_amount": "Importe total asociado a la operación.", "amount": "Importe monetario de la operación.",
    "quantity": "Cantidad de unidades.", "current_stock": "Existencias disponibles del producto.",
    "status": "Estado operativo del registro.", "payment_status": "Estado del pago.",
    "creation_date": "Fecha y hora de creación del registro.", "created_at": "Fecha y hora de creación del registro.",
    "last_update": "Fecha y hora de la última actualización.", "updated_at": "Fecha y hora de la última actualización.",
    "birth_date": "Fecha de nacimiento.", "phone": "Número telefónico de contacto.",
    "recipient_name": "Nombre de quien recibe el envío.", "recipient_phone": "Teléfono de quien recibe el envío.",
    "is_default": "Indica si este registro es la opción predeterminada.",
    "operation_date": "Fecha y hora de la operación registrada.", "table_name": "Tabla sobre la que se registró la operación.",
    "table_operation": "Tipo de operación realizada.", "db_users": "Usuario de base de datos que realizó la operación.",
    "table_description": "Detalle del cambio registrado en la bitácora.", "tracking_number": "Número de seguimiento del envío.",
    "latitude": "Coordenada geográfica de latitud.", "longitude": "Coordenada geográfica de longitud.",
    "default_address": "Indica si la dirección es la principal del usuario.",
    "provider_method_ref": "Referencia del método tokenizado en el proveedor de pagos.",
    "last_four": "Últimos cuatro dígitos visibles del método de pago.",
    "on_delete": "Regla aplicada cuando se elimina el registro referenciado.",
}


def unquote_sql(s):
    return s.replace("\\'", "'").replace("''", "'").replace("\\\\", "\\")


def get_comments(sql, data):
    by = {t["name"]: t for t in data["tables"]}
    create = re.compile(r"CREATE\s+TABLE\s+`([^`]+)`\s*\((.*?)\)\s*ENGINE\s*=.*?;", re.I | re.S)
    for m in create.finditer(sql):
        t = by.get(m.group(1))
        if not t: continue
        for item in split_top(m.group(2)):
            col = re.match(r"`([^`]+)`\s+(.+)$", item, re.S)
            if not col: continue
            c = next((x for x in t["columns"] if x["name"] == col.group(1)), None)
            cm = re.search(r"\bCOMMENT\s+'((?:\\.|''|[^'])*)'", col.group(2), re.I | re.S)
            if c and cm: c["comment"] = unquote_sql(cm.group(1))
        cm = re.search(r"\bCOMMENT\s*=\s*'((?:\\.|''|[^'])*)'", sql[m.end(2):m.end()], re.I | re.S)
        if cm: t["comment"] = unquote_sql(cm.group(1))


def iter_rows(tail):
    """Yield VALUES tuples, preserving quotes and parentheses in each value."""
    quote = None; escape = False; depth = 0; start = None; i = 0
    while i < len(tail):
        ch = tail[i]
        if quote:
            if escape: escape = False
            elif ch == "\\": escape = True
            elif ch == quote:
                if i + 1 < len(tail) and tail[i + 1] == quote: i += 1
                else: quote = None
        elif ch in "'\"`": quote = ch
        elif ch == "(":
            if depth == 0: start = i + 1
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start is not None:
                yield split_top(tail[start:i]); start = None
        elif ch == ";" and depth == 0: break
        i += 1


def column_description(table, column):
    if column.get("comment"): return column["comment"]
    if column["pk"]: return "Clave primaria que identifica esta fila."
    if column["fk"]: return "Referencia a la entidad destino indicada en las restricciones de la tabla."
    name = column["name"].lower()
    if name in FIELD_HELP: return FIELD_HELP[name]
    if name.endswith("_id") or name.startswith("id_"):
        return "Identificador relacionado con la entidad nombrada por el campo."
    if name.endswith(("_date", "_at")): return "Fecha u hora relacionada con el registro."
    if name.startswith(("is_", "has_")): return "Indicador booleano o de estado."
    if "phone" in name: return "Número telefónico de contacto."
    if "address" in name: return "Dato de dirección o entrega."
    if "status" in name or "type" in name: return "Clasificación o estado funcional del registro."
    return "Descripción inferida a partir del nombre del atributo y su tipo de dato."


def enrich(sql):
    data = analyze(sql)
    get_comments(sql, data)
    by = {t["name"]: t for t in data["tables"]}
    for t in data["tables"]:
        t["purpose"] = t.get("comment") or PURPOSE.get(t["name"], "Propósito inferido del nombre y las relaciones de la tabla.")
        fks_by_col = {c: (f, i) for f in t["foreignKeys"] for i, c in enumerate(f["columns"])}
        for ordinal, c in enumerate(t["columns"], 1):
            c["ordinal"] = ordinal
            c["description"] = column_description(t, c)
            c["indexNames"] = [i["name"] for i in t["indexes"] if not i.get("primary") and c["name"] in i["columns"]]
            if c["name"] in fks_by_col:
                f, i = fks_by_col[c["name"]]
                c["reference"] = {"table": f["target"], "column": f["targetColumns"][i],
                    "onDelete": f.get("onDelete") or "NO ACTION (implícito)",
                    "onUpdate": f.get("onUpdate") or "NO ACTION (implícito)"}
            else: c["reference"] = None
            c["nullCount"] = 0; c["observed"] = 0
            c["distinctValues"] = []
            c["enumValues"] = re.findall(r"'(.*?)'", c["type"])[0:] if c["type"].lower().startswith("enum(") else []
        t["entityType"] = ("Catálogo" if t["name"].startswith("tbc_") else
                           "Pivote / intermedia" if t["kind"].startswith("Pivote") else
                           "Entidad débil / subtipo" if t["kind"].startswith("Débil") else
                           "Transaccional" if any(k in t["name"] for k in ("order", "payment", "return", "refund", "shipment", "cancellation", "cart", "transaction", "log")) else "Entidad")
    tracked = {}
    for t in data["tables"]:
        tracked[t["name"]] = {c["name"]: set() for c in t["columns"] if
            c["type"].lower().startswith("enum(") or re.search(r"status|type|gender|country|operation|ownership", c["name"], re.I)}
    ins = re.compile(r"INSERT\s+INTO\s+`([^`]+)`(?:\s*\(([^)]*)\))?\s+VALUES\s+", re.I)
    for m in ins.finditer(sql):
        t = by.get(m.group(1))
        if not t: continue
        names = re.findall(r"`([^`]+)`", m.group(2) or "") or [c["name"] for c in t["columns"]]
        cby = {c["name"]: c for c in t["columns"]}
        for row in iter_rows(sql[m.end():]):
            for name, raw in zip(names, row):
                c = cby.get(name)
                if c is None: continue
                c["observed"] += 1
                val = sample_value(raw)
                if val is None: c["nullCount"] += 1
                elif len(c["samples"]) < 5 and val not in c["samples"]: c["samples"].append(val)
                if name in tracked[t["name"]] and val is not None: tracked[t["name"]][name].add(str(val))
    for t in data["tables"]:
        for c in t["columns"]:
            c["nullPercent"] = round(100*c["nullCount"]/c["observed"], 1) if c["observed"] else None
            values = tracked[t["name"]].get(c["name"])
            if values is not None:
                c["distinctCount"] = len(values)
                c["distinctValues"] = sorted(values)[:20]
    data["backupFile"] = SQL.name
    data["backupDate"] = "13/11/2026"
    data["engine"] = "MySQL / InnoDB"
    data["ddlCounts"] = {"createTable": len(re.findall(r"CREATE\s+TABLE\b", sql, re.I)),
                         "alterTable": len(re.findall(r"ALTER\s+TABLE\b", sql, re.I)),
                         "createIndex": len(re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX\b", sql, re.I))}
    return data


PAGE = r'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Diccionario de datos · __DB__</title>
<style>
:root{color-scheme:light;--bg:#f3f6fa;--paper:#fff;--ink:#172438;--muted:#687990;--line:#dce4ed;--accent:#3468af;--accent-soft:#eaf1fb;--green:#217553;--purple:#7250a0;--gold:#90641c;--shadow:0 7px 24px #1c35500c}body.dark{color-scheme:dark;--bg:#0c121b;--paper:#121c28;--ink:#e6edf6;--muted:#9baac0;--line:#28384c;--accent:#79a9f2;--accent-soft:#1b2a40;--green:#76d6a9;--purple:#c0a0ef;--gold:#efc477;--shadow:0 7px 24px #0003}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:13px/1.48 Inter,Segoe UI,Arial,sans-serif}header{position:sticky;top:0;z-index:4;background:var(--paper);border-bottom:1px solid var(--line);padding:14px 22px;display:flex;gap:18px;align-items:center}.brand{min-width:210px}.eyebrow{text-transform:uppercase;letter-spacing:.16em;color:var(--accent);font-size:9px;font-weight:800}h1{font-size:19px;margin:2px 0}.muted{color:var(--muted)}.dashboard{display:flex;gap:7px}.metric{padding:6px 10px;border:1px solid var(--line);border-radius:9px;font-size:10px;color:var(--muted);white-space:nowrap}.metric b{font-size:15px;color:var(--ink);margin-right:5px}.search{flex:1;min-width:180px}input[type=search]{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);font:inherit}.buttons{display:flex;gap:6px}button,.button{border:1px solid var(--line);border-radius:7px;background:var(--paper);color:var(--ink);padding:7px 9px;font:inherit;cursor:pointer;white-space:nowrap}button:hover{border-color:var(--accent);color:var(--accent)}.layout{display:grid;grid-template-columns:250px minmax(0,1fr);min-height:calc(100vh - 68px)}aside{position:sticky;top:68px;align-self:start;height:calc(100vh - 68px);overflow:auto;background:var(--paper);border-right:1px solid var(--line);padding:15px 10px}.navtitle{font-size:10px;text-transform:uppercase;letter-spacing:.13em;color:var(--muted);padding:4px 8px 9px}.navitem{display:flex;justify-content:space-between;gap:5px;padding:6px 8px;color:var(--ink);text-decoration:none;border-radius:6px;font-size:11px}.navitem:hover,.navitem.active{background:var(--accent-soft);color:var(--accent)}.navcount{font-size:9px;color:var(--muted)}.filterbox{padding:10px 8px;border-top:1px solid var(--line);margin-top:9px;color:var(--muted);font-size:11px}.filterbox label{display:block;margin:7px 0;cursor:pointer}.filterbox input{accent-color:var(--accent)}main{min-width:0;padding:20px clamp(12px,2.5vw,34px) 70px;max-width:1700px;width:100%;margin:auto}.summary{display:flex;justify-content:space-between;align-items:end;margin-bottom:14px}.summary h2{margin:0;font-size:16px}.tablecard{background:var(--paper);border:1px solid var(--line);border-radius:11px;margin:0 0 16px;box-shadow:var(--shadow);scroll-margin-top:84px;transition:box-shadow .25s,outline .25s}.tablecard.flash{outline:3px solid #78a6e880;box-shadow:0 0 0 7px #78a6e822}.tablehead{display:flex;justify-content:space-between;gap:12px;padding:14px 16px;border-bottom:1px solid var(--line)}.tablehead h3{font-size:16px;margin:0}.purpose{color:var(--muted);font-size:11px;margin-top:3px}.badges{display:flex;gap:5px;flex-wrap:wrap;justify-content:end}.badge{border:1px solid var(--line);border-radius:99px;padding:3px 7px;font-size:9px;color:var(--muted)}.badge.rows{color:var(--green);background:#eaf6ef;border-color:#cde9d8}.dark .badge.rows{background:#132c24;border-color:#244c3c}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;min-width:1390px;font-size:10px}th{text-align:left;position:sticky;top:66px;z-index:1;background:var(--bg);padding:8px;border-bottom:1px solid var(--line);font-size:9px;text-transform:uppercase;letter-spacing:.045em;color:var(--muted)}td{padding:8px;border-bottom:1px solid var(--line);vertical-align:top}tr:last-child td{border-bottom:0}tr:hover{background:var(--accent-soft)}tr.hit{background:#fff2c7}.dark tr.hit{background:#493a20}.field{font-weight:700;white-space:nowrap;cursor:pointer}.type,.sample,.code{font-family:Consolas,'Courier New',monospace}.type{white-space:nowrap;color:var(--accent)}.sample{font-size:9px;color:var(--green);overflow-wrap:anywhere;max-width:230px}.keybadge{display:inline-block;border:1px solid var(--line);border-radius:4px;padding:1px 4px;margin:0 2px 2px 0;font-size:8px;font-weight:700}.pk{color:var(--green)}.fk{color:var(--purple)}.uk{color:var(--gold)}.idx{color:var(--accent)}.nullable{white-space:nowrap}.ref{border:0;background:none;padding:0;color:var(--purple);text-decoration:underline;cursor:pointer;text-align:left;font:10px Consolas,monospace}.extra{padding:10px 15px;border-top:1px solid var(--line);font-size:10px}.extra summary{cursor:pointer;color:var(--accent);font-weight:700}.extra pre{white-space:pre-wrap;overflow-wrap:anywhere;color:var(--muted)}.hidden{display:none!important}.empty{padding:30px;text-align:center;color:var(--muted)}.toast{position:fixed;right:18px;bottom:18px;background:var(--ink);color:var(--paper);padding:9px 13px;border-radius:8px;opacity:0;transition:.2s;pointer-events:none}.toast.show{opacity:1}.no-print{}@media(max-width:1100px){header{flex-wrap:wrap}.dashboard{order:3;flex-wrap:wrap}.search{order:2;flex-basis:45%}.layout{grid-template-columns:210px minmax(0,1fr)}}@media(max-width:700px){.layout{grid-template-columns:1fr}aside{position:static;height:auto;max-height:210px;border-right:0;border-bottom:1px solid var(--line);columns:2}.filterbox{column-span:all}.buttons{flex-wrap:wrap}.dashboard{display:none}main{padding:12px}}
@media print{body{background:white;color:#111;font-size:9px}header{position:static;padding:8px;border:0}.search,.buttons,aside{display:none!important}.layout{display:block;min-height:0}main{padding:0;max-width:none}.tablecard{box-shadow:none;break-inside:avoid;border:1px solid #bbb;margin-bottom:10px}.scroll{overflow:visible}table{min-width:0;width:100%;font-size:7px}th{position:static;background:#eee;color:#222}td{padding:4px}.extra{display:block}.extra summary{display:none}.extra:not([open])>:not(summary){display:block}.badges .badge{color:#222}.purpose{color:#333}.no-print{display:none!important}}
</style></head><body><header><div class="brand"><div class="eyebrow">Diccionario de datos · __DB__</div><h1>Catálogo técnico</h1><div class="muted" style="font-size:10px">Respaldo __DATE__ · MySQL</div></div><div class="dashboard"><div class="metric"><b>__TABLES__</b>tablas</div><div class="metric"><b>__COLS__</b>columnas</div><div class="metric"><b>__FKS__</b>relaciones FK</div><div class="metric"><b>__ROWS__</b>registros</div></div><div class="search"><input id="q" type="search" placeholder="Buscar tabla, campo, tipo o descripción…"></div><div class="buttons"><button id="md">Markdown</button><button id="csv">CSV</button><button id="print">Imprimir / PDF</button><button id="theme">◐</button></div></header>
<div class="layout"><aside><div class="navtitle">Tablas <span id="navcount"></span></div><nav id="nav"></nav><div class="filterbox"><b>Filtros rápidos</b><label><input type="checkbox" id="fpk"> Contiene PK</label><label><input type="checkbox" id="ffk"> Contiene FK</label><label><input type="checkbox" id="fnull"> Acepta NULL</label><label><input type="checkbox" id="frows"> Con registros (&gt; 0)</label></div></aside><main><div class="summary"><div><h2>Inventario de tablas</h2><div id="sub" class="muted"></div></div><span class="muted">Orden alfabético · selección de campo para copiar</span></div><div id="docs"></div><div id="none" class="empty hidden">No hay coincidencias con los filtros actuales.</div><div class="muted no-print" style="font-size:10px;margin:14px 0">Los conteos y estadísticas se calculan sobre valores explícitos de sentencias INSERT del respaldo. La nulabilidad observada considera filas que incluyen la columna.</div></main></div><div id="toast" class="toast"></div>
<script>const D=__DATA__,nf=n=>Number(n||0).toLocaleString('es-MX'),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const tableBy=Object.fromEntries(D.tables.map(t=>[t.name,t]));
const detailCount=D.tables.reduce((a,t)=>a+t.columns.length,0),fkCount=D.tables.reduce((a,t)=>a+t.foreignKeys.length,0),rowCount=D.tables.reduce((a,t)=>a+t.count,0);document.querySelector('#sub').textContent=`${D.database} · ${D.engine} · respaldo ${D.backupDate} · ${D.ddlCounts.createTable} CREATE TABLE / ${D.ddlCounts.alterTable} ALTER TABLE`;
const sorted=[...D.tables].sort((a,b)=>a.name.localeCompare(b.name,'es'));const nav=document.querySelector('#nav');nav.innerHTML=sorted.map(t=>`<a class="navitem" href="#tbl-${encodeURIComponent(t.name)}" data-table="${esc(t.name)}"><span>${esc(t.name)}</span><span class="navcount">${nf(t.count)}</span></a>`).join('');document.querySelector('#navcount').textContent=`(${sorted.length})`;
function tags(c){return `${c.pk?'<span class="keybadge pk">PK</span>':''}${c.fk?'<span class="keybadge fk">FK</span>':''}${c.unique?'<span class="keybadge uk">UK</span>':''}${c.indexNames.filter(n=>!c.uniqueIndexes?.includes(n)).map(x=>`<span class="keybadge idx">IDX ${esc(x)}</span>`).join('')}`||'—'}
function vals(c){let values=c.samples.filter(x=>x!==null).slice(0,3);return values.length?values.map(x=>`<span class="sample">${esc(x)}</span>`).join('<br>'):'<span class="muted">Sin filas con muestra</span>'}
function reference(c){if(!c.reference)return '—';return `<button class="ref" data-table="${esc(c.reference.table)}" data-col="${esc(c.reference.column)}">${esc(c.reference.table)}.${esc(c.reference.column)}</button><div class="muted">ON DELETE ${esc(c.reference.onDelete)}<br>ON UPDATE ${esc(c.reference.onUpdate)}</div>`}
function restrictions(t,c){let bits=[];if(c.enumValues.length)bits.push('ENUM: '+c.enumValues.join(', '));for(const x of t.checks||[])if(!x.expression||x.expression.toLowerCase().includes(c.name.toLowerCase()))bits.push((x.name||'CHECK')+': '+x.expression);if(c.distinctCount!==undefined)bits.push(`${nf(c.distinctCount)} valores distintos`);return bits.length?bits.map(esc).join('<br>'):'—'}
function render(){document.querySelector('#docs').innerHTML=sorted.map(t=>{const matchT=t.name.toLowerCase(),fk=t.foreignKeys.length;return `<section class="tablecard" id="tbl-${esc(t.name)}" data-name="${esc(matchT)}" data-rows="${t.count}" data-pk="${t.columns.some(c=>c.pk)}" data-fk="${fk>0}" data-null="${t.columns.some(c=>c.nullable==='NULL')}"><div class="tablehead"><div><h3>${esc(t.name)}</h3><div class="purpose">${esc(t.purpose)}</div></div><div class="badges"><span class="badge rows">${nf(t.count)} registros</span><span class="badge">${esc(t.entityType)}</span><span class="badge">${t.columns.length} columnas</span><span class="badge">${esc(t.engine)}</span></div></div><div class="scroll"><table><thead><tr><th>#</th><th>Campo</th><th>Tipo de dato</th><th>Llaves / índices</th><th>Nulabilidad</th><th>Default / Extra</th><th>Restricciones / referencia</th><th>Descripción / ejemplos</th></tr></thead><tbody>${t.columns.map(c=>{const extras=[c.auto?'AUTO_INCREMENT':'',...(c.attributes||[]),c.default!==null?'DEFAULT '+c.default:''].filter(Boolean).join(' · ');const nullStat=c.nullPercent===null?'Sin dato':`${c.nullable}${c.nullPercent!==null?` · ${nf(c.nullCount)} NULL (${c.nullPercent}%)`:''}`;return `<tr data-col="${esc(c.name.toLowerCase())}" data-type="${esc(c.type.toLowerCase())}" data-search="${esc([c.name,c.type,c.description,extras,c.reference?.table||'',c.reference?.column||''].join(' ').toLowerCase())}"><td>${c.ordinal}</td><td class="field" title="Copiar nombre" data-copy="${esc(c.name)}">${esc(c.name)}</td><td class="type">${esc(c.type)}</td><td>${tags(c)}</td><td class="nullable">${esc(nullStat)}</td><td class="code">${extras?esc(extras):'—'}</td><td>${restrictions(t,c)}${c.reference?'<hr style="border:0;border-top:1px solid var(--line)">'+reference(c):''}</td><td>${esc(c.description)}<div style="margin-top:4px">${vals(c)}</div></td></tr>`}).join('')}</tbody></table></div><details class="extra"><summary>Índices y restricciones de tabla</summary><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:9px"><div><b>Índices</b>${t.indexes.map(i=>`<div>${esc(i.name)} · ${i.primary?'PRIMARY':i.unique?'UNIQUE':i.type} (${esc(i.columns.join(', '))})</div>`).join('')||'<div class="muted">Sin índices</div>'}</div><div><b>Claves foráneas</b>${t.foreignKeys.map(f=>`<div>${esc(f.name)} (${esc(f.columns.join(', '))}) → ${esc(f.target)}(${esc(f.targetColumns.join(', '))}) · DELETE ${esc(f.onDelete||'NO ACTION')} · UPDATE ${esc(f.onUpdate||'NO ACTION')}</div>`).join('')||'<div class="muted">Sin FK</div>'}</div><div><b>CHECK / comentario</b>${(t.checks||[]).map(x=>`<div>${esc(x.name||'CHECK')}: ${esc(x.expression)}</div>`).join('')||'<div class="muted">Sin CHECK</div>'}${t.comment?`<div>${esc(t.comment)}</div>`:''}</div></div></details></section>`}).join('');bind();filter()}
function bind(){document.querySelectorAll('.field').forEach(el=>el.onclick=async()=>{try{await navigator.clipboard.writeText(el.dataset.copy);toast(`Copiado: ${el.dataset.copy}`)}catch{toast(el.dataset.copy)}});document.querySelectorAll('.ref').forEach(el=>el.onclick=()=>{const target=document.querySelector(`#tbl-${CSS.escape(el.dataset.table)}`);if(!target)return;document.querySelector('#q').value='';filter();target.scrollIntoView({behavior:'smooth',block:'start'});target.classList.add('flash');const row=[...target.querySelectorAll('tr[data-col]')].find(r=>r.dataset.col===el.dataset.col.toLowerCase());if(row)row.classList.add('hit');setTimeout(()=>{target.classList.remove('flash');row?.classList.remove('hit')},1800)})}
function filter(){const q=document.querySelector('#q').value.trim().toLowerCase(),fpk=document.querySelector('#fpk').checked,ffk=document.querySelector('#ffk').checked,fn=document.querySelector('#fnull').checked,fr=document.querySelector('#frows').checked;let count=0;for(const t of sorted){const card=document.querySelector(`#tbl-${CSS.escape(t.name)}`),tableHit=!q||t.name.toLowerCase().includes(q)||t.purpose.toLowerCase().includes(q);let visibleRows=0;for(const row of card.querySelectorAll('tbody tr')){const c=t.columns.find(x=>x.name.toLowerCase()===row.dataset.col),hit=(tableHit||row.dataset.search.includes(q))&&(!fpk||c.pk)&&(!ffk||c.fk)&&(!fn||c.nullable==='NULL');row.classList.toggle('hidden',!hit);row.classList.toggle('hit',!!q&&!tableHit&&hit);if(hit)visibleRows++}const show=visibleRows>0&&(!fr||Number(card.dataset.rows)>0);card.classList.toggle('hidden',!show);if(show)count++;const link=nav.querySelector(`[data-table="${CSS.escape(t.name)}"]`);link?.classList.toggle('hidden',!show)}document.querySelector('#none').classList.toggle('hidden',count>0);document.querySelector('#navcount').textContent=`(${count}/${sorted.length})`}
document.querySelector('#q').addEventListener('input',filter);['fpk','ffk','fnull','frows'].forEach(id=>document.querySelector('#'+id).addEventListener('change',filter));document.querySelector('#print').onclick=()=>window.print();document.querySelector('#theme').onclick=()=>document.body.classList.toggle('dark');
function csvQuote(x){return '"'+String(x??'').replaceAll('"','""')+'"'}function download(name,type,text){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);toast('Exportado: '+name)}
document.querySelector('#csv').onclick=()=>{const rows=[['tabla','tipo_tabla','registros','proposito','ordinal','campo','tipo_dato','llaves_indices','nulabilidad','nulos_observados_pct','default_extra','restricciones','referencia','on_delete','on_update','descripcion','ejemplos']];for(const t of sorted)for(const c of t.columns)rows.push([t.name,t.entityType,t.count,t.purpose,c.ordinal,c.name,c.type,[c.pk?'PK':'',c.fk?'FK':'',c.unique?'UK':'',...c.indexNames].filter(Boolean).join('|'),c.nullable,c.nullPercent??'',[(c.auto?'AUTO_INCREMENT':''),...(c.attributes||[]),c.default!==null?'DEFAULT '+c.default:''].filter(Boolean).join('|'),[...c.enumValues,...(t.checks||[]).map(x=>x.expression)].join('|'),c.reference?.table+'.'+c.reference?.column||'',c.reference?.onDelete||'',c.reference?.onUpdate||'',c.description,c.samples.slice(0,3).join(' | ')]);download('diccionario_datos_13112026.csv','text/csv;charset=utf-8','\ufeff'+rows.map(r=>r.map(csvQuote).join(',')).join('\r\n'))};
document.querySelector('#md').onclick=()=>{let out=`# Diccionario de datos — ${D.database}\n\n- Motor: ${D.engine}\n- Respaldo: ${D.backupFile} (${D.backupDate})\n- Tablas: ${D.tables.length}\n- Columnas: ${detailCount}\n- Relaciones FK: ${fkCount}\n- Registros insertados: ${nf(rowCount)}\n\n`;for(const t of sorted){out+=`## ${t.name}\n\n${t.purpose}\n\n- Tipo: ${t.entityType}\n- Registros: ${nf(t.count)}\n\n`;out+='Índices: '+t.indexes.map(i=>`${i.name} (${i.columns.join(', ')})`).join('; ')+'\n\n';out+=`| # | Campo | Tipo | Llaves | Null | Default/Extra | Restricciones y referencia | Descripción y ejemplos |\n|---:|---|---|---|---|---|---|---|\n`;for(const c of t.columns){const ref=c.reference?`${c.reference.table}.${c.reference.column} (DELETE ${c.reference.onDelete}; UPDATE ${c.reference.onUpdate})`:'';const rest=[...c.enumValues,...(t.checks||[]).map(x=>x.expression),ref].join('; ').replaceAll('|','\\|');out+=`| ${c.ordinal} | ${c.name} | ${c.type} | ${[c.pk?'PK':'',c.fk?'FK':'',c.unique?'UK':'',...c.indexNames].filter(Boolean).join(', ')} | ${c.nullable} | ${[c.auto?'AUTO_INCREMENT':'',...(c.attributes||[]),c.default!==null?'DEFAULT '+c.default:''].filter(Boolean).join(', ')} | ${rest} | ${c.description}; ${c.samples.slice(0,3).join(', ')} |\n`}out+='\n'}download('diccionario_datos_13112026.md','text/markdown;charset=utf-8',out)};
let toastTimer;function toast(s){const el=document.querySelector('#toast');el.textContent=s;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),1800)}render();</script></body></html>'''


def main():
    sql = SQL.read_text(encoding="utf-8", errors="replace")
    data = enrich(sql)
    total_rows = sum(t["count"] for t in data["tables"])
    total_cols = sum(len(t["columns"]) for t in data["tables"])
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = PAGE.replace("__DATA__", payload).replace("__DB__", html.escape(data["database"])).replace("__DATE__", data["backupDate"])
    page = page.replace("__TABLES__", nf_fmt(len(data["tables"]))).replace("__COLS__", nf_fmt(total_cols))
    page = page.replace("__FKS__", nf_fmt(sum(len(t["foreignKeys"]) for t in data["tables"]))).replace("__ROWS__", nf_fmt(total_rows))
    OUT.write_text(page, encoding="utf-8")
    print(f"{OUT.name}: {len(data['tables'])} tablas, {total_cols} columnas, {sum(len(t['foreignKeys']) for t in data['tables'])} FK, {total_rows:,} registros")


def nf_fmt(value): return f"{value:,}"


if __name__ == "__main__": main()
