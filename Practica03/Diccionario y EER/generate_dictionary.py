import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path


WORK = Path(__file__).resolve().parent
PROJECT = WORK.parent
SQL = PROJECT / "backups" / "respaldo20261211.sql"
OUT = WORK / "Diccionario_Datos.html"
SOURCE = PROJECT / "scripts" / "build_data_dictionary.py"

spec = importlib.util.spec_from_file_location("dictionary_source", SOURCE)
dictionary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dictionary)
import build_eer as parser

dictionary.SQL = SQL
dictionary.OUT = OUT
parser.SQL = SQL


def repair_encoding(value):
    for _ in range(2):
        try:
            fixed = value.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if fixed == value:
            break
        value = fixed
    return value


PURPOSES = {
    "tb_carts": "Carritos de compra asociados a cuentas de usuario.",
    "tb_logs": "Bitácora de operaciones realizadas sobre los datos del sistema.",
    "tb_order_cancellations": "Motivos y fechas de cancelación de órdenes.",
    "tb_orders": "Órdenes de compra, dirección de entrega, importe y estado.",
    "tb_payment_methods": "Catálogo de métodos de pago disponibles.",
    "tb_payment_transaction": "Transacciones asociadas a pagos.",
    "tb_payments": "Pagos aplicados a órdenes y su estado de procesamiento.",
    "tb_people": "Información personal vinculada a una cuenta.",
    "tb_products": "Catálogo de productos, precios, inventario y disponibilidad.",
    "tb_refunds": "Solicitudes o registros de reembolso de pagos.",
    "tb_returns": "Devoluciones relacionadas con órdenes.",
    "tb_shipments": "Envíos, destinatarios y datos de seguimiento de órdenes.",
    "tb_user_addresses": "Direcciones y preferencias de entrega de usuarios.",
    "tb_users": "Cuentas de usuario y datos de acceso.",
    "tbc_categories": "Catálogo jerárquico para clasificar productos.",
    "tbc_payment_methods_types": "Catálogo de tipos de método de pago.",
    "tbd_address_components": "Componentes estructurados asociados a direcciones.",
    "tbd_cancellation_items": "Artículos incluidos en cancelaciones de órdenes.",
    "tbd_cart_items": "Productos y cantidades incluidos en carritos.",
    "tbd_order_items": "Renglones de producto pertenecientes a órdenes.",
    "tbd_products_categories": "Asociación de muchos a muchos entre productos y categorías.",
    "tbd_products_users_providers": "Asociación de productos con usuarios proveedores y su tipo de propiedad.",
    "tbd_return_items": "Artículos incluidos en devoluciones.",
    "tbd_user_payment_methods": "Métodos de pago tokenizados y asociados a usuarios.",
    "tbd_users_wishlist_products": "Productos guardados por usuarios en su lista de deseos.",
}

COLUMN_TEXT = {
    "status": "Estado o indicador de disponibilidad del registro; el dominio concreto depende del tipo SQL.",
    "creation_date": "Fecha y hora en que se creó el registro.",
    "last_update": "Fecha y hora de la última actualización del registro.",
    "created_at": "Fecha y hora en que se creó el registro.",
    "updated_at": "Fecha y hora de la última actualización del registro.",
    "email": "Dirección de correo electrónico de la cuenta o contacto.",
    "nick": "Nombre corto o alias público del usuario.",
    "name": "Nombre visible del elemento.",
    "description": "Descripción textual del elemento.",
    "sku": "Código SKU usado para identificar el producto en el catálogo.",
    "current_price": "Precio vigente del producto en la moneda definida por la aplicación.",
    "price": "Precio o importe monetario asociado al registro.",
    "total_amount": "Importe total calculado para la orden o transacción.",
    "amount": "Importe monetario de la operación.",
    "quantity": "Unidades asociadas al renglón o movimiento.",
    "current_stock": "Existencias actuales del producto.",
    "stock": "Existencias registradas para el producto.",
    "is_default": "Indica si el registro es la opción predeterminada.",
    "latitude": "Coordenada geográfica de latitud.",
    "longitude": "Coordenada geográfica de longitud.",
    "birth_date": "Fecha de nacimiento de la persona.",
    "operation_date": "Fecha y hora de la operación registrada.",
    "table_name": "Nombre de la tabla afectada por la operación registrada.",
    "table_operation": "Operación registrada sobre los datos.",
    "db_users": "Usuario de base de datos que ejecutó la operación.",
    "table_description": "Detalle de la operación o cambio registrado en la bitácora.",
    "operation_status": "Resultado o indicador de estado de la operación registrada.",
    "provider": "Proveedor externo o procesador relacionado con el registro.",
    "provider_method_ref": "Referencia tokenizada del método de pago en el proveedor.",
    "last_four": "Últimos cuatro dígitos visibles del instrumento de pago.",
    "type_ownership": "Clasificación del tipo de propiedad o relación con el producto.",
    "is_default": "Indica si la dirección o método es el predeterminado.",
    "reason": "Motivo o justificación textual de la operación.",
    "tracking_number": "Código de seguimiento asignado al envío.",
    "status_date": "Fecha y hora asociada al cambio de estado.",
}


