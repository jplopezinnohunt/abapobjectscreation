"""
EL CORREO ES LA OCASION; EL DOCUMENTO ES LA ESPECIFICACION.

QUE ES ESTO Y POR QUE ESTA FUERA DE UN AGENTE
    El metodo vivia dentro del prompt de `authority-doc-reader`: util para todos, usable por uno.
    JP lo nombro -- *"quizas hay herramientas de mineria encapsuladas dentro del agente como en
    un dominio; algo dentro de eso es mas generico para uso de todos"*. Asi que se parte en dos
    por donde de verdad se corta:

        LEER el PDF y estructurarlo   -> necesita CRITERIO      -> se queda en el agente
        COMPARAR lo autorizado con    -> es DETERMINISTA         -> sale aqui, para cualquiera
        lo pedido, y aplicar los gates

    El agente no pierde nada: sigue siendo quien decide. Gana que su comparacion la pueda
    ejecutar cualquier otro -- master-data-sync, bcm-signatory-panel, o un humano con un JSON.

LA REGLA, MEDIDA DOS VECES EN INCIDENTES DISTINTOS
    INC-000011781  el correo decia "add Renata RITTER"      las cartas decian ADD Renata Y DELETE Martin
    INC-000016262  el correo pedia revaluar dos cuentas     el formulario AM 3-11 firmado decia NO para una
    En los dos casos, ejecutar la nota del correo habria sido incorrecto.

QUE COMPRUEBA -- cinco cosas, y las cinco fallan distinto
    1. DELTA        que pide el correo y NO autoriza ningun documento   -> no ejecutable
    2. OMISION      que autorizan los documentos y el correo NO pide    -> el caso Martin
    3. SUSTITUCION  ¿algun documento dice "replaces all previous"?      -> el panel es sustitutivo,
                    y entonces todo extra en el sistema es sobre-autorizacion, no deriva
    4. COMPLETITUD  ¿hay documento para CADA objeto afectado?           -> si falta uno, HALT:
                    sin el no se puede llamar deriva a nada
    5. ALINEACION   ¿dicen lo MISMO todos los documentos?               -> si no, el cambio puede
                    no ser representable y hay que devolverlo

NO LEE SAP NI PDFs. Consume el JSON que produce el lector y devuelve el veredicto.

Uso:
    python authority_delta.py --entrada <fichero.json>
    python authority_delta.py --demo            # con el caso INC-000011781
"""
import argparse
import io
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SUSTITUTIVA = ("replaces all previous", "remplace toute", "annule et remplace",
               "sustituye a", "cancels and replaces")


def _norm(x):
    """Un mismo sujeto se escribe de tres formas en tres sitios. Se compara por su nucleo."""
    if isinstance(x, dict):
        x = x.get("id") or x.get("pernr") or x.get("cuenta") or x.get("nombre") or ""
    return str(x).strip().upper().lstrip("0") or str(x).strip().upper()


