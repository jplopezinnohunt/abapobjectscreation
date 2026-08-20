# -*- coding: utf-8 -*-
"""EXPLORADOR DEL MODELO DE BANCA: no calcula lo que le dicen, busca lo que falta.

LA DIFERENCIA CON house_bank_roles.py
    El censo calcula EXACTAMENTE lo que se le programo. Es util y es ciego: el 2026-08-20
    la categoria TESORERIA y las CUENTAS RECEPTORAS las encontro una persona a mano, no el
    algoritmo, porque el algoritmo no tenia forma de notar que su taxonomia se quedaba corta.

    Este explorador hace la otra mitad: recorre el modelo preguntando "hay estructura aqui
    que no estemos modelando", compara contra la foto anterior para ver que se movio, y --
    sobre todo -- DECLARA LO QUE NO PUEDE VER en vez de emitir un cero.

    Tres veces el mismo dia un denominador incompleto casi produjo una conclusion inventada
    (lista truncada, filas excluidas, extracto parcial). Por eso la sonda de integridad de
    denominadores es la primera y es bloqueante.

QUE EMITE Y DONDE ATERRIZA  (regla: un algoritmo que descubre y no aterriza es una nota)
    brain_v2/bank_model_findings.json  -- hallazgos tipados, listos para que el brain-steward
    los promueva a claims o a PMO. Cada hallazgo lleva veredicto:
        NEW    algo que no encaja en la taxonomia actual -> el modelo se queda corto
        DRIFT  algo cambio respecto a la foto anterior
        BLIND  no podemos verlo, y decirlo es el hallazgo
        RISK   encaja en el modelo y merece accion
        STABLE sin novedad

USO
    python brain_v2/bank_model_explorer.py
    python brain_v2/bank_model_explorer.py --json    (solo el fichero, sin narrar)

Claims 530-536. Nodo: knowledge/domains/Treasury/house_bank_operating_roles.md
"""
import collections
import io
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")
MODEL = os.path.join(HERE, "house_bank_roles.json")
OUT = os.path.join(HERE, "bank_model_findings.json")
SNAP = os.path.join(HERE, "bank_model_snapshot.json")

# Cubos de la taxonomia que significan "no supe clasificarlo". Si crecen, el modelo se
# queda corto -- no los bancos.
FALLBACK_BUCKETS = {"CORREDOR ESTRECHO", "SIN DESTINO RESOLUBLE", "MIXTO"}

# Los jobs que mueven los ficheros de la frontera bancaria. Si uno para, el modelo sigue
# calculando tan feliz sobre datos que ya no entran.
CHANNEL_JOBS = {
    "FEB_FILE_HANDLING": "entrada de extractos: sondea la carpeta y dispara FF_5",
    "RBNK_IMPORT_PAYM_STATUS_REPORT": "estado de pago que devuelve el banco (por BANCO)",
    "ZFI_SWIFT_UPLOAD_BCM": "acuse SWIFT de los ficheros enviados (por SOCIEDAD)",
}


def _q(con, sql, args=()):
    try:
        return list(con.execute(sql, args))
    except sqlite3.Error:
        return None