def description_for(table, column):
    if column.get("comment"):
        return column["comment"]
    if column["pk"]:
        return "Identificador único de la fila" + ("; generado automáticamente." if column["auto"] else ".")
    if column["fk"]:
        return f"Referencia a {column.get('reference') or 'la entidad padre'}; su integridad se rige por la llave foránea declarada."
    low = column["name"].lower()
    typ = column["type"] or ""
    enum = re.match(r"enum\((.*)\)", typ, re.I)
    if enum:
        values = re.findall(r"'((?:''|\\.|[^'])*)'", enum.group(1))
        domain = ", ".join(values) if values else enum.group(1)
        return f"Valor categórico del campo {column['name']}; valores permitidos por el tipo ENUM: {domain}."
    if low in COLUMN_TEXT:
        return COLUMN_TEXT[low]
    if low.startswith("is_") or low.startswith("has_") or typ.lower().startswith(("bit(1)", "boolean", "bool")):
        return f"Indicador lógico relacionado con {low.removeprefix('is_').removeprefix('has_').replace('_', ' ')}."
    if low.endswith("_date") or low.endswith("_at") or "timestamp" in typ.lower() or typ.lower().startswith("datetime"):
        return f"Fecha u hora relacionada con {low.replace('_', ' ')}."
    if "phone" in low:
        return "Número telefónico de contacto."
    if "address" in low:
        return "Dato relacionado con la dirección indicada por el nombre del campo."
    if "amount" in low or "price" in low or "total" in low:
        return "Importe o valor monetario asociado al registro."
    if low.startswith("id_") or low.endswith("_id"):
        return "Identificador de la entidad indicada por el nombre del campo."
    return f"Dato de {low.replace('_', ' ')} para {PURPOSES.get(table['name'], 'el registro')}."


def scan_objects(sql, data):
    triggers = []
    trigger_re = re.compile(
        r"\bTRIGGER\s+`([^`]+)`\s+(BEFORE|AFTER)\s+(INSERT|UPDATE|DELETE)\s+ON\s+`([^`]+)`\s+FOR EACH ROW(.*?)END\s*\*/",
        re.I | re.S,
    )
    for match in trigger_re.finditer(sql):
        triggers.append({
            "name": match.group(1), "timing": match.group(2).upper(),
            "event": match.group(3).upper(), "table": match.group(4),
            "body": match.group(5).strip(),
        })
    routines = []
    routine_re = re.compile(r"\b(PROCEDURE|FUNCTION)\s+`([^`]+)`", re.I)
    for match in routine_re.finditer(sql):
        opening = sql.find("(", match.end())
        depth, closing = 0, opening
        quote = None
        while closing < len(sql):
            ch = sql[closing]
            if quote:
                if ch == quote and (closing == 0 or sql[closing - 1] != "\\"):
                    quote = None
            elif ch in "'\"`":
                quote = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
            closing += 1
        parameters = re.sub(r"\s+", " ", sql[opening + 1:closing]).strip()
        terminator = sql.find("END ;;", closing)
        body = sql[match.start():terminator + 3] if terminator >= 0 else sql[match.start():closing + 1]
        routines.append({"kind": match.group(1).upper(), "name": match.group(2), "parameters": parameters, "body": body.strip()})
    alterations = []
    for match in re.finditer(r"\bALTER\s+TABLE\s+`([^`]+)`\s+(.*?);", sql, re.I | re.S):
        statement = re.sub(r"\s+", " ", match.group(0)).strip()
        if re.search(r"\b(ADD|DROP|MODIFY|CHANGE|RENAME|ALTER)\b", match.group(2), re.I):
            alterations.append({"table": match.group(1), "statement": statement})
    return {"triggers": triggers, "routines": routines, "alterations": alterations}


