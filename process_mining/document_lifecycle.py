"""ALGORITMO A24 — EL CICLO DE VIDA DE UN DOCUMENTO, NO SU RECUENTO.

QUE CONTESTA
    Contar transacciones dice VOLUMEN. Esto dice que le PASA a un documento desde que nace
    hasta que muere: cuantas veces se toca, quien lo toca, cuanto vive, si cruza el limite del
    ejercicio, y si su importe sube o baja. Esa es la diferencia entre "se ejecuto FMX2 98.293
    veces" y "hay un documento con 352 modificaciones en 393 dias".

POR QUE EXISTE
    2026-08-24. La pregunta era si UNESCO usa las reservas de fondos para retener presupuesto
    en vez de comprometerlo. Ningun recuento la contesta. La contestaron tres medidas sobre el
    CICLO:
      - el 66,6% de los documentos con 3+ cambios acaban con MENOS importe del que empezaron
      - hasta el 100% de las lineas no llevan acreedor: son retenciones, no obligaciones
      - un documento llega a 352 modificaciones en 393 dias
    Las tres salen de mirar el documento como CASO, no como fila.

EL METODO, EN CUATRO PASOS
    1. CASO       la clave del documento (aqui KBLK.BELNR)
    2. ACTIVIDAD  el ACTO DE NEGOCIO, no el codigo de transaccion. FMX1 y FMW1 son los dos
                  "CREA"; FB01, FB60 y FB50 son los tres "CONSUME". Sin esta traduccion las
                  variantes se multiplican por sinonimos y no se ve el patron.
    3. ORDEN      por fecha y hora, colapsando repeticiones consecutivas del mismo acto
    4. AGRUPAR    por area de gestion financiera, que es lo que separa formas de trabajar

QUE MIRA DE CADA CASO
    variante (el camino) · numero de modificaciones · vida en dias · si se arrastro a otro
    ejercicio · direccion del importe (sube, baja, igual) · si tiene contraparte (acreedor)

FAILURE MODE
    DOS, y las dos dan un resultado creible.
    (1) No traducir el codigo de transaccion al acto: FMX2, FMW2 y FMZ6 son el MISMO programa
        y la MISMA pantalla (SAPLFMFR dynpro 0511) y hacen cosas distintas; tratarlas como una
        sola pierde el bloqueo, y tratarlas como tres crea variantes falsas.
    (2) Mezclar tipos de valor: sin separar por WRTTP, el gasto se cuenta como reserva. Costo
        tres correcciones seguidas el dia que se escribio esto.

Uso:  python process_mining/document_lifecycle.py [--area FIKRS] [--json]
"""
import argparse
import collections
import datetime
import json
import os
import sqlite3
import sys

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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")
OUT = os.path.join(ROOT, "brain_v2", "document_lifecycle.json")

# El acto de NEGOCIO. La traduccion es el nucleo del algoritmo, no un detalle de formato.
ACTO = {
    "FMX1": "CREA", "FMW1": "CREA",
    "FMX2": "MODIFICA",
    "FMW2": "BLOQUEA",
    "FMZ6": "RESERVA",
    "FMMC": "CIERRA",
    "FMJ2": "ARRASTRA", "FMJ0": "ARRASTRA", "FMJ3": "ARRASTRA",
    "FB01": "CONSUME", "FB60": "CONSUME", "FB50": "CONSUME", "FV60": "CONSUME",
    "FBR2": "CONSUME", "MIRO": "CONSUME", "F-43": "CONSUME",
    "FB08": "ANULA",
    "SE38": "MOTOR", "ZPBC_PERIOD_CLS_EXEC": "MOTOR", "PCP0": "MOTOR",
    "HRPBC_ENGINE_PNP": "MOTOR", "PA30": "MOTOR", "HRFPM_VACANCY_DISP": "MOTOR",
    "": "JOB",
}
GESTION = {"CREA", "MODIFICA", "BLOQUEA", "RESERVA", "ARRASTRA", "CIERRA"}


def dias(d0, d1):
    try:
        a = datetime.date(int(d0[:4]), int(d0[4:6]), int(d0[6:8]))
        b = datetime.date(int(d1[:4]), int(d1[4:6]), int(d1[6:8]))
        return (b - a).days
    except Exception:
        return None


