"""
Tier 1 — CONFORMANCE (the 'as-implemented vs standard' product) for P2P.
Declare-style rule conformance against the 3-way-match reference (Create PO -> Goods Receipt -> Invoice
Receipt): each case is classified into a conformance category + the control-risk deviations are quantified
($ exposure). Plus Tier-2c performance: GR->IR cycle time. Built from EKKO + EKBE (VGABE).

Run:  python process_mining/p2p_conformance.py
"""
import sqlite3, datetime
from collections import defaultdict

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from gold_ref import GOLD  # T5: resolved via golden_manifest.json, not a hardcoded path

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `algorithm_memory.json` guarda, por cada memoria, su `implication`:
# que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no leerlas es
# aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo cada semana.
try:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__))), "process_mining"))
    from metodo import lo_que_ya_aprendimos as _aprendido   # noqa: E402
except Exception:
    _aprendido = None


def d(s):
    try: return datetime.datetime.strptime(s, "%Y%m%d").date()
    except Exception: return None


def main():
    # ANTES de abrir el Gold, no al cerrar: al arrancar, este minero esta a punto de leer justo
    # los datos que contestan lo que le preguntan; al terminar la conexion ya esta cerrada y lo
    # que queda es buena intencion. Los temas son lo que ESTE minero toca -- EKKO (EBELN es su
    # identificador de caso, y hay memoria de que el corte de un id de caso no se deduce del
    # nombre), DMBTR (el importe que suma por PO, con la memoria de que el control FM-vs-FI de
    # la casa ya tiene su propia definicion), BUDAT (ordena el 3-way match por fecha de
    # contabilizacion: SAP convierte por WWERT, no por BUDAT) y la VENTANA, que este fichero
    # imprime totales sin declarar. Ademas saca las preguntas abiertas del foro que puede
    # contestar.
    if _aprendido:
        _aprendido("ekko", "dmbtr", "budat", "ventana").avisar()

    c = sqlite3.connect(GOLD, timeout=10)
    created = {r[0] for r in c.execute("SELECT DISTINCT EBELN FROM ekko")}
    # per PO: GR dates, IR dates, IR amount
    gr, ir, ir_amt = defaultdict(list), defaultdict(list), defaultdict(float)
    for ebeln, budat, vgabe, dmbtr in c.execute(
            "SELECT EBELN,BUDAT,VGABE,DMBTR FROM ekbe WHERE EBELN<>'' AND BUDAT>'0'"):
        dt = d(budat)
        if not dt: continue
        if str(vgabe) == "1": gr[ebeln].append(dt)
        elif str(vgabe) == "2": ir[ebeln].append(dt); ir_amt[ebeln] += abs(float(dmbtr or 0))

    cats = defaultdict(lambda: [0, 0.0])           # category -> [count, $]
    cycle = []                                      # GR->IR days
    for po in created:
        g, i = gr.get(po), ir.get(po)
        amt = ir_amt.get(po, 0.0)
        if not g and not i:
            cat = "1. No receipt (PO only)"
        elif g and not i:
            cat = "2. GR without IR (received, not invoiced)"
        elif i and not g:
            cat = "3. IR without GR (CONTROL RISK: invoiced, never received)"
        elif min(i) < min(g):
            cat = "4. IR before GR (3-way-match VIOLATION risk)"
        elif len(g) == 1 and len(i) == 1:
            cat = "5. Clean 3-way match (Create->GR->IR)"
        else:
            cat = "6. Multi-receipt (partial deliveries)"
        cats[cat][0] += 1; cats[cat][1] += amt
        if g and i and min(i) >= min(g):
            cycle.append((min(i) - min(g)).days)

    total = sum(v[0] for v in cats.values())
    print(f"P2P CONFORMANCE vs 3-way-match reference — {total:,} POs\n")
    print(f"{'category':52} {'POs':>8} {'%':>5} {'IR $ (DMBTR)':>16}")
    for cat in sorted(cats):
        n, amt = cats[cat]
        print(f"  {cat:50} {n:>8,} {100*n//max(total,1):>4}% {amt:>16,.0f}")
    # performance
    if cycle:
        cycle.sort()
        med = cycle[len(cycle)//2]
        avg = sum(cycle)/len(cycle)
        over30 = sum(1 for x in cycle if x > 30)
        print(f"\nGR->IR cycle time: median {med}d, mean {avg:.1f}d, "
              f"{over30:,} POs >30d ({100*over30//len(cycle)}%)")
    print("\nThe ~61% off-happy-path = the product. Risk rows (3=invoiced-not-received, 4=IR-before-GR) "
          "are the audit-grade conformance findings; route to the SoD/control workstream.")


if __name__ == "__main__":
    main()
