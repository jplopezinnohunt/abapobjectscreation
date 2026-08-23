"""ALGORITHM A22 - ABRIR UN DOMINIO: de que esta HECHO y CUANDO ocurre.

LA PREGUNTA
    El indice de comprension dice CUANTO entendemos y DONDE. Este dice DE QUE esta hecho cada
    dominio: que objetos lo componen, quien los ejecuta, por que canal, y como se reparte en
    el tiempo. Sin eso, un porcentaje por dominio es un numero sin proceso dentro.

POR QUE EXISTE, Y EL CASO ES EXACTO
    PS salio con 3.501.373 ejecuciones, el 39,1% de toda la actividad de negocio -- mas que FI
    y HCM juntos. Leido asi, PS seria el corazon del sistema.

    Abierto, el 99,7% de su trafico RFC son DOS objetos con UN actor cada uno:
    Y_BAPI_WBS_FINANCIAL_DATA_1 con 1.861.107 llamadas y Y_BAPI_YPS8 con 878.833. Eso no es
    gente gestionando proyectos: es un satelite leyendo datos financieros de WBS en bucle.

    Un dominio puede parecer el mas vivo del sistema porque UNA integracion lo consulta mucho.
    Agregar sin abrir invierte la importancia de las cosas.

LO QUE MIDE, POR DOMINIO
    CONCENTRACION   que fraccion se lleva el objeto mas grande, y cuantos objetos hacen el 90%.
                    Alta concentracion + pocos actores = un canal, no un proceso.
    ACTORES         cuantas personas distintas, ya normalizadas. UNO es un hallazgo: o es un
                    satelite, o es riesgo de persona clave, y las dos cosas importan.
    CANAL           dialogo / informe / RFC entrante / job. En este tenant el 80,6% del
                    trabajo de negocio entra por RFC, asi que "nadie usa esa transaccion"
                    casi nunca significa que el proceso no corra.
    FORMA TEMPORAL  por mes. Un pico a fin de bienio es presupuesto; uno mensual estable es
                    una interfaz; uno que empieza de golpe es algo que se implanto.

FAILURE MODE
    Confundir volumen con importancia, que es el defecto que este algoritmo corrige, y
    confundir concentracion con sospecha: un job nocturno legitimo tambien tiene un actor y
    mucho volumen. Por eso se reporta la FORMA (concentracion, actores, canal, meses) y no un
    veredicto -- el juicio lo pone el agente log-process-discovery.

Uso:
    python brain_v2/domain_composition.py            # una pasada, todos los dominios
    python brain_v2/domain_composition.py PS         # imprime uno ya calculado
"""
import os, sys, json, sqlite3, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")
OUT = os.path.join(ROOT, "brain_v2", "domain_composition.json")
TOP = 15            # objetos que se guardan por dominio y canal
CONCENTRATED = 5    # <= actores para llamarlo concentrado


def classifiers():
    pm = os.path.join(ROOT, "process_mining")
    if pm not in sys.path:
        sys.path.insert(0, pm)
    from importlib import util as u
    s1 = u.spec_from_file_location("eodm", os.path.join(pm, "executed_objects_domain_map.py"))
    m1 = u.module_from_spec(s1); s1.loader.exec_module(m1)
    con = sqlite3.connect(GOLD, timeout=300)
    domain_of, ctx = m1.make_classifier(con)
    s2 = u.spec_from_file_location("lrf", os.path.join(pm, "log_reality_filter.py"))
    m2 = u.module_from_spec(s2); s2.loader.exec_module(m2)
    return domain_of, ctx, m2.classify_program, m2.normalize_actor


