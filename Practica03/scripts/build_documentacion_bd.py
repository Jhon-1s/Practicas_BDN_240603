"""Build one standalone HTML that contains both the data dictionary and EER app."""
import html
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "documentacion_bd.html"

PAGE = r'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Documentación interactiva de la base de datos</title>
<style>
*{box-sizing:border-box}html,body{height:100%;margin:0;font:14px/1.4 Inter,Segoe UI,system-ui,sans-serif;background:#101722;color:#eef3f9}.shell{height:100%;display:flex;flex-direction:column}.top{height:58px;flex:none;display:flex;align-items:center;gap:20px;padding:0 20px;background:#111b29;border-bottom:1px solid #29384b}.title{font-weight:700;letter-spacing:.01em}.title small{display:block;color:#99a8bb;font-size:10px;font-weight:400}.tabs{height:100%;display:flex;gap:4px;align-items:end}.tab{height:42px;padding:0 16px;border:0;border-bottom:2px solid transparent;border-radius:7px 7px 0 0;background:transparent;color:#aab8c9;cursor:pointer;font:inherit}.tab:hover{color:#fff;background:#1a2737}.tab.active{color:#80e4d7;border-bottom-color:#80e4d7;background:#172635;font-weight:700}.content{position:relative;flex:1;min-height:0}.view{position:absolute;inset:0}.view[hidden]{display:none}.view iframe{display:block;border:0;width:100%;height:100%;background:#0b1018}
</style></head><body><div class="shell"><header class="top"><div class="title">Documentación de la base de datos<small>Respaldo 13/11/2026 · diccionario y modelo EER</small></div><nav class="tabs" role="tablist" aria-label="Vistas de documentación"><button class="tab active" role="tab" aria-selected="true" aria-controls="dictionary" data-view="dictionary">Diccionario de datos</button><button class="tab" role="tab" aria-selected="false" aria-controls="eer" data-view="eer">Diagrama EER</button></nav></header><main class="content"><section class="view" id="dictionary" role="tabpanel"><iframe title="Diccionario de datos" srcdoc="__DICTIONARY__"></iframe></section><section class="view" id="eer" role="tabpanel" hidden><iframe title="Diagrama entidad-relación extendido" srcdoc="__EER__"></iframe></section></main></div>
<script>
const tabs=[...document.querySelectorAll('.tab')];function activate(name){for(const tab of tabs){const yes=tab.dataset.view===name;tab.classList.toggle('active',yes);tab.setAttribute('aria-selected',String(yes));document.getElementById(tab.getAttribute('aria-controls')).hidden=!yes}if(name==='eer'){const frame=document.querySelector('#eer iframe');try{frame.contentDocument.querySelector('#fit')?.click()}catch{}}}
tabs.forEach(tab=>tab.addEventListener('click',()=>activate(tab.dataset.view)));
</script></body></html>'''


def main():
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_data_dictionary_13112026.py")], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_eer_interactive.py")], check=True, cwd=ROOT)
    dictionary = (ROOT / "diccionario_datos.html").read_text(encoding="utf-8")
    eer = (ROOT / "eer.html").read_text(encoding="utf-8")
    page = PAGE.replace("__DICTIONARY__", html.escape(dictionary, quote=True))
    page = page.replace("__EER__", html.escape(eer, quote=True))
    OUT.write_text(page, encoding="utf-8")
    print(f"{OUT.name}: un solo HTML, {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
