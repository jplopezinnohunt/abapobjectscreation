# -*- coding: utf-8 -*-
"""ANTES DE LIBERAR UN TRANSPORTE DE CUSTOMIZING: diferenciar la TABLA ENTERA.

POR QUE EXISTE
    2026-08-19. Configurando Egipto en YTFI_PPC_STRUC se borro sin querer el separador
    '/' de la fila ID/USTRD/O/01 -- INDONESIA -- y esa clave quedo DENTRO del transporte
    de Egipto. Liberado asi, habria cambiado el fichero de Bank Indonesia de
    '/PURP/<cod>/<XBLNR>' a 'PURP/<cod>/<XBLNR>' sobre 921 lineas con codigo de proposito.

    Ninguna revision centrada en "esta Egipto bien configurado?" lo habria visto: la
    configuracion de Egipto era correcta. Lo vio el diff de TODA la tabla entre los dos
    sistemas, que devolvio exactamente una deriva ajena a Egipto.

    Mantener una entidad en SM30 puede capturar la clave de una entidad VECINA. El diff
    que lo ve no es el de las claves que querias tocar.

MATIZ QUE HAY QUE SABER PARA LEER LA SALIDA
    Un transporte de tabla guarda la CLAVE y exporta el VALOR al LIBERAR, no al capturarlo.
    Por eso restaurar el valor neutraliza el dano aunque la clave siga dentro -- pero deja
    a la entidad vecina ACOPLADA al transporte hasta la liberacion: cualquier edicion suya
    antes de liberar viaja sola y en silencio.

QUE CLASIFICA
    [VIAJA]      clave en el transporte y valor distinto entre origen y destino
                 -> es el cambio que querias. Verifica que TODO esto es intencionado.
    [INTRUSA]    clave en el transporte cuya entidad no es la mayoritaria del transporte
                 -> es la clase de defecto de Indonesia. Hace fallar el check.
    [NO-OP]      clave en el transporte con el mismo valor a los dos lados
                 -> no cambia nada al importar; candidata a quitar de la lista de objetos.
    [DERIVA]     clave FUERA del transporte con valor distinto
                 -> divergencia entre sistemas que este transporte NO va a corregir.

USO
    python Zagentexecution/quality_checks/config_transport_prerelease_check.py D01K9B0FXF
    python ... <TRKORR> --src D01 --dst P01
    python ... <TRKORR> --entity-field LAND1     (por defecto: el 1er campo clave tras MANDT)

Regla: feedback_diff_the_whole_table_before_releasing_a_config_transport (CRITICAL).
Claim 526.
"""
# --- self-declaration, read by quality_checks/run_all.py -------------------
# Un script sin declarar sale como UNCLASSIFIED y hace fallar al runner: un registro
# central es una lista que alguien se olvida de actualizar.
# tier=analysis y no gate a proposito: esto se corre ANTES DE LIBERAR un transporte
# concreto, no en cada ciclo -- necesita un TRKORR y no tiene sentido sin el.
QUALITY_CHECK = {
    "tier": "analysis",   # gate | live | analysis | quarantined
    "needs": "rfc_p01",   # gold_db | rfc_p01 | files
    "what": "transporte de customizing: diff de la TABLA ENTERA origen vs destino antes de liberar",
    "args": "<TRKORR> [--src D01 --dst P01]",
}
# --------------------------------------------------------------------------
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

sys.path.insert(0, os.path.join(HERE, "..", "mcp-backend-server-python"))

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `brain_v2/methods/algorithm_memory.json` guarda, por cada memoria,
# su `implication`: que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y
# no leerlas es aprender y no aprender a la vez -- y peor, el error queda MECANIZADO.
# Para ESTE check hay una memoria que le apunta directamente: las claves de customizing viven
# en E071K de la TAREA, no de la orden padre -- la orden de Egipto D01K9B0FXE sale exit 0 con
# analisis vacio mientras su hija D01K9B0FXF sale exit 1 con la clave intrusa de Indonesia.
sys.path.insert(0, os.path.join(REPO, "process_mining"))
try:
    from metodo import lo_que_ya_aprendimos as _aprendido  # noqa: E402
except Exception:
    _aprendido = None


def read_table(conn, table, fields, where=""):
    """RFC_READ_TABLE sin strip: los blancos son datos, no ruido."""
    kw = dict(QUERY_TABLE=table, DELIMITER="|",
              FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=0)
    if where:
        kw["OPTIONS"] = [{"TEXT": where}]
    r = conn.call("RFC_READ_TABLE", **kw)
    return [dict(zip(fields, d["WA"].split("|"))) for d in r["DATA"]]


