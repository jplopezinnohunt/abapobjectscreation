"""Cuantas combinaciones CASO -> DOCUMENTO existen de verdad.

Cada fila de CDHDR es un evento con identificador de caso (OBJECTCLAS + OBJECTID). Para que
el evento sirva hay que llegar al documento: sin eso hay un quien-y-cuando sin importe, sin
moneda y sin dueno del dinero.

Se prueba por SONDEO ACOTADO -- N claves distintas contra la tabla destino, con lookup
indexado -- y no con un join completo: el join sobre 520K x 1,9M sin indice por la expresion
substr se queda colgado, medido.

Nada se declara "combina" por que el nombre encaje: se declara por el porcentaje que casa.
"""
import sqlite3, os, json, collections

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

ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")
OUT = os.path.join(ROOT, "brain_v2", "case_spine.json")
N = 250   # claves distintas por clase

# (clase, tabla destino, columnas clave, funcion que parte el OBJECTID)
# El corte se VERIFICA, no se asume: BELEG resulto llevar el MANDANTE incrustado (350) y
# BUKRS de 3 caracteres rellenado a 4, cosa que ningun patron de nombre habria dicho.
SPINE = [
    ("BELEG",      "bkpf", ["BUKRS", "BELNR", "GJAHR"],
     lambda o: (o[3:7].rstrip(), o[7:17], o[17:21])),
    ("EINKBELEG",  "ekko", ["EBELN"], lambda o: (o,)),
    ("BANF",       "eban", ["BANFN"], lambda o: (o,)),
    ("ENTRYSHEET", "essr", ["LBLNI"], lambda o: (o,)),
    ("KRED",       "LFA1", ["LIFNR"], lambda o: (o,)),
    ("MM_SERVICE", "esll", ["PACKNO"], lambda o: (o,)),
    ("ADRESSE",    "ADRC", ["ADDRNUMBER"], lambda o: (o,)),
    # FMRESERV: destino dado por TCDOB (KBLK/KBLP), no por parecido de nombre. KBLK se
    # indexa SOLO por BELNR -- sin GJAHR -- cosa que hay que mirar en DD03L, no suponer.
    ("FMRESERV",   "KBLK", ["BELNR"], lambda o: (o,)),
    # PBC: TCDOB dice HRFPM_FM_DOC, pero esa tabla trae PLVAR, OTYPE y OBJID VACIOS en el
    # 100% de sus 1.393.580 filas (1 solo valor distinto en cada una), asi que no hay por
    # donde unir. Y el OBJECTID de PBC (29 caracteres, p.ej. 01P10000140302026013120260131)
    # tampoco casa contra HRP1000: OBJID='10000140' no existe alli, y los OTYPE reales son
    # CP/S/O/WF/T/WS/RY/PJ, sin P. Se sonda igualmente para que el 0% quede MEDIDO y con
    # fecha, en vez de desaparecer como si nadie lo hubiera intentado.
    ("PBC",        "HRFPM_FM_DOC", ["BELNR"], lambda o: (o,)),
]

con = sqlite3.connect("file:" + GOLD + "?mode=ro", uri=True)
q = con.execute
tables = {r[0] for r in q("select name from sqlite_master where type='table'")}
report = {"_generated_by": "sonda de columna vertebral de casos",
          "_what": "que clases de CDHDR alcanzan su documento, medido y no supuesto",
          "_method": f"{N} claves distintas por clase, lookup indexado, sin join completo",
          "combinations": []}

for klass, tbl, cols, split in SPINE:
    row = {"case_class": klass, "target": tbl, "key": cols}
    if tbl not in tables:
        row.update(status="SIN_TABLA", note=f"{tbl} no esta en la Gold DB")
        report["combinations"].append(row); print(f"  {klass:12s} SIN TABLA ({tbl})"); continue
    have = {c.upper() for c in
            (r[1].upper() for r in q(f'pragma table_info("{tbl}")'))}
    missing = [c for c in cols if c.upper() not in have]
    if missing:
        row.update(status="SIN_COLUMNA", note=f"{tbl} no tiene {missing}; tiene {sorted(have)[:12]}")
        report["combinations"].append(row); print(f"  {klass:12s} SIN COLUMNA {missing}"); continue

    ids = [r[0] for r in q("select distinct OBJECTID from cdhdr_history "
                           "where OBJECTCLAS=? and OBJECTID!='' limit ?", (klass, N))]
    where = " and ".join(f'"{c}"=?' for c in cols)
    hit = 0; sample = []
    for oid in ids:
        try:
            k = split(oid)
        except Exception:
            continue
        d = q(f'select * from "{tbl}" where {where} limit 1', k).fetchone()
        if d:
            hit += 1
            if len(sample) < 3:
                sample.append({"objectid": oid, "key": list(k)})
    pct = round(100 * hit / len(ids), 1) if ids else 0.0
    row.update(status=("COMBINA" if pct >= 70 else "PARCIAL" if pct >= 20 else "NO_COMBINA"),
               probed=len(ids), matched=hit, pct=pct, sample=sample)
    report["combinations"].append(row)
    print(f"  {klass:12s} -> {tbl:8s} {pct:>5}% ({hit}/{len(ids)})  {row['status']}")

# volumen por clase, para saber cual pesa
vol = dict(q("select OBJECTCLAS, count(*) from cdhdr_history where OBJECTCLAS!='' "
             "group by 1 order by 2 desc").fetchall())
for r in report["combinations"]:
    r["changes_in_log"] = vol.get(r["case_class"], 0)
report["_coverage"] = {
    "classes_probed": len(SPINE),
    "combining": sum(1 for r in report["combinations"] if r.get("status") == "COMBINA"),
    "changes_reachable": sum(r["changes_in_log"] for r in report["combinations"]
                             if r.get("status") == "COMBINA"),
    "changes_total": sum(vol.values()),
    "classes_never_probed": len(vol) - len(SPINE),
}
json.dump(report, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
cv = report["_coverage"]
print(f"\n  combinan {cv['combining']} de {cv['classes_probed']} probadas")
print(f"  cambios alcanzables {cv['changes_reachable']:,} de {cv['changes_total']:,} "
      f"({100*cv['changes_reachable']/max(1,cv['changes_total']):.1f}%)")
print(f"  clases NUNCA sondeadas: {cv['classes_never_probed']}")
print(f"-> {OUT}")
