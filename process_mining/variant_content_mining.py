"""A33 — LA VARIANTE ES EL PROCESO. Leer, INTERPRETAR, AGRUPAR y decir dónde se usó.

POR QUE NO BASTA CON LEERLAS
    Volcar el contenido de una variante produce una lista de pares campo/valor que no dice nada.
    El metodo tiene cuatro pasos y los tres ultimos son los que valen:

      LEER        RS_VARIANT_CONTENTS_255_RFC (255 porque las RUTAS son largas y la version
                  corta las trunca sin avisar)
      INTERPRETAR cada parametro cae en una de tres clases, y confundirlas rompe datos:
                    SELECCION  que objetos se procesan  -> ES el proceso
                    MODO       flags y config           -> CAMBIA el comportamiento
                    RESIDUO    fechas y handles de log  -> estado de la ULTIMA corrida
                  "hazlas identicas" sin esta clasificacion borra nombres de sesion batch y
                  voltea banderas de alcance (medido 2026-08-21).
      AGRUPAR     por FORMA DE TRABAJAR, no por programa. El mecanismo de seleccion cambia
                  entre variantes del MISMO programa: en SAPF100/UNES, UNES_DEPOSIT selecciona
                  por 16 valores EQ sueltos mientras UNES_UNBA usa rangos BT. Decir "se anade
                  por rangos" es falso la mitad de las veces.
      DONDE SE USO  TBTCO/TBTCP: cuantas veces corrio, cuando fue la ultima, con que usuario.
                  Una variante rica que no corre desde 2019 no es el proceso: es un fosil.

LO QUE SALE, Y NO ESTA EN NINGUN OTRO SITIO
    Las RUTAS DE FICHERO. Un job que escribe en una carpeta compartida ES una interfaz y no
    figura en rfcdes ni en el inventario de servicios. Esta es la unica forma de verla.

    Y su reverso: lo CONFIGURADO QUE QUEDA FUERA de toda variante. No da error -- simplemente
    no ocurre nunca. Toda auditoria de configuracion que no cruce contra la variante esta
    incompleta por construccion.

Uso:  python process_mining/variant_content_mining.py [--max-programas N]
Aterriza en: brain_v2/variant_content.json  + publica en el bus de mineros
Metodo completo: .claude/agents/variant-intelligence.md
"""
import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SALIDA = REPO / "brain_v2" / "variant_content.json"
sys.path.insert(0, str(REPO / "process_mining"))
sys.path.insert(0, str(REPO / "Zagentexecution" / "mcp-backend-server-python"))

# Una RUTA de verdad, no cualquier cosa que empiece por barra. La primera version casaba con
# '/STANDARD' -- que es un nombre de LAYOUT, no un fichero -- y publicaba dos interfaces que no
# existen. Se exige: unidad de disco, ruta UNC, ruta con AL MENOS DOS segmentos, un logico DIR_,
# o un nombre de fichero con extension conocida.
RUTA = re.compile(
    r"[A-Za-z]:\\[\w.\\$ -]{3,}"                      # C:\algo\...
    r"|\\\\[\w.$-]+\\[\w.\\$ -]{2,}"                  # \\servidor\recurso\...
    r"|/[\w.$-]+/[\w./$-]{2,}"                        # /dir/dir/...
    r"|\bDIR_[A-Z_]{3,}\b"                            # logico de SAP (FILE / DIR_HOME)
    r"|\b[\w-]{2,}\.(?:txt|csv|xml|dat|xls|xlsx|zip|pdf|log|asc|mt94\d|p8|pgp|ret|out)\b",
    re.I)

# RESIDUO: guarda el estado de la ultima corrida, no el diseno del proceso. Copiarlo entre
# sistemas propaga basura; compararlo produce diferencias que no significan nada.
RESIDUO = re.compile(r"BUDAT|BLDAT|STICHTAG|DATUM|_DATE|_DAT$|LVIEW|BUPEM|LOGHANDLE|LAUFD|"
                     r"^P_?DATE|ZEIT|TIME", re.I)
# MODO: no dice QUE se procesa sino COMO. Es donde vive el comportamiento.
MODO = re.compile(r"^X_|TEST|SIMU|^PAR_|BNAM|UPD|BWMET|^P_?MODE|BATCH|PROT|LIST|LAYOUT|FORM|"
                  r"^PA_WE|DRUCK|PRINT|VARI$|SPOOL", re.I)


