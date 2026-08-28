# -*- coding: utf-8 -*-
"""Mete la DESCRIPTION del front-matter en el nodo SKILL del toolgraph.

El nodo llevaba solo los TITULOS de seccion (`de_que_habla`), asi que el indice cargaba de
media el 28% de lo que la descripcion dice y 55 de 61 skills perdian mas de la mitad.
Consecuencia medida en s108: `sap_variant_analysis` no contenia "revaluation", "SAPF100" ni
"FX" aunque su propia descripcion los nombra, y por tanto era inencontrable preguntando por
ellos.

Se escribe como fichero (no heredoc): el intento anterior por heredoc destrozo los escapes de
las regex y dejo build_toolgraph.py sin compilar.
"""
import io, re, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

P = "brain_v2/build_toolgraph.py"
s = io.open(P, encoding="utf-8").read()

HELPER = '\n'.join([
    'def _descripcion_de(fichero):',
    '    """La DESCRIPTION del front-matter: el resumen mas intencionado de para que sirve un',
    '    instrumento, y lo que el propio harness usa para enrutar.',
    '',
    '    NO estaba en el grafo. El nodo SKILL llevaba solo los TITULOS de seccion',
    '    (`de_que_habla`), asi que el indice cargaba de media el 28% de lo que la descripcion',
    '    dice, y 55 de 61 skills perdian mas de la mitad. Medido en s108:',
    '    `sap_variant_analysis` no contenia "revaluation", "SAPF100" ni "FX" aunque su propia',
    '    descripcion los nombra -- y por tanto no se podia encontrar preguntando por ellos.',
    '    """',
    '    import os as _os',
    '    import re as _re',
    '    import io as _io',
    '    if not fichero:',
    '        return ""',
    '    p = fichero if _os.path.isabs(fichero) else _os.path.join(ROOT, fichero)',
    '    try:',
    '        txt = _io.open(p, encoding="utf-8").read()',
    '    except Exception:',
    '        return ""',
    '    m = _re.search(FM_RE, txt, _re.S | _re.M)',
    '    if not m:',
    '        return ""',
    '    d = _re.search(DESC_RE, m.group(1), _re.S | _re.M)',
    '    if not d:',
    '        return ""',
    '    return " ".join(d.group(1).split())[:1500]',
    '',
    '',
])
# Las dos regex como constantes, para que ningun escape se pierda al parchear
CONSTS = 'FM_RE = r"^---\\s*\\r?\\n(.*?)\\r?\\n---\\s*$"\nDESC_RE = r"^description:\\s*(.*?)(?=\\n[a-zA-Z_]+:\\s|\\Z)"\n\n\n'

if "_descripcion_de" in s:
    print("helper: ya estaba")
else:
    m = re.search(r"^def construir\(", s, re.M) or re.search(r"^def main\(", s, re.M)
    pos = m.start()
    s = s[:pos] + CONSTS + HELPER + s[pos:]
    print("helper + constantes: insertados")

old = ('        nodo("SKILL", s, bytes=r.get("bytes"), fichero=r.get("fichero"),\n'
       '             de_que_habla=r.get("de_que_habla"), cubre_tablas=len(r.get("cubre_tablas") or []))')
new = ('        nodo("SKILL", s, bytes=r.get("bytes"), fichero=r.get("fichero"),\n'
       '             descripcion=_descripcion_de(r.get("fichero")),\n'
       '             de_que_habla=r.get("de_que_habla"), cubre_tablas=len(r.get("cubre_tablas") or []))')
if "descripcion=_descripcion_de" in s:
    print("nodo: ya estaba")
elif old in s:
    s = s.replace(old, new, 1)
    print("nodo SKILL: lleva descripcion")
else:
    print("nodo: ANCLA NO ENCONTRADA")

io.open(P, "w", encoding="utf-8").write(s)

import ast
ast.parse(io.open(P, encoding="utf-8").read())
print("sintaxis OK")
