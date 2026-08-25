"""A31 — EL CANAL BATCH INPUT, MINADO. Quien genera sesiones, de donde vienen y a que dominio.

POR QUE EXISTE
    Este metodo encontro ALLOS: una herramienta Excel que genera sesiones de batch input por
    RFC y que se llevaba mas de un ano buscando sin dar con ella. Y despues de encontrarla, el
    metodo se quedo viviendo SOLO COMO PROMPT en .claude/agents/batch-input-explorer.md.

    Un metodo que solo vive en un prompt no se puede repetir, ni programar, ni gatear, ni
    comparar con la corrida del mes pasado. Es exactamente la perdida de conocimiento de metodo
    que este proyecto lleva persiguiendo: el hallazgo se guardo, la FORMA DE ENCONTRARLO no.

LO QUE MINA, Y POR QUE ES MINERIA DE VERDAD
    Descubrimiento de CANAL y ACTOR a partir de datos de evento -- la misma familia que A23 y
    A27. La cola APQI es un log: cada fila es una sesion con su generador, su creador y su
    fecha. De ahi sale por donde entra el trabajo que NO pasa por una transaccion de dialogo.

LA TRAMPA QUE DEFINE ESTE CANAL
    APQI es una COLA, no un archivo: **las sesiones que se procesan bien SE BORRAN**. Lo que
    queda es lo que fallo, lo que nadie corrio y lo reciente. Por eso ninguna cifra de aqui es
    "cuanto batch input se hace": es "cuanto batch input QUEDA VISIBLE", y las dos cosas se
    parecen lo suficiente como para confundirlas. Cada salida lo lleva escrito.

    Y PROGID no dice la transaccion: dice el PROGRAMA que genero la sesion. `SAPMSSY1` significa
    'vino de fuera por RFC' y no identifica la herramienta -- eso hay que abrirlo por GROUPID,
    que es lo unico que la sesion externa trae consigo.

Uso:  python process_mining/bdc_channel_mining.py [--desde AAAAMMDD]
Aterriza en: brain_v2/bdc_channel.json  + publica en el bus de mineros
"""
import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SALIDA = REPO / "brain_v2" / "bdc_channel.json"
sys.path.insert(0, str(REPO / "process_mining"))

# Gramaticas del GROUPID, que es lo unico que una sesion externa trae consigo. Cada una se
# comprobo contra datos reales antes de entrar aqui; la de acreedor exigio rellenar LIFNR a 10
# con ceros, que es como SAP lo guarda -- sin eso casaba 0 de 400.
GRAMATICAS = [
    (re.compile(r"^TRIP_", re.I), "Travel", "TRIP_CREATE / TRIP_MODIFY"),
    (re.compile(r"^\d{1,8}[A-Z0-9]{2,4}$", re.I), "HCM (ALLOS)",
     "<numero><sufijo de oficina>: la firma de ALLOS"),
]


def gold():
    from gold_ref import GOLD  # type: ignore
    return sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True, timeout=600)


def clasificador():
    import importlib.util as u
    sp = u.spec_from_file_location(
        "_a4", str(REPO / "process_mining" / "executed_objects_domain_map.py"))
    m = u.module_from_spec(sp)
    sp.loader.exec_module(m)      # sin try: si el clasificador no carga, esto debe PARAR
    con = sqlite3.connect(m.GOLD, timeout=300)
    return m.make_classifier(con)


def gramatica_de(groupid):
    g = (groupid or "").strip()
    for rx, dom, nota in GRAMATICAS:
        if rx.match(g):
            return dom, nota
    return None, None


