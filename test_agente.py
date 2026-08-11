import sys, json
sys.path.insert(0, '/workspaces/oi')
from datahub_bruto.agent.orquestador import consultar, _leer_manifest, CATALOGO
from datahub_bruto.geo.catalogo_operaciones import CATALOGO as CAT2

print("CATALOGO len:", len(CATALOGO))
print("manifest len:", len(_leer_manifest()))

r = consultar('dame el ndvi de la zona alfa')
print("RESULT:", json.dumps(r, indent=2, ensure_ascii=False)[:1200])
