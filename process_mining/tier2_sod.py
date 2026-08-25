"""
Tier 2 — systematic Segregation-of-Duties (SoD) from ACTUAL behavior (process_mining_maturity.md).
Grounded in research wwyujjqyk (SoD = function->action->permission ruleset, SAP GRC model). Here we run
the ACTION level against what users ACTUALLY did (rsau_audit_history tcode starts) — not what they're
authorized for. This is the "declared-vs-actual" angle and generalizes the BCM dual-control finding to the
whole landscape as a query. (Permission-level + AGR_* role reconciliation = next increment.)

Run:  python process_mining/tier2_sod.py

DEFECTO VIVO (A48, marcado 2026-08-26) -- NINGUNA CIFRA DE ESTE SCRIPT ES CITABLE HOY
    La consulta de main() agrupa por SLGTC, que en TXSUBCLSID='Transaction Start' es el
    tcode LANZADOR, no el ARRANCADO (ese vive en PARAM1; coinciden en 8 de 1.235.225
    filas). Este NO es un consumidor de semantic_activity_map: es un HERMANO -- no importa
    nada de el -- asi que arreglar aquel y dejar este es arreglar la mitad, y es la mitad
    que produce la cifra de AUDITORIA.
    Aqui el filtro SLGTC<>'' hace MAS dano que en A48 porque la consulta lleva SLGUSER:
    cada fila descartada es un par usuario-tcode PERDIDO, y el descarte cae entero sobre el
    lado de MAESTROS de la regla 1 -- XK01/XK02/FK01/FK02 estan entre los 13 tcodes que
    nunca aparecen como SLGTC. El titular publicado de 32 usuarios con factura + pago sale
    de aqui (claim 213, TIER_1) y por tanto SE DESCONOCE: no sustituir por otra cifra sin
    re-medir por PARAM1.
    El arreglo es cambio de LOGICA y NO se hizo en la corrida del 2026-08-26.
"""
import sqlite3
from collections import defaultdict

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from gold_ref import GOLD  # T5: resolved via golden_manifest.json, not a hardcoded path
try:  # lo ya aprendido sobre ESTE instrumento, antes de minar (no despues)
    from metodo import lo_que_ya_aprendimos as _aprendido
except Exception:
    _aprendido = None

# SoD ruleset (ACTION level) — standard Finance/P2P conflicting function pairs.
# Each rule: name, function A tcodes, function B tcodes. A user doing BOTH = a conflict.
RULES = [
    ("Vendor master + Invoice posting",
     {"XK01", "XK02", "FK01", "FK02", "MK01", "MK02"},
     {"MIRO", "MIR7", "FB60", "FB01", "F-43", "FV60"}),
    ("Invoice posting + Payment/clearing",
     {"MIRO", "MIR7", "FB60", "FB01", "F-43", "FV60"},
     {"F110", "F-53", "F-58", "FBRA", "F.13", "F-44", "FF67"}),
    ("Bank master + Payment",
     {"FI12", "FI01", "FI02", "FI12_HBANK"},
     {"F110", "F-53", "F-58"}),
    ("GL master + JE posting",
     {"FS00", "FSP0", "FSS0"},
     {"FB01", "FB50", "F-02"}),
    ("PO create + Goods receipt",
     {"ME21N", "ME21", "ME22N"},
     {"MIGO", "MB01", "MB31"}),
]

TECH = ("SAPSYS", "JOBBATCH", "WF-BATCH", "MULESOFT", "BRIDGE-RFC", "SMTMSBP", "DDIC", "TMSADM")


