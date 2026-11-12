import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from build_eer import SQL, parse

OUT = ROOT / "diccionario_datos.html"

TABLE_PURPOSE = {
    "tb_users": "Cuentas de usuario y datos de acceso al sistema.",
    "tb_people": "Datos personales asociados a una cuenta.",
    "tb_products": "Catálogo de productos disponibles.",
    "tbc_categories": "Categorías jerárquicas para clasificar productos.",
    "tb_carts": "Carritos de compra asociados a usuarios.",
    "tbd_cart_items": "Productos y cantidades incluidos en carritos.",
    "tb_orders": "Órdenes de compra y su estado.",
    "tbd_order_items": "Renglones de producto pertenecientes a órdenes.",
    "tb_payments": "Pagos asociados a órdenes y métodos de pago.",
    "tb_payment_methods": "Métodos de pago disponibles.",
    "tbc_payment_methods_types": "Catálogo de tipos de método de pago.",
    "tb_payment_transaction": "Transacciones relacionadas con pagos.",
    "tb_refunds": "Reembolsos relacionados con pagos.",
    "tb_returns": "Devoluciones relacionadas con órdenes.",
    "tbd_return_items": "Artículos incluidos en devoluciones.",
    "tb_order_cancellations": "Cancelaciones de órdenes y su estado.",
    "tbd_cancellation_items": "Artículos incluidos en cancelaciones.",
    "tb_shipments": "Envíos y datos de seguimiento de órdenes.",
    "tb_user_addresses": "Direcciones de entrega asociadas a usuarios.",
    "tbd_address_components": "Componentes estructurados de direcciones.",
    "tbd_products_categories": "Relación de muchos a muchos entre productos y categorías.",
    "tbd_products_users_providers": "Relación entre productos, usuarios y proveedores.",
    "tbd_user_payment_methods": "Métodos de pago tokenizados asociados a usuarios.",
    "tbd_users_wishlist_products": "Productos guardados en listas de deseos de usuarios.",
    "tb_logs": "Bitácora de operaciones registradas por la base de datos.",
}


def column_description(table, column):
    name = column["name"]
    low = name.lower()
    if column["pk"]:
        return "Identificador único" + (" de la fila; generado automáticamente." if column["auto"] else " de la fila.")
    if column["fk"]:
        return "Referencia a la entidad indicada en la restricción de llave foránea."
    descriptions = {
        "status": "Indicador o estado de actividad del registro.",
        "creation_date": "Fecha y hora de creación del registro.",
        "created_at": "Fecha y hora de creación del registro.",
        "last_update": "Fecha y hora de la última actualización.",
        "description": "Descripción textual del registro.",
        "name": "Nombre visible o descriptivo.",
        "email": "Dirección de correo electrónico.",
        "price": "Precio o importe monetario.",
        "quantity": "Cantidad de unidades.",
        "stock": "Existencia disponible.",
        "is_default": "Indica si el registro es el predeterminado.",
        "operation_date": "Fecha y hora de la operación registrada.",
        "table_name": "Nombre de la tabla relacionada con la operación.",
        "table_operation": "Tipo de operación registrada.",
        "db_users": "Usuario de base de datos que ejecutó la operación.",
        "table_description": "Detalle descriptivo de la operación.",
        "auto_increment": "Indica si el valor se genera automáticamente.",
        "latitude": "Coordenada geográfica de latitud.",
        "longitude": "Coordenada geográfica de longitud.",
        "birth_date": "Fecha de nacimiento.",
    }
    if low in descriptions:
        return descriptions[low]
    if low.endswith("_date") or low.endswith("_at"):
        return "Fecha u hora relacionada con el registro."
    if low.startswith("is_") or low.startswith("has_"):
        return "Indicador booleano."
    if "phone" in low:
        return "Número telefónico de contacto."
    if "address" in low:
        return "Dato relacionado con una dirección."
    if "amount" in low or "total" in low:
        return "Importe o total monetario."
    if "type" in low or "status" in low:
        return "Tipo o estado del registro."
    if "id" in low:
        return "Identificador relacionado con la entidad indicada por el nombre del campo."
    return "Propósito estimado a partir del nombre y tipo del campo."


def build_data():
    data = parse(SQL.read_text(encoding="utf-8", errors="replace"))
    for table in data["tables"]:
        for column in table["columns"]:
            fk = next((f for f in table["foreignKeys"] if column["name"] in f["columns"]), None)
            column["reference"] = (f"{fk['target']}({fk['targetColumns'][fk['columns'].index(column['name'])]})" if fk else None)
            column["description"] = column_description(table, column)
        table["purpose"] = TABLE_PURPOSE.get(table["name"], "Propósito estimado a partir del nombre y las columnas.")
    return data