def collect_comments_and_checks(sql, data):
    table_re = re.compile(r"CREATE TABLE\s+`([^`]+)`\s*\((.*?)\)\s*ENGINE\s*=\s*(\w+)(.*?);", re.I | re.S)
    ddl = {m.group(1): (m.group(2), m.group(3), m.group(4)) for m in table_re.finditer(sql)}
    for table in data["tables"]:
        name = table["name"]
        body, engine, tail = ddl.get(name, ("", table.get("engine", "MySQL"), ""))
        table["engine"] = engine
        table_comment = re.search(r"\bCOMMENT\s*=\s*'((?:''|\\.|[^'])*)'", tail, re.I)
        table["comment"] = table_comment.group(1).replace("''", "'") if table_comment else None
        table["checks"] = []
        column_specs = {}
        for item in parser.split_sql_items(body):
            col = re.match(r"`([^`]+)`\s+(.+)$", item, re.S)
            if col:
                column_specs[col.group(1)] = col.group(2)
            if re.search(r"\bCHECK\s*\(", item, re.I):
                table["checks"].append(re.sub(r"\s+", " ", item).strip())
        for column in table["columns"]:
            spec = column_specs.get(column["name"], "")
            comment = re.search(r"\bCOMMENT\s+'((?:''|\\.|[^'])*)'", spec, re.I | re.S)
            column["comment"] = comment.group(1).replace("''", "'") if comment else None
            fk = next((f for f in table["foreignKeys"] if column["name"] in f["columns"]), None)
            if fk:
                pos = fk["columns"].index(column["name"])
                column["reference"] = f"{fk['target']}({fk['targetColumns'][pos]})"
            column["description"] = description_for(table, column)
            for check in table["checks"]:
                if re.search(r"`" + re.escape(column["name"]) + r"`", check, re.I):
                    column["description"] += " Regla CHECK: " + check + "."
        if table["comment"]:
            table["purpose"] = table["comment"]
        else:
            table["purpose"] = PURPOSES.get(name, f"Entidad de datos {name.replace('_', ' ')}.")


def build_data():
    sql = SQL.read_text(encoding="utf-8", errors="replace")
    data = dictionary.parse(sql)
    collect_comments_and_checks(sql, data)
    objects = scan_objects(sql, data)
    for table in data["tables"]:
        table["incomingForeignKeys"] = []
    for child in data["tables"]:
        for fk in child["foreignKeys"]:
            parent = next((t for t in data["tables"] if t["name"] == fk["target"]), None)
            if parent:
                parent["incomingForeignKeys"].append({
                    "table": child["name"], "name": fk["name"],
                    "columns": fk["columns"], "targetColumns": fk["targetColumns"],
                    "onDelete": fk["onDelete"], "onUpdate": fk["onUpdate"],
                })
    engines = Counter(t["engine"] for t in data["tables"])
    charsets = Counter(t["charset"] for t in data["tables"])
    collations = Counter(t["collation"] for t in data["tables"])
    total = sum(t["count"] for t in data["tables"])
    largest = max(data["tables"], key=lambda t: t["count"])
    data["objects"] = objects
    data["summary"] = {
        "engine": engines.most_common(1)[0][0],
        "charset": charsets.most_common(1)[0][0],
        "collation": collations.most_common(1)[0][0],
        "tableCount": len(data["tables"]), "rowCount": total,
        "largestTable": largest["name"], "largestCount": largest["count"],
        "columnCount": sum(len(t["columns"]) for t in data["tables"]),
        "foreignKeyCount": sum(len(t["foreignKeys"]) for t in data["tables"]),
        "viewCount": len(data["views"]), "triggerCount": len(objects["triggers"]),
        "routineCount": len(objects["routines"]), "alterCount": len(objects["alterations"]),
    }
    return data


