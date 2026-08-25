"""Engancha al grafo los claims que nombran objetos en su texto y no los tienen en el campo.

EL PROBLEMA
    Un claim sin related_objects esta guardado y no entra en el grafo: no lo encuentra nadie
    que busque por el objeto del que habla, solo quien lea los 584 de arriba abajo. Medido el
    2026-08-25: 17 claims asi, casi todos heredados de antes de que el campo existiera. Y el
    conocimiento SI estaba -- 'CSKA cost element table is empty' nombra CSKA en la primera
    linea; simplemente nadie lo movio al campo por el que se busca.

LA REGLA, DELIBERADAMENTE CONSERVADORA
    Solo se ancla en nombres QUE EL BRAIN YA CONOCE: los que aparecen en el related_objects de
    algun otro claim, o son una tabla del Gold DB. Nada inventado, nada deducido de la forma de
    la palabra. Un anclaje falso es peor que ninguno, porque manda a quien busca a un sitio
    equivocado y ademas parece resuelto.

    Por eso NO extrae nombres 'con pinta de tabla SAP'. Esa heuristica habria metido AVC, TYPE,
    XML o STATUS como si fueran objetos.

Uso:  python brain_v2/anchor_claims.py [--apply]
      sin --apply solo muestra lo que haria.
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLAIMS = REPO / "brain_v2" / "claims" / "claims.json"
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

TOKEN = re.compile(r"[A-Z][A-Z0-9_/]{2,29}")
# Palabras que pasan el filtro de forma y no son objetos SAP.
RUIDO = {"THE", "AND", "FOR", "NOT", "ALL", "ARE", "WAS", "HAS", "TIER", "TYPE", "XML", "SAP",
         "GOLD", "DB", "OK", "NO", "YES", "NULL", "TRUE", "FALSE", "SESSION", "CLAIM", "INC",
         "USER", "DATA", "CODE", "FILE", "NAME", "TEXT", "LIST", "ROW", "ROWS", "P01", "D01",
         "V01", "UTC", "PDF", "CSV", "HTML", "JSON"}


def vocabulario():
    """Lo que el brain ya sabe nombrar. Nada fuera de aqui se usa como ancla."""
    voc = set()
    claims = json.loads(CLAIMS.read_text(encoding="utf-8"))
    frec = {}
    for c in claims:
        for o in (c.get("related_objects") or []):
            t = str(o).strip().upper()
            if len(t) >= 3:
                voc.add(t)
                frec[t] = frec.get(t, 0) + 1
    # Un nombre que sale en todas partes no localiza nada: UNESCO como ancla no lleva a ningun
    # sitio, y llena el grafo de aristas que no distinguen. Fuera lo que aparece en mas del 8%.
    techo = max(3, int(0.08 * len(claims)))
    generico = {t for t, n in frec.items() if n > techo}
    voc -= generico
    try:
        con = sqlite3.connect(GOLD, timeout=120)
        for (n,) in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')"):
            voc.add(str(n).strip().upper())
            # las tablas del gold llevan prefijo de sistema cuando no son P01
            for p in ("D01_", "V01_"):
                if n.upper().startswith(p):
                    voc.add(n.upper()[len(p):])
        con.close()
    except sqlite3.Error:
        pass
    return voc - RUIDO, claims


def texto_de(c):
    partes = [str(c.get("claim") or "")]
    for f in ("evidence_for", "evidence_legacy_text_for", "evidence", "resolution_notes"):
        v = c.get(f)
        if v:
            partes.append(json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v)
    return " ".join(partes)


def main():
    voc, claims = vocabulario()
    aplicar = "--apply" in sys.argv
    tocados = 0
    for c in claims:
        if c.get("related_objects"):
            continue
        hallados = sorted({t for t in TOKEN.findall(texto_de(c))
                           if t in voc and t not in RUIDO})
        print(f"  claim {c.get('id')}: {len(hallados)} ancla(s) -> "
              f"{', '.join(hallados[:10]) or '(ninguna que el brain conozca)'}")
        if hallados and aplicar:
            c["related_objects"] = hallados
            c["_anclado_por"] = ("brain_v2/anchor_claims.py 2026-08-25 -- nombres extraidos del "
                                 "propio texto del claim, solo los que el brain ya conocia")
            tocados += 1
    if aplicar:
        CLAIMS.write_text(json.dumps(claims, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n{tocados} claim(s) enganchados al grafo")
    else:
        print("\n(simulacion - pasa --apply para escribir)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