def main():
    ap = argparse.ArgumentParser(description="mina el canal batch input desde APQI")
    ap.add_argument("--desde", default="20250101",
                    help="AAAAMMDD. Por defecto 2025: como se trabaja HOY, no como se trabajo "
                         "en 2016")
    a = ap.parse_args()

    con = gold()
    dom_de, ctx = clasificador()

    filas = con.execute("""SELECT PROGID, GROUPID, CREATOR, CREDATE, QSTATE, TRANSCNT, DESTSYS
                           FROM apqi WHERE CREDATE >= ? """, (a.desde,)).fetchall()
    total_hist = con.execute("SELECT COUNT(*) FROM apqi").fetchone()[0]

    generadores, externos = {}, defaultdict(lambda: {"sesiones": 0, "grupos": set(),
                                                     "creadores": set(), "nota": ""})
    por_mes = defaultdict(Counter)
    for prog, grupo, creador, fecha, estado, trans, dest in filas:
        prog = (prog or "").strip()
        g = generadores.setdefault(prog, {"sesiones": 0, "creadores": set(),
                                          "primera": fecha, "ultima": fecha,
                                          "estados": Counter()})
        g["sesiones"] += 1
        g["creadores"].add((creador or "").strip())
        g["primera"] = min(g["primera"] or fecha, fecha or "")
        g["ultima"] = max(g["ultima"] or fecha, fecha or "")
        g["estados"][(estado or "").strip()] += 1

        if prog == "SAPMSSY1":
            # 'vino de fuera por RFC'. La herramienta no esta en PROGID: se abre por GROUPID.
            dom, nota = gramatica_de(grupo)
            clave = dom or "EXTERNO sin gramatica reconocida"
            e = externos[clave]
            e["sesiones"] += 1
            e["grupos"].add((grupo or "").strip())
            e["creadores"].add((creador or "").strip())
            e["nota"] = nota or ("el GROUPID no encaja en ninguna gramatica conocida: es un "
                                 "generador externo que todavia no sabemos nombrar")
            por_mes[clave][(fecha or "")[:6]] += 1
        else:
            por_mes[prog][(fecha or "")[:6]] += 1

    salida = []
    for prog, g in sorted(generadores.items(), key=lambda kv: -kv[1]["sesiones"]):
        d = dom_de(prog) if prog != "SAPMSSY1" else "EXTERNO_RFC"
        propio = prog[:1] in ("Z", "Y")
        salida.append({
            "progid": prog, "dominio": d, "sesiones": g["sesiones"],
            "creadores": len(g["creadores"]), "primera": g["primera"], "ultima": g["ultima"],
            "estados": dict(g["estados"]),
            "autoria": "PROPIO" if propio else ("EXTERNO por RFC" if prog == "SAPMSSY1"
                                                else "de SAP"),
            "codigo_auditable": (not propio) or None,
            "por_mes": dict(sorted(por_mes.get(prog, {}).items())),
        })

    ext = [{"dominio": k, "sesiones": v["sesiones"], "grupos": len(v["grupos"]),
            "creadores": len(v["creadores"]), "como_se_reconoce": v["nota"],
            "por_mes": dict(sorted(por_mes.get(k, {}).items()))}
           for k, v in sorted(externos.items(), key=lambda kv: -kv[1]["sesiones"])]

    propios = [s for s in salida if s["autoria"] == "PROPIO"]
    doc = {
        "_algoritmo": "A31_bdc_channel_mining",
        "_que_es": ("el canal batch input minado desde APQI: quien genera sesiones, de donde "
                    "vienen y a que dominio pertenecen"),
        "_LO_QUE_NO_SE_PUEDE_SABER": (
            "APQI es una COLA: las sesiones que se procesan BIEN SE BORRAN. Esto no mide cuanto "
            "batch input se hace, mide cuanto QUEDA VISIBLE -- lo que fallo, lo que nadie corrio "
            "y lo reciente. Confundir las dos cosas produjo una conclusion falsa el 2026-08-24"),
        "_progid_no_es_la_transaccion": (
            "PROGID dice el PROGRAMA que genero la sesion, no la transaccion que ejecuta. "
            "SAPMSSY1 solo significa 'vino de fuera por RFC' y no identifica la herramienta: "
            "eso se abre por GROUPID, que es lo unico que la sesion externa trae consigo"),
        "ventana": f"CREDATE >= {a.desde}",
        "sesiones_en_ventana": len(filas), "sesiones_en_toda_la_cola": total_hist,
        "generadores": salida,
        "externos_por_rfc_abiertos_por_groupid": ext,
        "_el_hueco": ([f"{s['progid']} ({s['dominio']}, {s['sesiones']} sesiones)"
                       for s in propios] and
                      {"que_pasa": ("estos generadores son CODIGO PROPIO que escribe en "
                                    "produccion por BDC. Si su fuente no esta extraida, no se "
                                    "puede auditar que hacen"),
                       "generadores_propios": [s["progid"] for s in propios]}),
    }
    SALIDA.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        from mining_bus import publicar
        for s in salida[:12]:
            publicar("A31_bdc_channel_mining", "CANAL_Y_ACTOR", s["progid"],
                     f"genera {s['sesiones']} sesiones de batch input desde {a.desde} "
                     f"({s['creadores']} creadores, dominio {s['dominio']}, {s['autoria']})",
                     evidencia="apqi agrupado por PROGID, brain_v2/bdc_channel.json",
                     aspecto="genera_batch_input")
        for e in ext:
            publicar("A31_bdc_channel_mining", "CANAL_Y_ACTOR", f"EXTERNO:{e['dominio']}",
                     f"{e['sesiones']} sesiones externas por RFC en {e['grupos']} grupos. "
                     f"{e['como_se_reconoce']}",
                     evidencia="apqi PROGID=SAPMSSY1 abierto por gramatica de GROUPID",
                     aspecto="genera_batch_input")
    except Exception as e:
        print(f"  AVISO: no se pudo publicar en el bus ({type(e).__name__})")

    print(f"CANAL BATCH INPUT desde {a.desde}: {len(filas):,} sesiones visibles "
          f"(de {total_hist:,} en toda la cola)")
    print("  OJO: la cola BORRA lo que se proceso bien. Esto es lo que QUEDA, no lo que pasa.\n")
    print(f"  {'generador':24s} {'dominio':22s} {'sesiones':>9s} {'creadores':>10s}  autoria")
    for s in salida[:12]:
        print(f"  {s['progid'][:24]:24s} {str(s['dominio'])[:22]:22s} {s['sesiones']:>9,} "
              f"{s['creadores']:>10}  {s['autoria']}")
    print(f"\n  externos por RFC, abiertos por GROUPID:")
    for e in ext:
        print(f"    {e['dominio'][:34]:34s} {e['sesiones']:>7,} sesiones · {e['grupos']:>5} grupos"
              f" · {e['creadores']} creadores")
    if propios:
        print(f"\n  CODIGO PROPIO que escribe por BDC ({len(propios)}): "
              f"{', '.join(s['progid'] for s in propios)}")
    print(f"\n-> {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