def repair_html_encoding(text):
    for _ in range(2):
        try:
            fixed = text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if fixed == text:
            break
        text = fixed
    return text


html = repair_html_encoding(dictionary.HTML)
html = html.replace("Fuente: respaldo20261111.sql", "Fuente: respaldo20261211.sql")
html = html.replace("Archivo: respaldo20261111.sql", "Archivo: respaldo20261211.sql")
html = html.replace("diccionario_datos_respaldo20261111", "diccionario_datos_respaldo20261211")
html = html.replace(
    "Sin tablas hijas con FK declarada.</div>'}</div></div></section>",
    "Sin tablas hijas con FK declarada.</div>'}</div><div><h4>Restricciones CHECK</h4>${t.checks.length?t.checks.map(c=>`<div class=\"fk-item\"><code>${esc(c)}</code></div>`).join(''):'<div class=\"empty\">Sin restricciones CHECK declaradas.</div>'}</div></div></section>",
)
html = html.replace(
    "<button id=\"csv\">Exportar CSV</button>",
    "<button id=\"md\">Exportar Markdown</button><button id=\"csv\">Exportar CSV</button>",
)
html = html.replace(
    '<div id="dictionary"></div>',
    '<div id="executive"></div><section class="table-card index-card"><div class="table-head"><div><h3>Índice general de entidades</h3><div class="purpose">Volumen, estructura y dependencias por tabla</div></div></div><div id="entity-index" class="matrix-wrap"></div></section><section class="table-card index-card"><div class="table-head"><div><h3>Vistas, disparadores, rutinas y alteraciones</h3><div class="purpose">Objetos declarados en el respaldo SQL</div></div></div><div id="objects" class="objects-grid"></div></section><div class="filters" id="filters"><span>Filtros:</span><button data-filter="pk">Tablas con PK</button><button data-filter="fk">Tablas con FK</button><button data-filter="rows">Con datos (&gt; 0)</button><button data-filter="clear">Limpiar</button></div><div id="dictionary"></div>',
)
html = html.replace(
    "function render(){document.querySelector('#nav').innerHTML=",
    "function render(){renderExecutive();renderIndex();renderObjects();document.querySelector('#nav').innerHTML=",
)
html = html.replace(
    "function render(){renderExecutive();renderIndex();renderObjects();document.querySelector('#nav').innerHTML=",
    "function render(){renderExecutive();renderIndex();renderObjects();document.querySelector('#nav').innerHTML=",
)
html = html.replace(
    "<section class=\"table-card\" id=\"t-${esc(t.name)}\" data-name=\"${esc(t.name.toLowerCase())}\" data-search=\"${esc([t.name,...t.columns.flatMap(c=>[c.name,c.type,c.description,c.default||''])].join(' ').toLowerCase())}\">",
    "<section class=\"table-card\" id=\"t-${esc(t.name)}\" data-name=\"${esc(t.name.toLowerCase())}\" data-pk=\"${t.columns.some(c=>c.pk)}\" data-fk=\"${t.foreignKeys.length>0}\" data-rows=\"${t.count>0}\" data-search=\"${esc([t.name,t.purpose,...t.columns.flatMap(c=>[c.name,c.type,c.description,c.default||''])].join(' ').toLowerCase())}\">",
)
html = html.replace("<th>Nombre del campo</th>", "<th>#</th><th>Nombre del campo</th>")
html = html.replace("t.columns.map(c=>{let tags=[];", "t.columns.map((c,i)=>{let tags=[];")
html = html.replace('<td class="field">${esc(c.name)}</td>', '<td>${i+1}</td><td class="field">${esc(c.name)}</td>')
html = html.replace(
    "</div></div></section>`).join('');filter('')}",
    "</div><div><h4>Relaciones entrantes</h4>${t.incomingForeignKeys.length?t.incomingForeignKeys.map(f=>`<div class=\"fk-item\"><code>${esc(f.table)}(${f.columns.map(esc).join(', ')})</code> â†’ ${esc(t.name)}(${f.targetColumns.map(esc).join(', ')}) Â· ${esc(f.name)}</div>`).join(''):'<div class=\"empty\">Sin tablas hijas con FK declarada.</div>'}</div></div></section>`).join('');filter('')}",
)
html = html.replace(
    "function filter(q){q=q.trim().toLowerCase();let visible=0;document.querySelectorAll('.table-card').forEach(card=>{let found=!q||card.dataset.search.includes(q);",
    "const activeFilters=new Set();function filter(q){q=q.trim().toLowerCase();let visible=0;document.querySelectorAll('#dictionary .table-card').forEach(card=>{let found=(!q||card.dataset.search.includes(q))&&(!activeFilters.has('pk')||card.dataset.pk==='true')&&(!activeFilters.has('fk')||card.dataset.fk==='true')&&(!activeFilters.has('rows')||card.dataset.rows==='true');",
)
html = html.replace(
    "document.querySelector('#q').addEventListener('input',e=>filter(e.target.value));",
    "document.querySelector('#q').addEventListener('input',e=>filter(e.target.value));document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{let f=b.dataset.filter;if(f==='clear'){activeFilters.clear();document.querySelectorAll('[data-filter]').forEach(x=>x.classList.remove('active'))}else{activeFilters.has(f)?activeFilters.delete(f):activeFilters.add(f);b.classList.toggle('active',activeFilters.has(f))}filter(document.querySelector('#q').value)});",
)
html = html.replace(
    "document.querySelector('#json').onclick=()=>download(",
    "document.querySelector('#md').onclick=()=>download('diccionario_datos_respaldo20261211.md','text/markdown;charset=utf-8',toMarkdown());document.querySelector('#json').onclick=()=>download(",
)
html = html.replace(
    "let timer;function toast(s)",
    "function toMarkdown(){const escMd=x=>String(x??'').replaceAll('|','\\\\|').replaceAll('\\n',' '),rows=['# Diccionario de datos Â· '+DATA.database,'','## Resumen ejecutivo','','- Motor: '+DATA.summary.engine,'- Charset / collation: '+DATA.summary.charset+' / '+DATA.summary.collation,'- Tablas: '+DATA.summary.tableCount,'- Columnas: '+DATA.summary.columnCount,'- Registros incluidos: '+nf(DATA.summary.rowCount),'- Tabla con más filas: '+DATA.summary.largestTable+' ('+nf(DATA.summary.largestCount)+')','- Vistas: '+DATA.summary.viewCount,'- Triggers: '+DATA.summary.triggerCount,'- Rutinas: '+DATA.summary.routineCount,'- ALTER estructurales: '+DATA.summary.alterCount,'','## Índice general','','| Tabla | Propósito | Columnas | FK salientes | FK entrantes | Registros |','|---|---|---:|---:|---:|---:|'];DATA.tables.forEach(t=>rows.push('| '+escMd(t.name)+' | '+escMd(t.purpose)+' | '+t.columns.length+' | '+t.foreignKeys.length+' | '+t.incomingForeignKeys.length+' | '+nf(t.count)+' |'));DATA.tables.forEach(t=>{rows.push('','## '+t.name,'',t.purpose+' · '+t.engine+' · '+nf(t.count)+' registros','','| # | Nombre del Campo | Tipo de Dato y Longitud | Restricciones / Llaves | Nulabilidad | Valor por Defecto | Descripción y Reglas de Negocio |','|---:|---|---|---|---|---|---|');t.columns.forEach((c,i)=>{let keys=[c.pk?'PK':null,c.fk?'FK':null,...c.uniqueIndexes.map(()=> 'UQ'),...c.indexes.map(()=> 'INDEX'),c.auto?'AI':null].filter(Boolean).join(', ')||'—';rows.push('| '+(i+1)+' | '+escMd(c.name)+' | '+escMd(c.type)+' | '+keys+' | '+c.nullable+' | '+escMd(c.default??'—')+' | '+escMd(c.description)+' |')});rows.push('','### Índices',...t.indexes.map(i=>'- '+i.name+' · '+i.type+(i.unique?' · UNIQUE':'')+' · ('+i.columns.join(', ')+')'));rows.push('','### Relaciones salientes',...t.foreignKeys.map(f=>'- '+f.name+': ('+f.columns.join(', ')+') → '+f.target+'('+f.targetColumns.join(', ')+') · ON DELETE '+(f.onDelete||'NO ACTION (implícito)')+' · ON UPDATE '+(f.onUpdate||'NO ACTION (implícito)')));rows.push('','### Relaciones entrantes',...t.incomingForeignKeys.map(f=>'- '+f.table+'('+f.columns.join(', ')+') → ('+f.targetColumns.join(', ')+')'));rows.push('','### Restricciones CHECK',...(t.checks.length?t.checks.map(c=>'- '+c):['- Ninguna declarada.']))});rows.push('','## Vistas',...DATA.views.map(v=>'- **'+v.name+'** · Tablas fuente: '+(v.sources.join(', ')||'no detectadas')+'\n  ```sql\n  '+v.definition.replaceAll('\\n','\\n  ')+'\n  ```'));rows.push('','## Triggers',...DATA.objects.triggers.map(t=>'- **'+t.name+'** · '+t.timing+' '+t.event+' ON '+t.table));rows.push('','## Procedimientos y funciones',...DATA.objects.routines.map(r=>'- **'+r.kind+' '+r.name+'('+r.parameters+')**'));rows.push('','## ALTER TABLE estructurales',...(DATA.objects.alterations.length?DATA.objects.alterations.map(a=>'- '+a.statement):['- Ninguno.']));return rows.join('\\n')}let timer;function toast(s)",
)
html = html.replace(
    "const esc=s=>String(s??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[c]));",
    "const esc=s=>String(s??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[c]));function renderExecutive(){let s=DATA.summary;document.querySelector('#executive').innerHTML=`<div class=\"exec-grid\"><div class=\"exec-card\"><small>Motor / dialecto</small><b>${esc(s.engine)} · MySQL</b></div><div class=\"exec-card\"><small>Charset / collation</small><b>${esc(s.charset)} / ${esc(s.collation)}</b></div><div class=\"exec-card\"><small>Tablas / columnas</small><b>${s.tableCount} / ${s.columnCount}</b></div><div class=\"exec-card\"><small>Registros en INSERT</small><b>${nf(s.rowCount)}</b></div><div class=\"exec-card\"><small>Mayor volumen</small><b>${esc(s.largestTable)} · ${nf(s.largestCount)}</b></div></div>`}function renderIndex(){document.querySelector('#entity-index').innerHTML=`<table><thead><tr><th>Tabla</th><th>Propósito</th><th>Columnas</th><th>FK salientes</th><th>FK entrantes</th><th>Registros</th></tr></thead><tbody>${DATA.tables.map(t=>`<tr><td><a href=\"#t-${encodeURIComponent(t.name)}\">${esc(t.name)}</a></td><td>${esc(t.purpose)}</td><td>${t.columns.length}</td><td>${t.foreignKeys.length}</td><td>${t.incomingForeignKeys.length}</td><td>${nf(t.count)}</td></tr>`).join('')}</tbody></table>`}function renderObjects(){let o=DATA.objects;document.querySelector('#objects').innerHTML=`<div class=\"object-group\"><h4>Vistas (${DATA.views.length})</h4>${DATA.views.length?DATA.views.map(v=>`<details><summary>${esc(v.name)} <span class=\"muted\">${esc(v.sources.join(', ')||'Fuentes no detectadas')}</span></summary><pre>${esc(v.definition)}</pre></details>`).join(''):'<div class=\"empty\">No hay vistas.</div>'}</div><div class=\"object-group\"><h4>Triggers (${o.triggers.length})</h4>${o.triggers.length?o.triggers.map(t=>`<details><summary>${esc(t.name)} · ${esc(t.timing)} ${esc(t.event)} ON ${esc(t.table)}</summary><pre>${esc(t.body)}</pre></details>`).join(''):'<div class=\"empty\">No hay triggers.</div>'}</div><div class=\"object-group\"><h4>Procedimientos / funciones (${o.routines.length})</h4>${o.routines.length?o.routines.map(r=>`<div class=\"fk-item\">${esc(r.kind)} ${esc(r.name)}(${esc(r.parameters)})</div>`).join(''):'<div class=\"empty\">No hay procedimientos ni funciones.</div>'}</div><div class=\"object-group\"><h4>ALTER TABLE (${o.alterations.length})</h4>${o.alterations.length?o.alterations.map(a=>`<pre>${esc(a.statement)}</pre>`).join(''):'<div class=\"empty\">No hay alteraciones estructurales.</div>'}</div>`}",
)
html = html.replace(
    ".hidden{display:none!important}",
    ".hidden{display:none!important}.filters{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin:0 0 15px}.filters span{font-size:11px;color:var(--muted);font-weight:700}.filters button.active{background:var(--blue);border-color:var(--blue);color:#fff}.exec-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:0 0 20px}.exec-card{padding:13px 15px;background:#fff;border:1px solid var(--line);border-radius:10px;display:grid;gap:5px}.exec-card small{color:var(--muted);font-size:10px}.exec-card b{font-size:14px}.index-card{margin-bottom:18px}.index-card table{min-width:860px}.objects-grid{padding:16px;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}.object-group{min-width:0}.object-group h4{margin:0 0 8px;font-size:12px;color:#586982;text-transform:uppercase;letter-spacing:.06em}.object-group details{border:1px solid var(--line);border-radius:7px;padding:8px 10px;margin:0 0 6px;font-size:11px}.object-group summary{cursor:pointer;font-weight:700}.object-group pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:300px;overflow:auto;font-size:10px;color:#43536a;background:#f5f7fa;padding:8px;border-radius:5px}"
)
dictionary.HTML = html
dictionary.build_data = build_data
dictionary.main()