def analizar(q, area, solo_gestion=False):
    """-> dict con el perfil de ciclo de vida de un area."""
    rows = q("""SELECT REFBN, TCODE, CPUDT, CPUTM, USNAM, CAST(FKBTR AS REAL), LIFNR
                FROM FMIOI WHERE REFBT='110' AND FIKRS=? AND CPUDT!=''
                ORDER BY REFBN, CPUDT, CPUTM""", (area,)).fetchall()
    casos = collections.defaultdict(list)
    for belnr, tc, d, t, u, v, lif in rows:
        act = ACTO.get(tc, tc or "JOB")
        if solo_gestion and act not in GESTION:
            continue
        if casos[belnr] and casos[belnr][-1][0] == act:
            casos[belnr].append((act, d, u, v, lif))   # se guarda, no se colapsa el conteo
        else:
            casos[belnr].append((act, d, u, v, lif))
    casos = {k: v for k, v in casos.items() if v}
    if not casos:
        return None

    var = collections.Counter()
    vida, mods, arrastrados, baja, sube, igual, sin_lif, tot_lin = [], [], 0, 0, 0, 0, 0, 0
    extremos = []
    for b, ev in casos.items():
        camino = []
        for a, *_ in ev:
            if not camino or camino[-1] != a:
                camino.append(a)
        var[" > ".join(camino)] += 1
        m = sum(1 for e in ev if e[0] == "MODIFICA")
        mods.append(m)
        if any(e[0] == "ARRASTRA" for e in ev):
            arrastrados += 1
        dd = dias(ev[0][1], ev[-1][1])
        if dd is not None:
            vida.append(dd)
        if m >= 3:
            v0, v1 = ev[0][3] or 0, ev[-1][3] or 0
            if v1 < v0:
                baja += 1
            elif v1 > v0:
                sube += 1
            else:
                igual += 1
        for e in ev:
            tot_lin += 1
            if not (e[4] or "").strip():
                sin_lif += 1
        if m >= 10:
            extremos.append({"documento": b, "modificaciones": m, "dias": dd,
                             "usuario": ev[0][2]})
    v = sorted(vida)
    d3 = baja + sube + igual
    extremos.sort(key=lambda x: -x["modificaciones"])
    return {
        "casos": len(casos), "variantes": len(var),
        "una_variante_cada_n_casos": round(len(casos) / max(1, len(var)), 1),
        "camino_dominante": var.most_common(1)[0] if var else None,
        "top_variantes": var.most_common(6),
        "con_3_o_mas_modificaciones": sum(1 for m in mods if m >= 3),
        "pct_3_o_mas": round(100 * sum(1 for m in mods if m >= 3) / len(casos), 1),
        "arrastrados": arrastrados,
        "pct_arrastrados": round(100 * arrastrados / len(casos), 1),
        "vida_mediana_dias": v[len(v) // 2] if v else None,
        "vida_p90_dias": v[int(len(v) * .9)] if v else None,
        "vida_max_dias": v[-1] if v else None,
        "direccion_del_importe": {"baja": baja, "sube": sube, "igual": igual,
                                  "pct_baja": round(100 * baja / d3, 1) if d3 else None},
        "lineas_sin_acreedor_pct": round(100 * sin_lif / tot_lin, 1) if tot_lin else None,
        "los_mas_retocados": extremos[:5],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", help="una sola area de gestion financiera")
    ap.add_argument("--solo-gestion", action="store_true",
                    help="excluir CONSUME: solo crear/modificar/bloquear/arrastrar")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    # LO APRENDIDO, ANTES DE MEDIR EL CICLO. La primera memoria que sale es exactamente el
    # defecto que este minero puede cometer: una tasa construida como eventos-por-ventana MIDE
    # LA VIDA, no el comportamiento -- el 34,7% de los documentos de reserva viven un solo mes y
    # puntuan 1,00 por construccion. Ademas: LIFNR va relleno con ceros (aqui se cuenta
    # `lineas_sin_acreedor_pct`), FMIOI es la tabla de COMPROMISO con tipos de valor que no
    # estan en los reales, y FKBTR no contesta preguntas de tipo de cambio presupuestario.
    if _aprendido:
        _aprendido("fmioi", "reserva", "documento", "fkbtr", "lifnr").avisar()

    if not os.path.exists(GOLD):
        print(f"Gold DB ausente: {GOLD}", file=sys.stderr)
        return 2
    con = sqlite3.connect("file:" + GOLD + "?mode=ro", uri=True)
    q = con.execute
    areas = ([a.area] if a.area else
             [r[0] for r in q("SELECT FIKRS FROM FMIOI WHERE REFBT='110' "
                              "GROUP BY 1 ORDER BY COUNT(*) DESC")])
    rep = {"_generated_by": "process_mining/document_lifecycle.py (A24)",
           "_question": ("que le PASA a un documento en su vida, no cuantas veces se ejecuto "
                         "una transaccion"),
           "_scope": "solo gestion (sin consumo)" if a.solo_gestion else "ciclo completo",
           "_measured_utc": datetime.datetime.now(datetime.timezone.utc)
                            .isoformat(timespec="seconds"),
           "areas": {}}
    for ar in areas:
        r = analizar(q, ar, a.solo_gestion)
        if r:
            rep["areas"][ar] = r

    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        for ar, r in rep["areas"].items():
            dom = r["camino_dominante"]
            print(f"\n=== {ar}  {r['casos']:,} casos · {r['variantes']} variantes "
                  f"(1 cada {r['una_variante_cada_n_casos']}) ===")
            if dom:
                print(f"  camino dominante: {dom[0]}  {dom[1]:,} "
                      f"({100*dom[1]/r['casos']:.1f}%)")
            print(f"  con 3+ modificaciones: {r['pct_3_o_mas']}% · "
                  f"arrastrados: {r['pct_arrastrados']}%")
            print(f"  vida: mediana {r['vida_mediana_dias']}d · p90 {r['vida_p90_dias']}d · "
                  f"max {r['vida_max_dias']}d")
            di = r["direccion_del_importe"]
            if di["pct_baja"] is not None:
                print(f"  importe: BAJA en el {di['pct_baja']}% de los que se retocan 3+ veces")
            print(f"  lineas sin acreedor: {r['lineas_sin_acreedor_pct']}%")
            for e in r["los_mas_retocados"][:3]:
                print(f"     {e['documento']}  {e['modificaciones']} modificaciones  "
                      f"{e['dias']}d  {e['usuario']}")

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