def analizar(d):
    docs = d.get("documentos") or []
    pedido = d.get("pedido_del_correo") or {}
    r = {"veredicto": "OK", "halt": [], "avisos": [], "delta": {}, "gates": {}}

    if not docs:
        r["veredicto"] = "HALT"
        r["halt"].append("NO HAY DOCUMENTO DE AUTORIDAD. El correo no autoriza nada por si "
                         "mismo: sin documento no hay especificacion que ejecutar.")
        return r

    aut_add, aut_del = set(), set()
    for x in docs:
        acc = x.get("acciones") or {}
        aut_add |= {_norm(v) for v in (acc.get("add") or [])}
        aut_del |= {_norm(v) for v in (acc.get("delete") or [])}
    ped = pedido.get("acciones") or {}
    ped_add = {_norm(v) for v in (ped.get("add") or [])}
    ped_del = {_norm(v) for v in (ped.get("delete") or [])}

    # 1 y 2 -- las dos direcciones del delta, y la segunda es la que muerde
    sin_autorizar = sorted((ped_add - aut_add) | (ped_del - aut_del))
    no_pedido = sorted((aut_add - ped_add) | (aut_del - ped_del))
    r["delta"] = {"pide_el_correo_y_nadie_autoriza": sin_autorizar,
                  "autorizado_y_el_correo_NO_pide": no_pedido}
    if sin_autorizar:
        r["veredicto"] = "HALT"
        r["halt"].append("EL CORREO PIDE ALGO QUE NINGUN DOCUMENTO AUTORIZA: %s. No es "
                         "ejecutable." % ", ".join(sin_autorizar))
    if no_pedido:
        r["veredicto"] = "REVISAR" if r["veredicto"] == "OK" else r["veredicto"]
        r["avisos"].append("LOS DOCUMENTOS AUTORIZAN ALGO QUE EL CORREO NO MENCIONA: %s. Es el "
                           "caso Martin (INC-000011781): la nota decia solo 'add' y las cartas "
                           "tambien daban de baja. El documento manda."
                           % ", ".join(no_pedido))

    # 3 -- sustitutiva cambia la naturaleza de todo extra encontrado despues
    subs = [x.get("ref") for x in docs
            if any(c in json.dumps(x.get("clausulas") or [], ensure_ascii=False).lower()
                   for c in SUSTITUTIVA)]
    r["gates"]["sustitutiva"] = bool(subs)
    if subs:
        r["avisos"].append("CLAUSULA SUSTITUTIVA en %s: el panel del documento REEMPLAZA al "
                           "anterior, asi que todo lo que sobre en el sistema es "
                           "SOBRE-AUTORIZACION, no deriva menor." % ", ".join(map(str, subs)))

    # 4 -- completitud: sin documento para cada objeto no se puede concluir deriva
    objs = {_norm(o) for x in docs for o in (x.get("objetos") or [])}
    esperados = {_norm(o) for o in (d.get("objetos_esperados") or [])}
    faltan = sorted(esperados - objs) if esperados else []
    r["gates"]["completitud"] = not faltan
    if faltan:
        r["veredicto"] = "HALT"
        r["halt"].append("INCOMPLETO: falta documento para %s. Sin el, NO se puede llamar deriva "
                         "a ningun extra del sistema." % ", ".join(faltan))
    elif not esperados:
        r["avisos"].append("No se declararon `objetos_esperados`: el gate de completitud no se "
                           "pudo evaluar. No es un OK, es un DESCONOCIDO.")

    # 5 -- alineacion entre documentos
    paneles = [tuple(sorted(_norm(p) for p in (x.get("panel") or []))) for x in docs
               if x.get("panel")]
    r["gates"]["alineacion"] = len(set(paneles)) <= 1
    if len(set(paneles)) > 1:
        r["veredicto"] = "HALT"
        r["halt"].append("LOS DOCUMENTOS NO DICEN LO MISMO: %d paneles distintos. Si el sistema "
                         "modela una sola lista por entidad, esto NO es representable y hay que "
                         "devolverlo a quien lo autoriza." % len(set(paneles)))

    ilegible = d.get("no_legible") or []
    if ilegible:
        r["avisos"].append("HAY PARTES NO LEGIBLES (%s): lo no leido es DESCONOCIDO, nunca "
                           "'no dice nada'." % ", ".join(map(str, ilegible))[:120])
    return r


DEMO = {
 "documentos": [
  {"tipo": "carta", "ref": "FIN.8/MOD/10.0000003618", "objetos": ["CIT01"],
   "acciones": {"add": ["10021811"], "delete": ["10108464"]},
   "panel": ["10021811", "10005016"], "clausulas": []},
  {"tipo": "carta", "ref": "FIN.8/MOD/10.0000003617", "objetos": ["BRA01"],
   "acciones": {"add": ["10021811"], "delete": ["10108464"]},
   "panel": ["10021811", "10005016"], "clausulas": []}],
 "pedido_del_correo": {"de": "Ingrid Wettie", "acciones": {"add": ["10021811"]}},
 "objetos_esperados": ["CIT01", "BRA01"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        d = DEMO
    elif a.entrada:
        d = json.load(io.open(a.entrada, encoding="utf-8"))
    else:
        ap.error("da --entrada <json> o --demo")

    r = analizar(d)
    print("VEREDICTO: %s\n" % r["veredicto"])
    for h in r["halt"]:
        print("  HALT   %s\n" % h)
    for w in r["avisos"]:
        print("  AVISO  %s\n" % w)
    print("  gates: %s" % json.dumps(r["gates"], ensure_ascii=False))
    print("  delta: %s" % json.dumps(r["delta"], ensure_ascii=False))
    return 0 if r["veredicto"] == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