def gold():
    from gold_ref import GOLD  # type: ignore
    return sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True, timeout=600)


def clase_de(selname, kind):
    """SELECCION / MODO / RESIDUO. La distincion no es cosmetica: decide que se puede copiar."""
    s = (selname or "").upper()
    if RESIDUO.search(s):
        return "RESIDUO"
    if MODO.search(s):
        return "MODO"
    return "SELECCION" if (kind or "").upper() == "S" else "MODO"


def mecanismo(sel):
    """COMO selecciona esta variante. Cambia entre variantes del mismo programa, y por eso no
    se puede decir 'se anade por rangos' sin haber leido la variante concreta."""
    ops = Counter(x.get("OPTION", "").upper() for x in sel if x.get("OPTION"))
    if not ops:
        return "SIN_SELECCION"
    if ops.get("BT", 0) and not (ops.get("EQ", 0) > ops.get("BT", 0) * 2):
        return "RANGOS_BT"
    if ops.get("EQ", 0) >= 5:
        return "LISTA_EQ"
    if ops.get("CP", 0):
        return "PATRON_CP"
    return "MIXTO(" + "+".join(k for k, _ in ops.most_common(3)) + ")"


def disenadas(con, tope_variantes=20, min_pasos=20):
    filas = con.execute("""SELECT PROGNAME, VARIANT, COUNT(*) FROM tbtcp
                           WHERE TRIM(COALESCE(VARIANT,'')) <> ''
                           GROUP BY 1,2""").fetchall()
    porprog = defaultdict(lambda: [set(), 0])
    for p, v, n in filas:
        porprog[p][0].add(v)
        porprog[p][1] += n
    out = [(p, sorted(vs), pasos) for p, (vs, pasos) in porprog.items()
           if len(vs) <= tope_variantes and pasos >= min_pasos]
    out.sort(key=lambda t: -t[2])
    return out, len(filas)


def uso_de(con, prog, var):
    """DONDE SE USO. Una variante rica que no corre desde hace anos es un fosil, no el proceso."""
    # La columna de fecha de tbtco es SDLSTRTDT, no SDLDATE. Con el nombre equivocado la
    # consulta fallaba, el except devolvia {} y `uso` salia VACIO en las 115 variantes -- pero
    # el algoritmo quedo registrado diciendo que cruzaba tbtcp x tbtco "cuantas veces, primera
    # y ultima, cuantos usuarios". Afirmar en el registro lo que el codigo no hace es peor que
    # no tener la capa: nadie va a volver a mirarla.
    try:
        r = con.execute("""SELECT COUNT(DISTINCT p.JOBNAME), COUNT(*),
                                  MIN(o.SDLSTRTDT), MAX(o.SDLSTRTDT),
                                  COUNT(DISTINCT p.AUTHCKNAM),
                                  SUM(CASE WHEN o.STATUS='A' THEN 1 ELSE 0 END)
                           FROM tbtcp p LEFT JOIN tbtco o
                             ON o.JOBNAME = p.JOBNAME AND o.JOBCOUNT = p.JOBCOUNT
                           WHERE p.PROGNAME = ? AND p.VARIANT = ?""", (prog, var)).fetchone()
    except sqlite3.Error as e:
        return {"_no_medible": f"tbtcp x tbtco: {str(e)[:70]}"}
    if not r or not r[1]:
        return {"_no_medible": "esta variante no aparece en ningun paso de job"}
    return {"jobs": r[0], "pasos": r[1], "primera": r[2], "ultima": r[3],
            "usuarios": r[4], "corridas_abortadas": r[5],
            "_es_un_fosil": (bool(r[3]) and str(r[3])[:4] < "2025")}


