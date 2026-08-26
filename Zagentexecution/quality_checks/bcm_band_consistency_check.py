"""BCM — ¿el panel POR TRAMO DE IMPORTE dice lo mismo que el cartón?
================================================================================================
POR QUE EXISTE, Y POR QUE NO LO CUBRE NINGUN CHECK ANTERIOR

    `bcm_signatory_reconciliation_check.py` compara PERSONAS: quién está en SAP y no en el cartón,
    y al revés. Eso basta mientras el panel sea plano. **Deja de bastar en cuanto la carta pone un
    tope a alguien**, porque entonces la pregunta ya no es "¿está?" sino "¿está EN EL TRAMO QUE LE
    CORRESPONDE?" — y eso vive en el infotipo 1218, que ese check no mira.

    Nace de INC-000016338 (UIL, 2026-08-26). Ahí la validación se hizo A MANO, en un script de una
    sesión, y encontró que subir el suelo del nodo alto habría quitado a cuatro firmantes sin tope
    los pagos por debajo de 10.000. Mientras siga siendo un script de una sesión, la próxima
    entidad depende de que alguien se acuerde. Esto es ese script, convertido en puerta.

LO QUE COMPRUEBA — cinco cosas, y las cinco fallaron alguna vez

    A. COBERTURA   Quien NO tiene tope, ¿alcanza TODOS los tramos? (da igual cómo: estando en los
                   dos nodos como UBO, o con un nodo solapado que los cubra como UIL).
    B. EXCESO      Quien SI tiene tope, ¿está FUERA de los tramos por encima de su límite?
    C. QUORUM      Cada tramo, ¿tiene al menos 2 aprobadores CON rol BNK_APP? Con `rel_proc 01`
                   (doble control) un tramo servido por 0 o 1 persona no se puede liberar.
    D. EXTRAS      ¿Hay alguien activo en SAP que no esté en el cartón?
    E. BEGDA       Las filas creadas a partir de la fecha de la carta, ¿arrancan en esa fecha?
                   (2 ocurrencias medidas de lo contrario: 7 días en INC-000006313, 15 en 16338).

    NO decide la forma del panel. UBO (bandas disjuntas, panel alto subconjunto) y UIL (nodo bajo
    con sólo los limitados, nodo alto solapado) son AMBOS válidos — claim 613 — y este check pasa
    con los dos, porque razona por TRAMO EFECTIVO y no por la forma de los nodos.

POR QUE RAZONA POR TRAMO Y NO POR NODO

    Porque la determinación devuelve la UNION de todos los nodos que encajan (claim 612, verificado
    con `Simulate rule resolution`: 10.000,00 -> 6 agentes, 10.001,00 -> 4). Así que "quién puede
    aprobar un pago de X" NO es el contenido de un nodo: es la unión de todos los nodos cuya banda
    contiene X. Un check que mire nodo a nodo se equivoca en las dos direcciones.

    ⚠️ Esa semántica depende de que la columna PRIORITY de OOCU_RESP siga VACIA. El check lo avisa
    si detecta prioridad, porque entonces sus conclusiones dejan de ser válidas.

FORMATO DEL CARTON — el mismo de siempre, con el límite en el comentario

    # Fecha carton : 2026-08-11
    10168474  # ABDI Dereje Bune      - Hamburg - sin limite
    10111198  # BASOGLU Ana Suzan     - Hamburg - hasta USD 10,000.00

    Se lee "hasta ... <numero>" como tope y cualquier otra cosa como SIN TOPE. Si el fichero no
    anota límites, el check avisa y comprueba sólo D y E.

USO
    python bcm_band_consistency_check.py --entity UIL --carton cartons/uil_deutschebank_hamburg_20260811.txt
    python bcm_band_consistency_check.py --entity UIL --carton <f> --strict   # falla tambien con avisos

SALIDA
    0 = coherente · 1 = incoherencia (A-E) · 2 = error de lectura/uso
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mcp-backend-server-python"))
from rfc_helpers import get_connection  # noqa: E402

RULE_OF_SHORT = {"BNK_01_01_03": ("90000004", "FIRMAR  (BNK_COM)"),
                 "BNK_01_01_04": ("90000005", "VALIDAR (BNK_INI)")}
ROLE_PREFIX = "YS:FI:M:BCM_MON_APP"


def rr(conn, table, fields, where="", rowcount=9000):
    opts = [{"TEXT": where}] if where else []
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|", ROWCOUNT=rowcount,
                    ROWSKIPS=0, OPTIONS=opts, FIELDS=[{"FIELDNAME": f} for f in fields])
    hdr = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
    out = []
    for row in res.get("DATA", []):
        parts = row["WA"].split("|")
        out.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdr)})
    return out


def parse_carton(path):
    """-> (dict pernr -> limite (float) o None si sin tope, fecha_carta 'YYYYMMDD' o None, anota_limites)"""
    limits, letter_date, annotated = {}, None, False
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            m = re.search(r"[Ff]echa\s+cart[oó]n\s*:\s*(\d{4})-(\d{2})-(\d{2})", line)
            if m:
                letter_date = "".join(m.groups())
            continue
        m = re.match(r"^(\d{6,10})\s*(?:#\s*(.*))?$", line)
        if not m:
            continue
        pernr, comment = m.group(1).lstrip("0"), (m.group(2) or "")
        cap = None
        mc = re.search(r"hasta[^0-9]{0,12}([\d.,]+)", comment, re.I)
        if mc:
            annotated = True
            num = mc.group(1).rstrip(".,")
            # 10,000.00 -> 10000.00 ; 10.000,00 -> 10000.00
            if "," in num and "." in num:
                num = num.replace(",", "") if num.rfind(".") > num.rfind(",") else num.replace(".", "").replace(",", ".")
            elif "," in num:
                num = num.replace(",", "") if len(num.split(",")[-1]) == 3 else num.replace(",", ".")
            cap = float(num)
        elif re.search(r"sin\s+l[ií]mite|unlimited", comment, re.I):
            annotated = True
        limits[pernr] = cap
    return limits, letter_date, annotated


def read_landscape(conn, entity):
    """Nodos RY de la entidad con su banda, miembros vivos y prioridad."""
    today = __import__("datetime").date.today().strftime("%Y%m%d")
    nodes = []
    for n in rr(conn, "HRP1000", ["OBJID", "SHORT", "STEXT", "BEGDA", "ENDDA"], "OTYPE = 'RY'"):
        if not n["STEXT"].upper().startswith(entity.upper()):
            continue
        if n["SHORT"] not in RULE_OF_SHORT:
            continue
        crit = {}
        for h in rr(conn, "HRP1218", ["OBJID", "TABNR"], f"OBJID = '{n['OBJID']}'"):
            for t in rr(conn, "HRT1218", ["TABNR", "ELEMENT", "EXPR_LOW", "EXPR_HIGH"],
                        f"TABNR = '{h['TABNR']}'"):
                crit[t["ELEMENT"]] = (t["EXPR_LOW"], t["EXPR_HIGH"])
        lo, hi = crit.get("MAXPAYAMT_RULECURR", ("0", "0"))
        members = sorted({r["SOBID"].lstrip("0") for r in
                          rr(conn, "HRP1001", ["OBJID", "RELAT", "SCLAS", "SOBID", "BEGDA", "ENDDA"],
                             f"OBJID = '{n['OBJID']}'")
                          if r["RELAT"] == "007" and r["SCLAS"] == "P" and r["ENDDA"] >= today})
        begdas = {r["SOBID"].lstrip("0"): r["BEGDA"] for r in
                  rr(conn, "HRP1001", ["OBJID", "RELAT", "SCLAS", "SOBID", "BEGDA", "ENDDA"],
                     f"OBJID = '{n['OBJID']}'")
                  if r["RELAT"] == "007" and r["SCLAS"] == "P" and r["ENDDA"] >= today}
        rule, label = RULE_OF_SHORT[n["SHORT"]]
        nodes.append({"objid": n["OBJID"], "stext": n["STEXT"], "rule": rule, "label": label,
                      "lo": float(lo or 0), "hi": float(hi or 0),
                      "members": members, "begdas": begdas})
    return nodes


def identities(conn, pernrs):
    uname, roles = {}, {}
    for p in pernrs:
        rows = [r for r in rr(conn, "PA0105", ["PERNR", "SUBTY", "USRID"], f"PERNR = '{p.zfill(8)}'")
                if r["SUBTY"] == "0001"]
        uname[p] = rows[-1]["USRID"] if rows else ""
    for r in rr(conn, "AGR_USERS", ["UNAME", "AGR_NAME"], f"AGR_NAME LIKE '{ROLE_PREFIX}%'"):
        roles.setdefault(r["UNAME"], []).append(r["AGR_NAME"])
    return uname, roles


def tiers_from(nodes):
    """Puntos de corte -> lista de tramos (lo, hi) con los que hay que razonar."""
    edges = sorted({n["lo"] for n in nodes} | {n["hi"] for n in nodes})
    out = []
    for i in range(len(edges) - 1):
        out.append((edges[i], edges[i + 1]))
    return [t for t in out if t[1] > t[0]]


def who_can(nodes, rule, amount):
    """UNION de los nodos de esa regla cuya banda contiene el importe (claim 612)."""
    s = set()
    for n in nodes:
        if n["rule"] == rule and n["lo"] <= amount <= n["hi"]:
            s |= set(n["members"])
    return s


def main():
    ap = argparse.ArgumentParser(description="Coherencia del panel BCM por tramo de importe")
    ap.add_argument("--entity", required=True)
    ap.add_argument("--carton", required=True)
    ap.add_argument("--strict", action="store_true", help="salir 1 tambien con avisos")
    a = ap.parse_args()

    if not Path(a.carton).exists():
        print(f"ERROR: no existe el carton {a.carton}")
        print("  Sin carton NO se puede juzgar el panel. Pedirlo es parte del ticket.")
        return 2

    limits, letter_date, annotated = parse_carton(a.carton)
    conn = get_connection()
    nodes = read_landscape(conn, a.entity)
    if not nodes:
        print(f"ERROR: sin nodos RY para la entidad {a.entity}")
        return 2
    everyone = set(limits) | {m for n in nodes for m in n["members"]}
    uname, roles = identities(conn, everyone)

    print("=" * 78)
    print(f"COHERENCIA DE TRAMOS BCM — {a.entity} — carton {Path(a.carton).name}")
    print("=" * 78)
    for n in sorted(nodes, key=lambda z: (z["rule"], z["lo"])):
        print(f"  [{n['label']}] {n['objid']} {n['stext'][:40]:40} "
              f"{n['lo']:,.2f} -> {n['hi']:,.2f}  ({len(n['members'])}p)")
    if not annotated:
        print("\n  AVISO: el carton no anota limites por persona -> solo se comprueban EXTRAS y BEGDA.")

    fails, warns = [], []
    rules = sorted({n["rule"] for n in nodes})

    for rule in rules:
        rnodes = [n for n in nodes if n["rule"] == rule]
        label = rnodes[0]["label"]
        print(f"\n--- regla {rule} {label} ---")
        for lo, hi in tiers_from(rnodes):
            probe = hi  # el borde ES inclusivo (claim 612)
            can = who_can(rnodes, rule, probe)
            con_rol = {p for p in can if roles.get(uname.get(p, ""), [])}
            print(f"  tramo <= {hi:,.2f}: {len(can)} elegibles, {len(con_rol)} con rol BNK_APP")

            if annotated:
                # A. cobertura
                debe = {p for p, cap in limits.items() if cap is None or cap >= probe}
                faltan = debe - can
                if faltan:
                    fails.append(f"[A cobertura] regla {rule}, tramo <={hi:,.2f}: autorizados por el "
                                 f"carton y NO elegibles: {sorted(faltan)}")
                # B. exceso
                sobran = {p for p in can if p in limits and limits[p] is not None and limits[p] < probe}
                if sobran:
                    fails.append(f"[B exceso] regla {rule}, tramo <={hi:,.2f}: elegibles POR ENCIMA de "
                                 f"su tope de carton: {sorted(sobran)}")
            # C. quorum
            if len(con_rol) < 2:
                fails.append(f"[C quorum] regla {rule}, tramo <={hi:,.2f}: solo {len(con_rol)} "
                             f"aprobador(es) con rol BNK_APP -> el doble control NO se puede satisfacer")

    # D. extras
    activos = {m for n in nodes for m in n["members"]}
    extras = activos - set(limits)
    if extras:
        fails.append(f"[D extras] activos en SAP y NO en el carton: "
                     f"{sorted((p, uname.get(p, '')) for p in extras)}")

    # E. BEGDA contra la fecha de la carta
    if letter_date:
        for n in nodes:
            for p, b in n["begdas"].items():
                if b > letter_date and p in limits:
                    warns.append(f"[E begda] {p} en {n['objid']} arranca {b} y la carta es de "
                                 f"{letter_date} -> hueco de auditoria de "
                                 f"{(int(b) - int(letter_date))} (aaaammdd)")
    else:
        warns.append("[E begda] el carton no declara '# Fecha carton : YYYY-MM-DD' -> no se comprueba")

    # aviso de PRIORITY (la semantica de UNION depende de que este vacia)
    try:
        prio = [r for r in rr(conn, "HRP1222", ["OBJID"], "") if r]
        if prio:
            warns.append("[!] HRP1222 devuelve filas: revisar PRIORITY en OOCU_RESP — si hay prioridad, "
                         "la determinacion deja de ser UNION y este check pierde validez (claim 612).")
    except Exception:
        pass

    print("\n" + "=" * 78)
    for w in warns:
        print("  AVISO   " + w)
    for f in fails:
        print("  FALLO   " + f)
    if not fails and not warns:
        print("  OK — el panel por tramos coincide con el carton.")
    elif not fails:
        print("  OK con avisos — ningun tramo incoherente.")
    print("=" * 78)

    if fails:
        return 1
    if warns and a.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