def main():
    if _aprendido:
        _aprendido("rsau_audit_history", "slgtc", "slguser", "usr02", "sod", "ventana").avisar()
    c = sqlite3.connect(GOLD, timeout=10)
    c.execute("PRAGMA busy_timeout=10000")
    # user -> {tcode: count}  from real Transaction Start events
    user_tc = defaultdict(lambda: defaultdict(int))
    # >>> A48 - CAUSA RAIZ, VIVA (2026-08-26). Se lee SLGTC (el LANZADOR) y ademas se
    # filtra SLGTC<>'', que descarta justo las filas cuyo tcode arrancado esta en PARAM1.
    # La consulta CORRECTA (no aplicada: es cambio de LOGICA) seria
    #   SELECT SLGUSER, TRIM(PARAM1), COUNT(*) FROM rsau_audit_history
    #    WHERE TXSUBCLSID='Transaction Start' AND TRIM(PARAM1)<>''
    #      AND SLGUSER NOT IN {TECH} AND SLGUSER NOT LIKE '%RFC%' GROUP BY 1,2
    # -- SIN el filtro sobre SLGTC. Y falta una ASERCION que FALLE si alguna regla queda
    # con el lado A o el lado B VACIO: una regla cuyo lado no aparece nunca no da
    # "cero conflictos", da "NO MEDIDO", y el script de hoy no distingue las dos cosas.
    q = (f"SELECT SLGUSER, TRIM(PARAM1), COUNT(*) FROM rsau_audit_history "
         f"WHERE TXSUBCLSID='Transaction Start' AND TRIM(PARAM1)<>'' "
         f"AND SLGUSER NOT IN {TECH} AND SLGUSER NOT LIKE '%RFC%' "
         f"GROUP BY 1, 2")
    for u, tc, n in c.execute(q):
        user_tc[u][tc] += n
    span = c.execute('SELECT MIN(SAL_DATE),MAX(SAL_DATE) FROM rsau_audit_history').fetchone()
    print(f"SoD sobre rsau_audit_history (PARAM1 = tcode ARRANCADO) | span "
          f"{span[0]}->{span[1]} | {len(user_tc):,} usuarios humanos\n")

    # ⛔ UNA REGLA CUYO LADO NO APARECE NUNCA NO DA "CERO CONFLICTOS": DA "NO MEDIDO".
    #
    # Esa es la diferencia que costo el claim 213. Leyendo SLGTC, SEIS de los OCHO tcodes
    # clave del ruleset no aparecian jamas -- XK01/XK02/FK01/FK02 del lado A y
    # F-53/F-58/F-44/FF_5 del lado B -- asi que la regla de maestro-de-proveedor daba cero
    # POR CONSTRUCCION y se leyo como "no hay conflicto ahi". El sesgo no era ruido: era
    # direccional y mutilaba el ruleset por los dos lados.
    vistos = {t for tcs in user_tc.values() for t in tcs}
    no_medibles = []
    for name, A, B in RULES:
        for lado, S in (("A", A), ("B", B)):
            if not (S & vistos):
                no_medibles.append(f"{name} lado {lado}: NINGUNO de {sorted(S)} aparece")
    if no_medibles:
        print("⛔ REGLAS NO MEDIBLES -- su resultado NO es 'cero conflictos', es 'no medido':")
        for x in no_medibles:
            print(f"   {x}")
        print()

    total_conflicts = 0
    for name, A, B in RULES:
        medible = bool(A & vistos) and bool(B & vistos)
        hits = []
        for u, tcs in user_tc.items():
            a = {t: tcs[t] for t in A if t in tcs}
            b = {t: tcs[t] for t in B if t in tcs}
            if a and b:
                hits.append((u, sum(a.values()), sum(b.values()), sorted(a) + ["|"] + sorted(b)))
        hits.sort(key=lambda x: -(x[1] + x[2]))
        marca = "" if medible else "  [NO MEDIBLE: un lado no aparece nunca]"
        print(f"=== {name}: {len(hits)} usuarios en conflicto{marca} ===")
        for u, na, nb, tcs in hits[:8]:
            print(f"  {u:14} A={na:>5} B={nb:>5}  {' '.join(tcs)}")
        if medible:
            total_conflicts += len(hits)
        print()
    print(f"TOTAL conflictos SoD a nivel de accion (usuario x regla, solo reglas MEDIBLES): "
          f"{total_conflicts}")
    if no_medibles:
        print(f"   ({len(no_medibles)} lado(s) de regla sin cobertura: ese trozo NO esta medido)")
    print("Next increments: (1) permission level via AGR_*/USOBX_C; (2) reconcile declared auth vs this "
          "actual behavior (right-unused / done-without-role); (3) time-proximity (same user A then B on same doc).")


if __name__ == "__main__":
    main()