def del_gold(con, programa, variante):
    """EL GOLD DB PRIMERO, SIEMPRE. Antes de abrir una conexion a P01 se mira si el dato ya
    esta extraido: es gratis, es instantaneo y no depende de que la VPN este en pie.

    Esta funcion nacio de saltarse la regla: el minero fue directo por RFC, P01 dejo de
    responder a media corrida, y resulto que las variantes de SAPF100 llevaban extraidas desde
    agosto en sapf100_varid. Se pago una lectura de SAP -- y una caida -- por un dato que ya
    estaba en casa.
    """
    for tabla in (f"{programa.lower()}_varid", "varid_content", "variant_values"):
        try:
            filas = con.execute(
                f"SELECT SELNAME, KIND, SIGN, OPTION, LOW, HIGH FROM [{tabla}] "
                f"WHERE UPPER(REPORT)=? AND UPPER(TRIM(VARIANT))=? "
                f"AND TRIM(COALESCE(SELNAME,'')) <> ''",
                (programa.upper(), variante.upper())).fetchall()
        except sqlite3.Error:
            continue
        if filas:
            return [{"SELNAME": r[0], "KIND": r[1], "SIGN": r[2], "OPTION": r[3],
                     "LOW": r[4], "HIGH": r[5]} for r in filas]
    return None


def gold_sirve(con):
    """¿El Gold tiene CONTENIDO de variante, o solo la cascara?

    Medido 2026-08-25: `sapf100_varid` existe con las columnas correctas y sus 21 filas estan
    VACIAS -- REPORT='SAPF100' y todo lo demas en blanco. `varid_content` y `variant_values` no
    existen. Asi que "el Gold primero" no ha evitado ni una lectura de SAP: 115 de 115 se
    leyeron por RFC.

    Una tabla que existe y esta vacia es peor que una que falta: parece cobertura. Por eso esto
    se comprueba y se DECLARA en la salida, en vez de dejar la regla como un adorno.
    """
    for tabla in ("sapf100_varid", "varid_content", "variant_values"):
        try:
            n = con.execute(f"SELECT COUNT(*) FROM [{tabla}] "
                            f"WHERE TRIM(COALESCE(SELNAME,'')) <> ''").fetchone()[0]
        except sqlite3.Error:
            continue
        if n:
            return {"sirve": True, "tabla": tabla, "filas_con_contenido": n}
    return {"sirve": False,
            "_por_que": ("las tablas de variante del Gold existen pero estan VACIAS: 21 filas "
                         "de sapf100_varid sin SELNAME. Una tabla vacia parece cobertura y no "
                         "lo es, asi que todo se lee por RFC"),
            "_que_falta": ("extraer VARI/VARID con contenido para las 127 variantes disenadas; "
                           "hasta entonces la regla del Gold-primero es correcta y ociosa")}


def contenido(conn, programa, variante):
    """255 primero: las rutas son largas y la version corta las TRUNCA SIN AVISAR."""
    # `err` inicializado: si las dos llamadas tienen EXITO y devuelven cero filas -- una
    # variante que existe y no tiene valores -- nunca entraba en el except, y el return final
    # reventaba con UnboundLocalError. Eso no fallaba una variante: tiraba la corrida entera
    # sin escribir el fichero, perdiendo todo lo leido hasta ahi.
    err = None
    for fm in ("RS_VARIANT_CONTENTS_255_RFC", "RS_VARIANT_CONTENTS_RFC"):
        try:
            r = conn.call(fm, REPORT=programa, VARIANT=variante, VALUTAB=[])
        except Exception as e:
            err = str(e)[:90]
            continue
        filas = []
        for t in ("VALUTAB", "VALUTAB_255", "SELTAB"):
            for x in (r.get(t) or []):
                if isinstance(x, dict) and any(str(v).strip() for v in x.values()):
                    filas.append({k: str(v).strip() for k, v in x.items()})
        if filas:
            return filas, fm, None
        err = err or f"{fm} respondio sin filas: la variante existe y no tiene valores"
    return None, None, err