def ddic(conn, table):
    """Campos de la tabla en orden, y cuales son clave. Con su longitud, que hace
    falta para trocear el TABKEY de E071K -- que es un campo de ancho fijo."""
    rows = read_table(conn, "DD03L",
                      ["FIELDNAME", "POSITION", "KEYFLAG", "LENG", "INTLEN", "DATATYPE"],
                      "TABNAME = '%s'" % table)
    out = []
    for r in sorted(rows, key=lambda x: int(x["POSITION"].strip())):
        fn = r["FIELDNAME"].strip()
        if fn.startswith("."):            # .INCLUDE y similares
            continue
        # LENG = longitud en CARACTERES. INTLEN es la interna Unicode (2 bytes por
        # caracter) y trocea el TABKEY mal: con INTLEN, MANDT(3) se come 6 posiciones
        # y todas las claves salen desplazadas -- el check daba OK siendo incorrecto.
        out.append({"name": fn, "key": r["KEYFLAG"].strip() == "X",
                    "len": int(r["LENG"].strip() or 0),
                    "type": r["DATATYPE"].strip()})
    return out


def split_tabkey(tabkey, fields):
    """E071K.TABKEY = MANDT + campos clave concatenados a ancho fijo."""
    vals, pos = [], 0
    for f in fields:
        if not f["key"]:
            continue
        vals.append(tabkey[pos:pos + f["len"]])
        pos += f["len"]
    return tuple(v.rstrip() for v in vals)


def key_of(row, fields):
    return tuple(row[f["name"]].rstrip() for f in fields if f["key"])


def value_of(row, fields):
    return "|".join(row[f["name"]].rstrip() for f in fields if not f["key"])