def build():
    domain_of, ctx, classify_program, normalize_actor = classifiers()
    q = sqlite3.connect("file:" + GOLD + "?mode=ro", uri=True).execute
    # OBSERVER: nuestras propias lecturas no son actividad del sistema (ver A20)
    obs = "'JP_LOPEZ'"

    dom_obj = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    dom_actors = collections.defaultdict(lambda: collections.defaultdict(set))
    dom_month = collections.defaultdict(collections.Counter)
    dom_observer = collections.Counter()

    def feed(channel, rows, kind, resolve=None):
        for name, n, users, mes in rows:
            if kind == "object":
                k, _, _, _ = classify_program(name)
                if k != "OBJECT":
                    continue
            d = resolve(name) if resolve else domain_of(name)
            dom_obj[d][channel][name] += n
            if mes:
                dom_month[d][mes] += n

    print("1/4 informes y programas ...")
    feed("report", q(f"""SELECT SLGREPNA, COUNT(*), COUNT(DISTINCT SLGUSER),
            SUBSTR(SAL_DATE,1,6) FROM rsau_audit_history
            WHERE SLGREPNA != '' AND SLGUSER NOT IN ({obs})
            GROUP BY SLGREPNA, SUBSTR(SAL_DATE,1,6)"""), "object")

    print("2/4 llamadas RFC ...")
    feed("rfc", q(f"""SELECT PARAM3, COUNT(*), COUNT(DISTINCT SLGUSER),
            SUBSTR(SAL_DATE,1,6) FROM rsau_audit_history
            WHERE TXSUBCLSID = 'RFC Function Call' AND PARAM3 != ''
              AND SLGUSER NOT IN ({obs})
            GROUP BY PARAM3, SUBSTR(SAL_DATE,1,6)"""), "rfc",
         resolve=lambda n: domain_of(n, overlay=ctx["fm_dom"].get(n)))

    print("3/4 cambios ...")
    feed("change", q("""SELECT TCODE, COUNT(*), COUNT(DISTINCT USERNAME),
            SUBSTR(UDATE,1,6) FROM cdhdr_history WHERE TCODE != ''
            GROUP BY TCODE, SUBSTR(UDATE,1,6)"""), "change",
         resolve=lambda n: domain_of(n, program=ctx["tc_prog"].get(n),
                                     text=ctx["tc_text"].get(n)))

    print("4/4 actores por dominio ...")
    for name, user in q(f"""SELECT DISTINCT PARAM3, SLGUSER FROM rsau_audit_history
            WHERE TXSUBCLSID = 'RFC Function Call' AND PARAM3 != ''
              AND SLGUSER NOT IN ({obs})"""):
        d = domain_of(name, overlay=ctx["fm_dom"].get(name))
        k, _ = normalize_actor(user)
        if k:
            dom_actors[d]["rfc"].add(k)
    for name, user in q(f"""SELECT DISTINCT SLGREPNA, SLGUSER FROM rsau_audit_history
            WHERE SLGREPNA != '' AND SLGUSER NOT IN ({obs})"""):
        k0, _, _, _ = classify_program(name)
        if k0 != "OBJECT":
            continue
        d = domain_of(name)
        k, _ = normalize_actor(user)
        if k:
            dom_actors[d]["report"].add(k)

    out = {"_generated_by": "brain_v2/domain_composition.py (A22)",
           "_question": "de que esta HECHO cada dominio, quien lo ejecuta y cuando",
           "_why": ("un porcentaje por dominio es un numero sin proceso dentro. PS parecia el "
                    "39,1% del negocio y son DOS objetos con UN actor: una integracion, no un "
                    "proceso"),
           "_observer_excluded": ["JP_LOPEZ"],
           "_measured_utc": datetime.datetime.now(datetime.timezone.utc)
                            .isoformat(timespec="seconds"),
           "domains": {}}

    for d, chans in dom_obj.items():
        allc = collections.Counter()
        for ch, c in chans.items():
            allc.update(c)
        tot = sum(allc.values())
        if not tot:
            continue
        ranked = allc.most_common()
        top1 = ranked[0][1] / tot
        acc, n90 = 0, 0
        for _, v in ranked:
            acc += v; n90 += 1
            if acc / tot >= 0.90:
                break
        actors = set()
        for s in dom_actors[d].values():
            actors |= s
        months = dict(sorted(dom_month[d].items()))
        out["domains"][d] = {
            "executions": tot,
            "distinct_objects": len(allc),
            "top_object_share_pct": round(100 * top1, 1),
            "objects_for_90pct": n90,
            "actors": len(actors),
            "by_channel": {ch: sum(c.values()) for ch, c in
                           sorted(chans.items(), key=lambda x: -sum(x[1].values()))},
            "top_objects": [{"object": o, "execs": v, "pct": round(100 * v / tot, 1)}
                            for o, v in ranked[:TOP]],
            "by_month": months,
            "shape": _shape(top1, n90, len(actors), months),
        }
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\n-> {OUT}  ({len(out['domains'])} dominios)")
    return out


def _shape(top1, n90, actors, months):
    """La FORMA, no un veredicto. El juicio lo pone el agente."""
    f = []
    if top1 >= 0.50:
        f.append(f"UN objeto se lleva el {top1*100:.0f}%")
    if n90 <= 3:
        f.append(f"{n90} objeto(s) hacen el 90%")
    if actors <= CONCENTRATED:
        f.append(f"solo {actors} actor(es): satelite o persona clave, no una poblacion")
    if months:
        v = list(months.values())
        if len(v) >= 3 and min(v) and max(v) / max(1, min(v)) >= 5:
            f.append("volumen muy desigual entre meses: mirar el pico")
        # NO se declara "algo se implanto" por que el primer mes sea flojo: las dos fuentes
        # tienen VENTANAS distintas -- RSAU cubre ~6 meses (2026-02 en adelante) y CDHDR llega
        # a 2024 -- asi que todo dominio dominado por RFC "arranca" en febrero de 2026 sin que
        # haya pasado nada. Eso seria inventar implantaciones a partir del alcance del
        # instrumento, que es la misma falacia del techo de retencion.
        ks = sorted(months)
        if len(ks) >= 3 and months[ks[0]] < sum(v) / len(v) * 0.1 and ks[0] > "202603":
            f.append(f"arranca en {ks[0]}, y NO es el borde de la ventana del log "
                     f"(RSAU empieza en 202602): mirar si se implanto algo")
    return f or ["reparto sin nada llamativo"]


def show(dom, data=None):
    data = data or json.load(open(OUT, encoding="utf-8"))
    d = data["domains"].get(dom)
    if not d:
        print(f"{dom}: no esta. Hay: {', '.join(sorted(data['domains']))}")
        return
    print(f"\n=== {dom} · {d['executions']:,} ejecuciones · {d['actors']} actores reales ===")
    print("  forma: " + " · ".join(d["shape"]))
    print(f"  {d['distinct_objects']:,} objetos distintos, y {d['objects_for_90pct']} hacen el 90%")
    print("  canal: " + " · ".join(f"{k} {v:,}" for k, v in d["by_channel"].items()))
    print("  objetos:")
    for o in d["top_objects"][:8]:
        print(f"    {o['object'][:44]:44s} {o['execs']:>10,} {o['pct']:>5.1f}%")
    print("  por mes:")
    for m, v in d["by_month"].items():
        print(f"    {m}  {v:>10,}  {'#' * min(50, int(50 * v / max(d['by_month'].values())))}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and os.path.exists(OUT):
        show(sys.argv[1])
    else:
        data = build()
        for dom in sorted(data["domains"],
                          key=lambda x: -data["domains"][x]["executions"])[:4]:
            show(dom, data)