def explore():
    if not os.path.exists(MODEL):
        print("Falta %s -- ejecuta antes house_bank_roles.py" % MODEL)
        return None
    doc = json.load(io.open(MODEL, encoding="utf-8"))
    banks = {b["house_bank"]: b for b in doc["banks"]}
    con = sqlite3.connect("file:%s?mode=ro" % GOLD, uri=True) if os.path.exists(GOLD) else None
    F = []

    def add(probe, verdict, title, detail, evidence=None):
        F.append({"probe": probe, "verdict": verdict, "title": title,
                  "detail": detail, "evidence": evidence or {}})

    # --- 1. integridad de denominadores. Primera y bloqueante.
    bad = []
    for ctry, c in doc.get("corridors", {}).items():
        s = sum(x["lines"] for x in c["served_by"])
        if s != c["lines"]:
            bad.append({"country": ctry, "total": c["lines"], "breakdown": s})
    if bad:
        add("denominator_integrity", "RISK",
            "Un desglose no suma su total: el modelo publicaria porcentajes falsos",
            "En %d corredor(es) la suma de served_by no coincide con lines. Un total correcto "
            "con un desglose incompleto es peor que no tener desglose -- paso tres veces el "
            "2026-08-20." % len(bad), {"corridors": bad[:10]})
    else:
        add("denominator_integrity", "STABLE",
            "Los desgloses suman sus totales", "Comprobados %d corredores."
            % len(doc.get("corridors", {})))

    # --- 2. residuo de taxonomia: cuanto NO sabemos clasificar
    live = [b for b in doc["banks"] if b["lines"] >= 50]
    res = [b for b in live if b["topology"] in FALLBACK_BUCKETS or b["role"] in FALLBACK_BUCKETS]
    share = len(res) / float(len(live) or 1)
    if share >= 0.25:
        add("taxonomy_residue", "NEW",
            "El %.0f%% de los bancos vivos cae en un cubo de 'no supe clasificarlo'" % (100 * share),
            "%d de %d bancos quedan en %s. Cuando ese residuo es grande el que se queda corto "
            "es el MODELO, no los datos: mirar si hay un tipo nuevo escondido ahi, como paso "
            "con TESORERIA y con las cuentas receptoras."
            % (len(res), len(live), ", ".join(sorted(FALLBACK_BUCKETS))),
            {"banks": [b["house_bank"] for b in res][:20]})
    else:
        add("taxonomy_residue", "STABLE",
            "Residuo de taxonomia bajo (%.0f%%)" % (100 * share), "%d de %d bancos sin tipo claro."
            % (len(res), len(live)))

    # --- 3. deriva contra la foto anterior
    prev = json.load(io.open(SNAP, encoding="utf-8")) if os.path.exists(SNAP) else None
    if prev:
        moved, gone = [], []
        for hb, b in banks.items():
            p = prev.get(hb)
            if p and p.get("topology") != b["topology"]:
                moved.append({"bank": hb, "de": p["topology"], "a": b["topology"]})
        for hb in prev:
            if hb not in banks:
                gone.append(hb)
        new = [hb for hb in banks if hb not in prev]
        if moved or gone or new:
            add("role_drift", "DRIFT", "El rol de algun banco se movio",
                "%d cambiaron de tipo, %d nuevos, %d desaparecieron." % (len(moved), len(new), len(gone)),
                {"moved": moved[:15], "new": new[:15], "gone": gone[:15]})
        else:
            add("role_drift", "STABLE", "Ningun banco cambio de tipo", "Comparado con la foto anterior.")
    else:
        add("role_drift", "BLIND", "No hay foto anterior con la que comparar",
            "Primera ejecucion: se guarda la instantanea y a partir de la proxima se detecta deriva.")

    # --- 4. cuentas que COBRAN: REGUH solo ve dinero saliendo
    if con:
        feb = _q(con, "SELECT TRIM(COALESCE(HBKID,'')), COUNT(*), MAX(AZDAT), "
                      "COUNT(DISTINCT TRIM(BUKRS)) FROM FEBKO_2024_2026 GROUP BY 1")
        if feb is None:
            add("receiving_accounts", "BLIND", "No hay tabla de extractos en el Gold DB",
                "Sin FEBKO no se pueden ver las cuentas que cobran. Un modelo derivado solo de "
                "REGUH es ciego a ellas por construccion.")
        else:
            ccs = set()
            for row in _q(con, "SELECT DISTINCT TRIM(BUKRS) FROM FEBKO_2024_2026") or []:
                ccs.add(row[0])
            allcc = {c for c in (doc.get("companies") or {})}
            missing = sorted(allcc - ccs)
            recv = [(hb, n, d) for hb, n, d, _ in feb if hb and hb not in banks]
            if recv:
                add("receiving_accounts", "NEW",
                    "%d cuenta(s) con extracto y CERO pagos: no pagan, COBRAN" % len(recv),
                    "REGUH solo ve dinero saliendo, asi que el censo de pagos no puede verlas. "
                    "Es un rol que el modelo aun no representa.",
                    {"accounts": [{"bank": h, "statements": n, "last": d} for h, n, d in
                                  sorted(recv, key=lambda x: -x[1])[:12]]})
            if missing:
                add("statement_coverage", "BLIND",
                    "El extracto de FEBKO es PARCIAL: faltan %d sociedad(es)" % len(missing),
                    "FEBKO_2024_2026 no cubre %s. Cruzar pagos contra extractos con esta tabla "
                    "produce conclusiones invertidas -- el 2026-08-20 salia que los hubs no "
                    "reciben extractos, que es falso (claim 535). NO publicar ninguna columna "
                    "de 'recibe extracto' hasta completar la extraccion."
                    % ", ".join(missing), {"missing_company_codes": missing})

    # --- 5. la frontera: si el job para, el modelo mide un rio seco
    if con:
        for prog, what in CHANNEL_JOBS.items():
            r = _q(con, "SELECT COUNT(*), MAX(o.SDLSTRTDT) FROM tbtco o JOIN tbtcp p "
                        "ON p.JOBNAME=o.JOBNAME AND p.JOBCOUNT=o.JOBCOUNT "
                        "WHERE UPPER(TRIM(p.PROGNAME))=?", (prog,))
            if not r or not r[0][0]:
                add("channel_jobs", "BLIND", "Sin rastro del job %s" % prog,
                    "%s. O no corre, o no esta en la extraccion de TBTCO. Las dos posibilidades "
                    "importan y no se distinguen desde aqui." % what)
            else:
                n, last = r[0]
                add("channel_jobs", "STABLE", "%s activo" % prog,
                    "%s -- %d ejecuciones, ultima programada %s." % (what, n, last),
                    {"executions": n, "last": last})

    # --- 6. cuentas muertas: configuradas y sin mover dinero
    dead = [b for b in doc["banks"]
            if b["lines"] >= 100 and b.get("last_run", "") and b["last_run"][:4] <= "2024"]
    if dead:
        add("dead_accounts", "RISK", "%d banco(s) casa sin actividad desde 2024 o antes" % len(dead),
            "Una cuenta abierta y sin uso es superficie de riesgo, no un dato neutro. "
            "Confirmar con Tesoreria si se cierran o se mantienen a proposito.",
            {"banks": [{"bank": b["house_bank"], "country": b["country"],
                        "lines": b["lines"], "last_run": b["last_run"]}
                       for b in sorted(dead, key=lambda x: x["last_run"])]})

    # --- 7. banco de un solo metodo: hace exactamente una cosa
    mono = [b for b in live if len(b.get("methods", [])) == 1]
    if mono:
        add("single_purpose", "NEW" if len(mono) > 3 else "STABLE",
            "%d banco(s) ejecutan UN SOLO metodo de pago" % len(mono),
            "Un banco que hace exactamente una cosa suele merecer un rol con nombre propio en "
            "vez de caer en un cubo generico. Mirar si comparten proposito.",
            {"banks": [{"bank": b["house_bank"], "country": b["country"],
                        "method": b["methods"][0], "topology": b["topology"],
                        "lines": b["lines"]} for b in sorted(mono, key=lambda x: -x["lines"])[:12]]})

    # --- 8. la sociedad manda: bancos cuyo pais no puede despachar PPC
    comps = doc.get("companies") or {}
    if comps:
        nofr = {c: v for c, v in comps.items() if v.get("country") not in ("FR",) and v["lines"] >= 1000}
        if nofr:
            add("company_frame", "RISK",
                "%d sociedad(es) no francesas: su pais no alcanza la clase que despacha PPC" % len(nofr),
                "El pais de la SOCIEDAD decide el marco -- que T042Z aplica y que clase BAdI se "
                "selecciona. Ninguna de estas puede renderizar purpose codes por construccion, "
                "por mucho que su beneficiario este en un pais configurado.",
                {"companies": [{"cc": c, "country": v["country"], "lines": v["lines"]}
                               for c, v in sorted(nofr.items(), key=lambda kv: -kv[1]["lines"])]})

    if con:
        con.close()

    # instantanea para la proxima deriva
    io.open(SNAP, "w", encoding="utf-8", newline="\n").write(json.dumps(
        {hb: {"topology": b["topology"], "role": b["role"], "lines": b["lines"]}
         for hb, b in banks.items()}, indent=2, ensure_ascii=False))

    doc_out = {
        "_what_this_is": ("Hallazgos del explorador del modelo de banca. NO es un informe de "
                          "estado: cada entrada es algo que el modelo no sabia, no puede ver, o "
                          "que se movio. Listo para que el brain-steward lo promueva."),
        "_lands_in": ["brain_v2/claims/claims.json",
                      ".agents/intelligence/PMO_BRAIN.md",
                      "knowledge/domains/Treasury/house_bank_operating_roles.md"],
        "_generated_by": "brain_v2/bank_model_explorer.py",
        "findings": F,
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(doc_out, indent=2, ensure_ascii=False))
    return doc_out