def main(argv):
    if _aprendido:
        _aprendido("transporte", "e071k", "customizing", "tarea").avisar()
        print()
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    trkorr = argv[0].upper()
    src = argv[argv.index("--src") + 1].upper() if "--src" in argv else "D01"
    dst = argv[argv.index("--dst") + 1].upper() if "--dst" in argv else "P01"
    entity_field = argv[argv.index("--entity-field") + 1].upper() \
        if "--entity-field" in argv else None

    from rfc_helpers import get_connection

    print("=" * 78)
    print("TRANSPORTE %s   %s -> %s" % (trkorr, src, dst))
    print("=" * 78)

    c = get_connection(src)
    try:
        hdr = read_table(c, "E070",
                         ["TRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER", "AS4DATE"],
                         "TRKORR = '%s'" % trkorr)
        if not hdr:
            print("No existe el transporte %s en %s." % (trkorr, src))
            return 2
        h = {k: v.strip() for k, v in hdr[0].items()}
        txt = read_table(c, "E07T", ["TRKORR", "AS4TEXT"], "TRKORR = '%s'" % trkorr)
        print("  %s  funcion=%s  estado=%s  %s  %s" %
              (h["TRKORR"], h["TRFUNCTION"], h["TRSTATUS"], h["AS4USER"], h["AS4DATE"]))
        if txt:
            print("  %s" % txt[0]["AS4TEXT"].strip())
        if h["TRSTATUS"] == "R":
            print("  AVISO: ya esta LIBERADO. Este check es para ANTES de liberar.")
        print()

        # ARREGLADO 2026-08-26 (A40). LA UNIDAD DE CAMBIO ES LA ORDEN, Y ERA LA QUE DECIA OK.
        #
        # Las claves de customizing viven en E071K de la TAREA, no de la orden padre. Antes,
        # con la orden se imprimia «E071K vacio / puede ser una tarea padre» y se devolvia 0
        # -- mientras su hija D01K9B0FXF devolvia 1 con la clave INTRUSA de Indonesia
        # '350/ID/USTRD/O/01'. Mismo dia, misma herramienta, veredictos opuestos, y el objeto
        # que un operador teclea al liberar era justo el que aprobaba. El propio codigo nombraba
        # el remedio (E070.STRKORR) en el mensaje y no lo aplicaba.
        #
        # Ahora se resuelven las hijas y se analiza la UNION. Y si no hay hijas y no hay claves,
        # se sale 2 (NO ANALIZABLE), nunca 0: un exit 0 sobre algo que no se pudo mirar se lee
        # como aprobado, que es la forma mas cara de fallar en una puerta de liberacion.
        analizados = [trkorr]
        keys = read_table(c, "E071K", ["TRKORR", "OBJNAME", "TABKEY"],
                          "TRKORR = '%s'" % trkorr)
        if not keys:
            hijas = [x["TRKORR"].strip() for x in
                     read_table(c, "E070", ["TRKORR", "STRKORR"],
                                "STRKORR = '%s'" % trkorr)]
            if not hijas:
                print("  El transporte no lleva claves de tabla (E071K vacio) y NO tiene tareas")
                print("  hijas (E070.STRKORR). NO ANALIZABLE -- no se puede decir que este")
                print("  limpio, solo que no se ha podido mirar.")
                return 2
            print("  Es una ORDEN: sus claves viven en las %d tarea(s) hija(s). Se analiza la"
                  % len(hijas))
            print("  UNION, que es lo que de verdad se libera: %s" % ", ".join(sorted(hijas)))
            for t in sorted(hijas):
                keys.extend(read_table(c, "E071K", ["TRKORR", "OBJNAME", "TABKEY"],
                                       "TRKORR = '%s'" % t))
            analizados = sorted(hijas)
            if not keys:
                print("  Ninguna hija lleva claves de tabla: NO ANALIZABLE.")
                return 2
            print()
        by_tab = collections.defaultdict(list)
        for k in keys:
            by_tab[k["OBJNAME"].strip()].append(k["TABKEY"])
        print("  %d clave(s) en %d tabla(s): %s" %
              (len(keys), len(by_tab), ", ".join(sorted(by_tab))))
        print()

        meta = {t: ddic(c, t) for t in by_tab}
        src_rows = {t: read_table(c, t, [f["name"] for f in meta[t]]) for t in by_tab}
    finally:
        c.close()

    c = get_connection(dst)
    try:
        dst_rows = {t: read_table(c, t, [f["name"] for f in meta[t]]) for t in by_tab}
    finally:
        c.close()

    intrusas, viaja, noop, deriva = [], [], [], []
    no_vacias = []          # tablas donde la prueba INTRUSA NO pudo ejecutarse

    for tab in sorted(by_tab):
        fields = meta[tab]
        keyf = [f["name"] for f in fields if f["key"]]
        in_tr = {split_tabkey(tk, fields) for tk in by_tab[tab]}
        a = {key_of(r, fields): value_of(r, fields) for r in src_rows[tab]}
        b = {key_of(r, fields): value_of(r, fields) for r in dst_rows[tab]}

        # LA ENTIDAD DEL TRANSPORTE — ARREGLADO 2026-08-26 (A40).
        #
        # Antes se fijaba UN eje a ciegas: el 1er campo clave tras MANDT. Para T030H eso es
        # KTOPL, y en D01 solo existe UNES -- asi que `len(ents) > 1` era SIEMPRE falso y la
        # prueba INTRUSA no podia dispararse NUNCA. El discriminador real (HKONT, la cuenta) no
        # se miraba. Resultado: un «0 INTRUSA» que significaba NO COMPROBADO y se leia como
        # LIMPIO. Un doc de incidente llego a publicar «alcance limpio, sin claves ajenas»
        # apoyado en ese cero.
        #
        # Ahora se recorren los campos clave EN ORDEN y gana EL PRIMERO QUE DISCRIMINA.
        #
        # ⛔ EL ORDEN IMPORTA Y NO ES UN DETALLE. La primera version de este arreglo elegia el
        # campo con MAS VALORES DISTINTOS, y sobre YTFI_PPC_STRUC eligio CODE_ORD -- un numero
        # de secuencia, 01..06 -- como si fuera una entidad. Resultado medido: marco OCHO claves
        # de EGIPTO como intrusas (EG/USTRD/O/02..06, EG/USTRD/P/02..04, que son el contenido
        # propio del transporte) y DEJO PASAR la de Indonesia, 350/ID/USTRD/O/01, clasificada
        # NO-OP. Rompio el unico caso que funcionaba y produjo 8 falsos positivos. Cambiar una
        # heuristica por otra heuristica no es arreglar: es mover el error de sitio.
        #
        # En una clave de SAP los campos DELANTEROS son la entidad y los traseros el detalle.
        # Por eso: el primero que separe, no el que mas separe. Asi el pais gana en
        # YTFI_PPC_STRUC (Indonesia se caza) y HKONT gana en T030H, donde KTOPL no separa nada
        # porque en D01 solo existe UNES. Si NINGUNO discrimina, se DICE en vez de dar un cero.
        candidatos = [i for i, f in enumerate(keyf) if f.upper() != "MANDT"]
        if entity_field and entity_field in keyf:
            candidatos = [keyf.index(entity_field)]
        idx, ents, main_ents = None, collections.Counter(), set()
        for i in candidatos:
            cnt = collections.Counter(k[i] for k in in_tr if len(k) > i)
            if len(cnt) < 2:
                continue                      # ese campo no separa nada en este transporte
            top = max(cnt.values())
            mayoria = {e for e, n in cnt.items() if n == top}
            if len(mayoria) != 1:
                continue                      # empate: no hay "la entidad que se mantenia"
            idx, ents, main_ents = i, cnt, mayoria
            break                             # EL PRIMERO que discrimina, no el que mas
        eje_discrimina = idx is not None
        if not eje_discrimina:
            idx = candidatos[0] if candidatos else 0

        print("-" * 78)
        print("TABLA %s   clave=(%s)   %s:%d filas  %s:%d filas   claves en transporte:%d"
              % (tab, ",".join(keyf), src, len(a), dst, len(b), len(in_tr)))
        # Autocomprobacion del troceo del TABKEY. Si ninguna clave del transporte
        # existe en la tabla, no es que el transporte sea raro: es que las estamos
        # troceando mal. Un check que informa OK estando roto es peor que no tenerlo.
        casan = len([k for k in in_tr if k in a or k in b])
        if in_tr and casan == 0:
            print("   ERROR: ninguna de las %d claves del transporte existe en %s ni en %s."
                  % (len(in_tr), src, dst))
            print("   Eso es un fallo de troceo del TABKEY, no un hallazgo. Abortando.")
            return 2
        if in_tr and casan < len(in_tr):
            print("   AVISO: %d de %d claves del transporte no existen en ningun sistema"
                  % (len(in_tr) - casan, len(in_tr)))
        if eje_discrimina:
            print("   eje de entidad = %s (el campo clave que DISCRIMINA): %s"
                  % (keyf[idx] if len(keyf) > idx else "?", dict(ents)))
        else:
            # NO SE CALLA. Un cero que significa "no comprobado" impreso junto a ceros que
            # significan "no ocurre" es exactamente como se fabrica una conclusion falsa.
            no_vacias.append(tab)
            print("   ⛔ NINGUN campo clave discrimina en esta tabla: todas las claves del")
            print("      transporte comparten el mismo valor en cada campo, o hay empate.")
            print("      LA PRUEBA INTRUSA NO SE EJECUTA AQUI. Un 0 en el resumen significa")
            print("      NO COMPROBADO, no 'limpio'. Fuerza un eje con --entity-field <CAMPO>.")

        for k in sorted(in_tr, key=str):
            va, vb = a.get(k), b.get(k)
            ent = k[idx] if len(k) > idx else ""
            tag = "NO-OP " if va == vb else "VIAJA "
            extra = ""
            if eje_discrimina and ent not in main_ents:
                tag = "INTRUSA"
                extra = "   <-- entidad ajena a este transporte"
                intrusas.append((tab, k, va, vb))
            elif va == vb:
                noop.append((tab, k))
            else:
                viaja.append((tab, k))
            print("   [%s] %-34s %s%s" % (tag, "/".join(k), "" if va == vb else "", extra))
            if va != vb:
                print("        %s = %r" % (src, va))
                print("        %s = %r" % (dst, vb))

        fuera = [k for k in sorted(set(a) | set(b), key=str)
                 if k not in in_tr and a.get(k) != b.get(k)]
        if fuera:
            print("   -- deriva FUERA del transporte (no viaja) --")
            for k in fuera:
                deriva.append((tab, k))
                print("   [DERIVA] %-32s %s=%r  %s=%r"
                      % ("/".join(k), src, a.get(k), dst, b.get(k)))

    print()
    print("=" * 78)
    print("  ANALIZADO: %s" % ", ".join(analizados))
    print("  VIAJA   %3d   el cambio que querias -- verifica que TODO es intencionado"
          % len(viaja))
    print("  NO-OP   %3d   misma valor a los dos lados; candidatas a quitar del transporte"
          % len(noop))
    print("  DERIVA  %3d   divergencia que este transporte NO corrige" % len(deriva))
    print("  INTRUSA %3d   clave de una entidad ajena DENTRO del transporte%s"
          % (len(intrusas),
             "" if not no_vacias else "   <-- PARCIAL, ver abajo"))
    if no_vacias:
        # EL CERO QUE SIGNIFICA "NO COMPROBADO" VA JUNTO AL CERO, NO EN OTRO SITIO.
        print()
        print("  ⛔ ALCANCE NO VERIFICADO en %d tabla(s): %s"
              % (len(no_vacias), ", ".join(no_vacias)))
        print("     Ahi ningun campo clave discrimina, asi que la prueba INTRUSA no se ejecuto.")
        print("     NO leas el 'INTRUSA 0' de arriba como 'sin claves ajenas': significa que en")
        print("     esas tablas no se ha podido mirar. Fuerza un eje con --entity-field <CAMPO>.")
    if intrusas:
        print()
        print("  FALLA. Una clave ajena dentro del transporte es la clase de defecto que")
        print("  casi cambia Indonesia el 2026-08-19. Revisa cada una:")
        for tab, k, va, vb in intrusas:
            print("     %s %s   %s=%r  %s=%r" % (tab, "/".join(k), src, va, dst, vb))
        print("  Si el valor coincide a los dos lados la importacion es inocua, pero la")
        print("  entidad queda ACOPLADA al transporte hasta liberarlo: quitala por SE10.")
        return 1
    print()
    print("  OK -- ninguna clave ajena. Sigue siendo tuya la lectura de [VIAJA] y [DERIVA].")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