page = OUT.read_text(encoding="utf-8")
page = page.replace("\u00c2\u00b7", "\u00b7").replace("\u00e2\u2020\u2019", "\u2192")
page = page.replace(
    "o.routines.map(r=>`<div class=\"fk-item\">${esc(r.kind)} ${esc(r.name)}(${esc(r.parameters)})</div>`).join('')",
    "o.routines.map(r=>`<details><summary>${esc(r.kind)} ${esc(r.name)}(${esc(r.parameters)})</summary><pre>${esc(r.body)}</pre></details>`).join('')",
)
page = page.replace(
    "DATA.objects.triggers.map(t=>'- **'+t.name+'** · '+t.timing+' '+t.event+' ON '+t.table)",
    r"DATA.objects.triggers.map(t=>'- **'+t.name+'** · '+t.timing+' '+t.event+' ON '+t.table+'\n```sql\n'+t.body+'\n```')",
)
page = page.replace(
    "DATA.objects.routines.map(r=>'- **'+r.kind+' '+r.name+'('+r.parameters+')**)",
    r"DATA.objects.routines.map(r=>'- **'+r.kind+' '+r.name+'('+r.parameters+')**\n```sql\n'+r.body+'\n```')",
)
page = page.replace(
    "document.querySelectorAll('.nav-link').forEach(a=>a.classList.toggle('hidden',!!q&&document.querySelector(a.getAttribute('href'))?.classList.contains('hidden')));",
    "document.querySelectorAll('.nav-link').forEach(a=>a.classList.toggle('hidden',document.querySelector(a.getAttribute('href'))?.classList.contains('hidden')));",
)
page = page.replace(
    "document.querySelector('#navCount').textContent=q?`(${visible}/${DATA.tables.length})`:`(${DATA.tables.length})`",
    "document.querySelector('#navCount').textContent=(q||activeFilters.size)?`(${visible}/${DATA.tables.length})`:`(${DATA.tables.length})`",
)
OUT.write_text(page, encoding="utf-8")