def narrate(d):
    order = {"RISK": 0, "NEW": 1, "BLIND": 2, "DRIFT": 3, "STABLE": 4}
    F = sorted(d["findings"], key=lambda f: order.get(f["verdict"], 9))
    print("=" * 82)
    print("EXPLORADOR DEL MODELO DE BANCA -- que no sabemos, que no vemos, que se movio")
    print("=" * 82)
    for f in F:
        print("\n[%-6s] %s" % (f["verdict"], f["title"]))
        for line in _wrap(f["detail"], 78):
            print("          " + line)
        ev = f.get("evidence") or {}
        for k, v in list(ev.items())[:2]:
            if isinstance(v, list) and v:
                print("          %s: %s" % (k, json.dumps(v[:4], ensure_ascii=False)[:200]))
    c = collections.Counter(f["verdict"] for f in F)
    print("\n" + "-" * 82)
    print("  " + " | ".join("%s %d" % (k, c[k]) for k in ("RISK", "NEW", "BLIND", "DRIFT", "STABLE") if c[k]))
    print("  aterriza en: %s" % ", ".join(d["_lands_in"]))
    print("  emitido: brain_v2/bank_model_findings.json")


def _wrap(t, w):
    out, cur = [], ""
    for word in t.split():
        if len(cur) + len(word) + 1 > w:
            out.append(cur); cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        out.append(cur)
    return out


if __name__ == "__main__":
    d = explore()
    if not d:
        sys.exit(2)
    if "--json" not in sys.argv[1:]:
        narrate(d)
    sys.exit(0)