def desde_cache():
    """RE-INTERPRETAR SIN VOLVER A P01.

    La lectura es cara y P01 es intermitente -- se cayo a media sesion. Pero la capa que hay
    que poder mejorar es la INTERPRETACION, no la lectura: cada vez que se afina una regla
    (que es una ruta, que es residuo, que mecanismo usa) no se debe pagar una lectura de SAP.
    Ademas, sin esto no se puede comparar interpretacion nueva contra interpretacion vieja
    sobre los MISMOS datos, que es la unica forma de saber si mejoro.
    """
    if not SALIDA.exists():
        return None
    d = json.loads(SALIDA.read_text(encoding="utf-8"))
    for r in d.get("variantes", []):
        crudo = (r.get("seleccion", []) + r.get("modo", []) + r.get("residuo_ultima_corrida", []))
        texto = " ".join(str(x.get("LOW", "")) + " " + str(x.get("HIGH", "")) for x in crudo)
        r["rutas_de_fichero"] = sorted({m.group(0) for m in RUTA.finditer(texto)})
        r["mecanismo_de_seleccion"] = mecanismo(r.get("seleccion", []))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-programas", type=int, default=40)
    ap.add_argument("--desde-cache", action="store_true",
                    help="re-interpreta lo ya leido sin tocar P01")
    a = ap.parse_args()

    if a.desde_cache:
        d = desde_cache()
        if not d:
            raise SystemExit("no hay lectura previa en " + str(SALIDA))
        registros = d["variantes"]
        rutas_por_prog = {}
        for r in registros:
            if r["rutas_de_fichero"]:
                rutas_por_prog.setdefault(r["programa"], set()).update(r["rutas_de_fichero"])
        firma = defaultdict(list)
        for r in registros:
            campos = tuple(sorted({s.get("SELNAME", "") for s in r.get("seleccion", [])
                                   if s.get("SELNAME")}))
            firma[(r["mecanismo_de_seleccion"], campos, bool(r["rutas_de_fichero"]))].append(
                f"{r['programa']}/{r['variante']}")
        d["formas_de_trabajar"] = sorted(
            [{"forma_de_trabajar": {"mecanismo": k[0], "campos": list(k[1]),
                                    "escribe_fichero": k[2]}, "miembros": v, "n": len(v)}
             for k, v in firma.items() if len(v) > 1], key=lambda g: -g["n"])[:40]
        d["rutas_por_programa"] = {k: sorted(v) for k, v in sorted(rutas_por_prog.items())}
        d["_reinterpretado_sin_sap"] = True
        SALIDA.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"re-interpretadas {len(registros)} variantes SIN tocar P01")
        print("RUTAS DE FICHERO (interfaces no declaradas):")
        for p, r in sorted(rutas_por_prog.items()):
            print(f"  {p[:30]:30s} {', '.join(sorted(r)[:3])[:110]}")
        print(f"{len(d['formas_de_trabajar'])} formas de trabajar")
        return 0

    con = gold()
    gold_util = gold_sirve(con)
    if not gold_util["sirve"]:
        print(f"  el Gold NO tiene contenido de variante: {gold_util['_por_que'][:90]}")
    dis, total_pares = disenadas(con)
    print(f"pares (programa, variante) en tbtcp: {total_pares:,}")
    print(f"programas con variante DISENADA: {len(dis)} "
          f"({sum(len(v) for _, v, _ in dis)} variantes)\n")

    # La conexion a P01 es el ULTIMO recurso, y que no exista no debe abortar la corrida: lo
    # que ya este en el Gold se mina igual. Antes, un fallo de VPN tiraba todo el proceso.
    conn = None
    try:
        from rfc_helpers import get_connection  # type: ignore
        conn = get_connection()
    except Exception as e:
        print(f"  P01 no disponible ({str(e)[:60]}) -- se mina SOLO lo que ya esta en el Gold\n")

    registros, fallos, saltadas = [], [], []
    for prog, variantes, pasos in dis[:a.max_programas]:
        # VARID dice cuales son de SAP (prefijo SAP&) y cuales de sistema: esas no son el proceso
        for v in variantes:
            if v.upper().startswith(("SAP&", "CUS&")):
                saltadas.append(f"{prog}/{v}")     # entregadas por SAP: no son el proceso
                continue
            # EL GOLD PRIMERO. Solo si no esta ahi se abre P01.
            filas, fm = del_gold(con, prog, v), "gold_db"
            if filas is None:
                if conn is None:
                    fallos.append({"programa": prog, "variante": v,
                                   "error": "no esta en el Gold y no hay conexion a P01"})
                    continue
                filas, fm, err = contenido(conn, prog, v)
                if filas is None:
                    fallos.append({"programa": prog, "variante": v, "error": err})
                    continue
            porclase = defaultdict(list)
            for f in filas:
                sel = f.get("SELNAME") or f.get("selname") or ""
                porclase[clase_de(sel, f.get("KIND"))].append(
                    {k: f.get(k) for k in ("SELNAME", "KIND", "SIGN", "OPTION", "LOW", "HIGH")
                     if f.get(k)})
            texto = " ".join(str(f.get("LOW", "")) + " " + str(f.get("HIGH", "")) for f in filas)
            rutas = sorted({m.group(0) for m in RUTA.finditer(texto)})
            registros.append({
                "programa": prog, "variante": v, "leido_con": fm,
                "mecanismo_de_seleccion": mecanismo(porclase["SELECCION"]),
                "parametros": {k: len(x) for k, x in porclase.items()},
                "rutas_de_fichero": rutas,
                "seleccion": porclase["SELECCION"][:30],
                "modo": porclase["MODO"][:20],
                "residuo_ultima_corrida": porclase["RESIDUO"][:10],
                "uso": uso_de(con, prog, v),
            })
        print(f"  {prog[:32]:32s} {len([r for r in registros if r['programa']==prog]):>3} leidas")

    con.close()

    # UNA CORRIDA PARCIAL NO MACHACA UNA COMPLETA. Con --max-programas 6 se sobrescribio un
    # corpus de 115 variantes con 8: el fichero quedo bien formado y decia mucho menos, que es
    # la peor forma de perder datos porque no parece un fallo. Se FUSIONA por (programa,
    # variante) y lo nuevo gana solo sobre su propia clave.
    nuevos_de_esta_corrida = list(registros)
    if SALIDA.exists():
        try:
            previo = json.loads(SALIDA.read_text(encoding="utf-8")).get("variantes", [])
        except Exception:
            previo = []
        nuevas = {(r["programa"], r["variante"]) for r in registros}
        conservadas = [r for r in previo if (r.get("programa"), r.get("variante")) not in nuevas]
        if conservadas:
            print(f"  conservadas {len(conservadas)} variantes de corridas anteriores")
        registros = registros + conservadas

    # AGRUPAR POR FORMA DE TRABAJAR: mismo mecanismo + mismos campos de seleccion + escribe o no
    # fichero. Dos programas distintos con la misma firma hacen el mismo tipo de trabajo.
    firma = defaultdict(list)
    for r in registros:
        campos = tuple(sorted({s.get("SELNAME", "") for s in r["seleccion"] if s.get("SELNAME")}))
        f = (r["mecanismo_de_seleccion"], campos, bool(r["rutas_de_fichero"]))
        firma[f].append(f"{r['programa']}/{r['variante']}")
    grupos = [{"forma_de_trabajar": {"mecanismo": k[0], "campos": list(k[1]),
                                     "escribe_fichero": k[2]},
               "miembros": v, "n": len(v)}
              for k, v in firma.items() if len(v) > 1]
    grupos.sort(key=lambda g: -g["n"])

    rutas_por_prog = {}
    for r in registros:
        if r["rutas_de_fichero"]:
            rutas_por_prog.setdefault(r["programa"], set()).update(r["rutas_de_fichero"])

    doc = {
        "_algoritmo": "A33_variant_content_mining",
        "_que_es": ("las variantes disenadas leidas, INTERPRETADAS por clase de parametro, "
                    "agrupadas por forma de trabajar y cruzadas con donde se usan"),
        "_las_tres_clases": {
            "SELECCION": "que objetos se procesan. ES el proceso",
            "MODO": "flags y config: CAMBIA el comportamiento. Copiarlo a ciegas voltea el alcance",
            "RESIDUO": ("fechas y handles: estado de la ULTIMA corrida, no diseno. Sirve para "
                        "fechar la ultima ejecucion sin mirar logs; no sirve para comparar")},
        "_el_mecanismo_cambia_dentro_del_mismo_programa": (
            "en SAPF100/UNES, UNES_DEPOSIT selecciona por 16 valores EQ sueltos y UNES_UNBA por "
            "rangos BT. Decir 'se anade por rangos' es falso la mitad de las veces: hay que leer "
            "la variante concreta"),
        "_las_rutas_son_interfaces_no_declaradas": (
            "un job que escribe en una carpeta compartida ES una interfaz y no figura en rfcdes "
            "ni en el inventario de servicios"),
        # UN SOLO DENOMINADOR, DECLARADO. `variantes_leidas` mide el corpus FUSIONADO de varias
        # corridas y `no_legibles` medía solo la ultima: dos denominadores en el mismo fichero.
        # Y 127 no es el universo -- es lo que queda tras dos umbrales sobre 29.190 pares.
        "cobertura": {
            "pares_programa_variante_en_tbtcp": total_pares,
            "disenadas_tras_los_umbrales": sum(len(v) for _p, v, _n in dis),
            "_los_umbrales": "<=20 variantes por programa y >=20 pasos de job",
            "leidas_en_esta_corrida": len(nuevos_de_esta_corrida),
            "en_el_corpus_acumulado": len(registros),
            "no_legibles_en_esta_corrida": len(fallos),
            "saltadas_por_ser_de_SAP": len(saltadas),
            "cuales_saltadas": saltadas[:10],
            "_la_suma_cierra": (len(nuevos_de_esta_corrida) + len(fallos) + len(saltadas)
                                == sum(len(v) for _p, v, _n in dis)),
            "_por_que_importa_que_cierre": ("una suma que no cierra esconde un tercer grupo sin "
                                            "nombrar. Aqui eran las variantes entregadas por "
                                            "SAP (prefijo SAP&/CUS&), que se saltan a proposito "
                                            "porque no son el proceso de esta casa"),
        },
        "el_gold_sirve": gold_util,
        "variantes_leidas": len(registros), "no_legibles": len(fallos),
        "rutas_por_programa": {k: sorted(v) for k, v in sorted(rutas_por_prog.items())},
        "formas_de_trabajar": grupos[:40],
        "variantes": registros,
        "fallos": fallos[:20],
    }
    SALIDA.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        from mining_bus import publicar
        # La evidencia dice de donde salio DE VERDAD, no una constante. Publicar
        # "RS_VARIANT_CONTENTS_255_RFC" en duro mientras el registro dice `leido_con: gold_db`
        # es una evidencia que el propio fichero puede desmentir.
        for prog, rutas in rutas_por_prog.items():
            fuentes_usadas = sorted({r.get("leido_con") for r in registros
                                     if r.get("programa") == prog and r.get("leido_con")})
            publicar("A33_variant_content_mining", "REALIDAD", prog,
                     f"su variante de job toca ficheros: {', '.join(sorted(rutas)[:4])}. "
                     "Es una interfaz que no figura en ningun inventario",
                     evidencia=f"contenido de variante leido con {'/'.join(fuentes_usadas)} "
                               f"sobre P01",
                     aspecto="rutas_de_fichero")
        for g in grupos[:12]:
            publicar("A33_variant_content_mining", "REALIDAD",
                     "FORMA:" + g["forma_de_trabajar"]["mecanismo"],
                     f"{g['n']} variantes trabajan igual: {', '.join(g['miembros'][:5])}",
                     evidencia="brain_v2/variant_content.json", aspecto="forma_de_trabajar")
    except Exception as e:
        print(f"  AVISO: no se pudo publicar en el bus ({type(e).__name__})")

    print(f"\n{len(registros)} variantes leidas · {len(fallos)} no legibles")
    print(f"\nMECANISMO DE SELECCION (cambia dentro del mismo programa):")
    for m, n in Counter(r["mecanismo_de_seleccion"] for r in registros).most_common():
        print(f"  {m:22s} {n}")
    if rutas_por_prog:
        print(f"\nRUTAS DE FICHERO -- interfaces que no estan en ningun inventario:")
        for p, r in sorted(rutas_por_prog.items()):
            print(f"  {p[:30]:30s} {', '.join(sorted(r)[:3])[:110]}")
    print(f"\n{len(grupos)} FORMAS DE TRABAJAR (>=2 variantes con la misma firma):")
    for g in grupos[:8]:
        f = g["forma_de_trabajar"]
        print(f"  [{f['mecanismo']:14s}] {'con fichero' if f['escribe_fichero'] else '           '}"
              f" {g['n']:>3}: {', '.join(g['miembros'][:4])[:80]}")
    print(f"\n-> {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