HTML = r'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Diccionario de datos · __DB__</title>
<style>
:root{color-scheme:light;--ink:#172334;--muted:#65748a;--line:#dbe2eb;--paper:#f4f6f9;--white:#fff;--blue:#2558a5;--blue-soft:#eaf1fc;--green:#157451;--purple:#7144a1}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.5 Inter,Segoe UI,Arial,sans-serif}header{height:94px;position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:24px;padding:15px 26px}.brand{min-width:250px}.brand small{font-size:10px;text-transform:uppercase;letter-spacing:.16em;color:var(--blue);font-weight:700}h1{font-size:20px;margin:2px 0}.sub{font-size:11px;color:var(--muted)}.search{flex:1;max-width:680px;position:relative}.search input{width:100%;padding:12px 14px 12px 40px;border:1px solid #cbd5e2;border-radius:9px;background:#f9fbfd;color:var(--ink);font:inherit;outline:none}.search input:focus{border-color:#6b93ce;box-shadow:0 0 0 3px #dce8fa}.search span{position:absolute;left:14px;top:10px;color:#75849b;font-size:18px}.actions{display:flex;gap:7px;margin-left:auto}button{border:1px solid #cbd5e2;background:white;color:#304058;border-radius:8px;padding:8px 11px;cursor:pointer;font-weight:600}button:hover{color:var(--blue);border-color:#7195c7}.layout{display:grid;grid-template-columns:250px minmax(0,1fr);min-height:calc(100vh - 94px)}nav{position:sticky;top:94px;align-self:start;height:calc(100vh - 94px);overflow:auto;background:#fff;border-right:1px solid var(--line);padding:19px 13px}.nav-title{padding:0 10px 9px;color:var(--muted);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.13em}.nav-link{display:flex;justify-content:space-between;gap:8px;text-decoration:none;color:#43536a;padding:7px 10px;border-radius:6px;font-size:12px}.nav-link:hover,.nav-link.active{background:var(--blue-soft);color:var(--blue)}.nav-count{font-size:10px;color:#8794a7}.content{padding:22px clamp(16px,3vw,42px) 70px;max-width:1600px;width:100%;margin:auto}.summary{display:flex;align-items:center;justify-content:space-between;gap:20px;margin:0 0 18px}.summary h2{margin:0;font-size:18px}.summary p{margin:3px 0 0;color:var(--muted);font-size:12px}.table-card{background:white;border:1px solid var(--line);border-radius:12px;margin:0 0 22px;box-shadow:0 3px 12px #14253a08;scroll-margin-top:112px}.table-head{padding:16px 18px 13px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:15px}.table-head h3{margin:0;font-size:17px;letter-spacing:.01em}.purpose{color:var(--muted);font-size:12px;margin-top:4px}.metrics{display:flex;gap:6px;justify-content:flex-end;flex-wrap:wrap;align-content:flex-start}.pill{border:1px solid #d8e0ea;border-radius:99px;padding:4px 8px;color:#52627a;font-size:10px;white-space:nowrap}.pill.rows{background:#eaf6f0;border-color:#c4e7d5;color:#176644;font-weight:700}.matrix-wrap{overflow:auto}table{border-collapse:collapse;width:100%;min-width:1180px;font-size:11px}th{text-align:left;background:#f5f7fa;color:#526178;font-size:10px;text-transform:uppercase;letter-spacing:.055em;padding:9px 10px;border-bottom:1px solid var(--line);position:sticky;top:94px;z-index:2}td{padding:9px 10px;border-bottom:1px solid #edf0f4;vertical-align:top}tr:last-child td{border-bottom:0}tbody tr:hover{background:#f9fbfe}.field{font-weight:700;white-space:nowrap}.type{font-family:Consolas,monospace;color:#334b69;white-space:nowrap}.default{font-family:Consolas,monospace;color:#77552f}.nullable{white-space:nowrap}.tag{display:inline-block;margin:0 3px 3px 0;padding:2px 5px;border-radius:4px;background:#edf1f5;color:#53647b;font-size:9px;font-weight:700;white-space:nowrap}.tag.pk{background:#def4ee;color:#11644e}.tag.fk{background:#f0e8fb;color:#684294}.tag.unique{background:#fff1d8;color:#86550b}.tag.index{background:#e8effa;color:#355c94}.tag.attr{background:#f2f3f5;color:#5d6572}.reference{font-family:Consolas,monospace;color:#684294;white-space:nowrap}.extra{border-top:1px solid var(--line);padding:13px 18px 16px;display:grid;grid-template-columns:minmax(280px,1fr) minmax(280px,1fr);gap:18px}.extra h4{margin:0 0 8px;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#586982}.index-item,.fk-item{font-size:11px;padding:6px 8px;background:#f5f7fa;border-radius:6px;margin:0 0 5px}.index-item code,.fk-item code{font-family:Consolas,monospace;color:#334b69}.empty{font-size:11px;color:#8793a4}.hidden{display:none!important}.no-results{background:white;border:1px solid var(--line);border-radius:10px;padding:35px;text-align:center;color:var(--muted)}.footer{font-size:11px;color:var(--muted);padding:12px 2px}.matched{background:#fff4cc}.toast{position:fixed;right:18px;bottom:18px;background:#172334;color:white;padding:10px 14px;border-radius:8px;opacity:0;transform:translateY(8px);transition:.2s;pointer-events:none}.toast.show{opacity:1;transform:none}@media(max-width:900px){header{height:auto;min-height:94px;flex-wrap:wrap;gap:10px;padding:12px 15px}.brand{min-width:180px}.search{order:3;flex-basis:100%;max-width:none}.layout{grid-template-columns:190px minmax(0,1fr)}nav{top:120px;height:calc(100vh - 120px)}th{top:120px}.table-head{flex-direction:column}.metrics{justify-content:flex-start}}@media(max-width:620px){.layout{grid-template-columns:1fr}nav{position:static;height:auto;max-height:170px;border-right:0;border-bottom:1px solid var(--line);columns:2}.nav-title{column-span:all}.content{padding:14px}.extra{grid-template-columns:1fr}.actions{margin-left:0}}
</style></head><body>
<header><div class="brand"><small>Catálogo técnico · MySQL</small><h1>Diccionario de Datos</h1><div class="sub" id="database"></div></div><label class="search"><span>⌕</span><input id="q" type="search" placeholder="Buscar tabla, campo, tipo de dato…" autocomplete="off" aria-label="Búsqueda global"></label><div class="actions"><button id="csv">Exportar CSV</button><button id="json">Exportar JSON</button><button id="print">Imprimir</button></div></header>
<div class="layout"><nav><div class="nav-title">Tablas <span id="navCount"></span></div><div id="nav"></div></nav><main class="content"><div class="summary"><div><h2>Inventario de entidades</h2><p id="summary"></p></div><div class="sub">Fuente: respaldo20261111.sql</div></div><div id="dictionary"></div><div id="empty" class="no-results hidden">No hay tablas o columnas que coincidan con la búsqueda.</div><div class="footer">Los conteos corresponden a filas incluidas en sentencias INSERT del respaldo. Las descripciones de propósito son estimaciones derivadas del esquema.</div></main></div><div id="toast" class="toast"></div>
<script>
const DATA=__DATA__;const nf=n=>n.toLocaleString('es-MX');document.querySelector('#database').textContent=`Base de datos: ${DATA.database} · Archivo: respaldo20261111.sql`;document.querySelector('#summary').textContent=`${DATA.tables.length} tablas · ${nf(DATA.tables.reduce((a,t)=>a+t.count,0))} filas incluidas en el respaldo`;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function render(){document.querySelector('#nav').innerHTML=DATA.tables.map(t=>`<a class="nav-link" href="#t-${encodeURIComponent(t.name)}" data-table="${esc(t.name)}"><span>${esc(t.name)}</span><span class="nav-count">${nf(t.count)}</span></a>`).join('');document.querySelector('#navCount').textContent=`(${DATA.tables.length})`;
document.querySelector('#dictionary').innerHTML=DATA.tables.map(t=>`<section class="table-card" id="t-${esc(t.name)}" data-name="${esc(t.name.toLowerCase())}" data-search="${esc([t.name,...t.columns.flatMap(c=>[c.name,c.type,c.description,c.default||''])].join(' ').toLowerCase())}"><div class="table-head"><div><h3>${esc(t.name)}</h3><div class="purpose">${esc(t.purpose)}</div></div><div class="metrics"><span class="pill rows">Total registros: ${nf(t.count)}</span><span class="pill">${esc(t.engine)}</span><span class="pill">${esc(t.charset)}</span><span class="pill">${esc(t.collation)}</span></div></div><div class="matrix-wrap"><table><thead><tr><th>Nombre del campo</th><th>Tipo de dato</th><th>Acepta nulos</th><th>Valor por defecto</th><th>Llaves e índices</th><th>Atributos adicionales</th><th>Tabla y campo referenciado</th><th>Descripción / propósito estimado</th></tr></thead><tbody>${t.columns.map(c=>{let tags=[];if(c.pk)tags.push('<span class="tag pk">PK</span>');if(c.fk)tags.push('<span class="tag fk">FK</span>');if(c.uniqueIndexes.length)tags.push('<span class="tag unique">UNIQUE</span>');if(c.indexes.length)tags.push(...c.indexes.map(n=>`<span class="tag index">INDEX ${esc(n)}</span>`));let attrs=[...c.attributes];if(c.auto)attrs.push('AUTO_INCREMENT');return `<tr data-field="${esc(c.name.toLowerCase())}" data-type="${esc(c.type.toLowerCase())}"><td class="field">${esc(c.name)}</td><td class="type">${esc(c.type)}</td><td class="nullable">${esc(c.nullable)}</td><td class="default">${c.default===null?'—':esc(c.default)}</td><td>${tags.join(' ')||'—'}</td><td>${attrs.map(a=>`<span class="tag attr">${esc(a)}</span>`).join(' ')||'—'}</td><td class="reference">${c.reference?esc(c.reference):'—'}</td><td>${esc(c.description)}</td></tr>`}).join('')}</tbody></table></div><div class="extra"><div><h4>Índices</h4>${t.indexes.length?t.indexes.map(i=>`<div class="index-item"><code>${esc(i.name)}</code> · ${esc(i.type)}${i.unique?' · UNIQUE':''} · (${i.columns.map(esc).join(', ')})</div>`).join(''):'<div class="empty">Sin índices secundarios declarados.</div>'}</div><div><h4>Reglas de integridad · llaves foráneas</h4>${t.foreignKeys.length?t.foreignKeys.map(f=>`<div class="fk-item"><b>${esc(f.name)}</b> · (${f.columns.map(esc).join(', ')}) → <code>${esc(f.target)}(${f.targetColumns.map(esc).join(', ')})</code><br>ON DELETE ${esc(f.onDelete||'NO ACTION (implícito)')} · ON UPDATE ${esc(f.onUpdate||'NO ACTION (implícito)')}</div>`).join(''):'<div class="empty">Sin llaves foráneas declaradas.</div>'}</div></div></section>`).join('');filter('')}
function filter(q){q=q.trim().toLowerCase();let visible=0;document.querySelectorAll('.table-card').forEach(card=>{let found=!q||card.dataset.search.includes(q);card.classList.toggle('hidden',!found);if(found)visible++});document.querySelectorAll('.nav-link').forEach(a=>a.classList.toggle('hidden',!!q&&document.querySelector(a.getAttribute('href'))?.classList.contains('hidden')));document.querySelector('#empty').classList.toggle('hidden',visible>0);document.querySelector('#navCount').textContent=q?`(${visible}/${DATA.tables.length})`:`(${DATA.tables.length})`}
document.querySelector('#q').addEventListener('input',e=>filter(e.target.value));document.querySelector('#print').onclick=()=>window.print();
function download(name,type,content){let a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type}));a.download=name;a.click();URL.revokeObjectURL(a.href);toast('Archivo exportado: '+name)}
document.querySelector('#json').onclick=()=>download('diccionario_datos_respaldo20261111.json','application/json;charset=utf-8',JSON.stringify(DATA,null,2));document.querySelector('#csv').onclick=()=>{let rows=[['tabla','registros','motor','charset','collation','campo','tipo','nulos','default','llaves_indices','atributos','referencia','descripcion']];DATA.tables.forEach(t=>t.columns.forEach(c=>rows.push([t.name,t.count,t.engine,t.charset,t.collation,c.name,c.type,c.nullable,c.default??'',[(c.pk?'PK':''),(c.fk?'FK':''),...c.uniqueIndexes.map(()=> 'UNIQUE'),...c.indexes].filter(Boolean).join('|'),[...c.attributes,...(c.auto?['AUTO_INCREMENT']:[])].join('|'),c.reference??'',c.description])));let csv='\ufeff'+rows.map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\r\n');download('diccionario_datos_respaldo20261111.csv','text/csv;charset=utf-8',csv)};
let timer;function toast(s){let e=document.querySelector('#toast');e.textContent=s;e.classList.add('show');clearTimeout(timer);timer=setTimeout(()=>e.classList.remove('show'),2200)}render();
</script></body></html>'''


def main():
    data = build_data()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    OUT.write_text(HTML.replace("__DATA__", payload).replace("__DB__", data["database"]), encoding="utf-8")
    print(f"{OUT.name}: {len(data['tables'])} tablas, {sum(len(t['columns']) for t in data['tables'])} columnas, "
          f"{sum(t['count'] for t in data['tables']):,} filas")


if __name__ == "__main__":
    main()
