# -*- coding: utf-8 -*-
"""opportunity_watch.py — el registro de oportunidades y riesgos NOTA su propia ausencia.

EL PROBLEMA QUE RESUELVE
    En s109 se construyo el registro (`PMO_OPORTUNIDADES.md` + companion) generado del bus de
    mineros. Quedo bonito y quedo MUERTO: nada regeneraba el registro, nada volvia a correr los
    mineros, y ningun hook mencionaba mineria. Un registro que nadie refresca no envejece a la
    vista -- envejece EN SILENCIO, afirmando cifras de un dia concreto como si fueran de hoy.

    Es exactamente la regla #179: lo programado debe NOTAR SU PROPIA AUSENCIA. Detectar no es
    actuar, y generar una vez no es mantener.

QUE HACE, EN DOS MODOS
    Por defecto (SIN SAP, vale siempre, y es la PUERTA):
      A. ¿esta el registro mas viejo que el bus?          -> el bus cambio y nadie regenero
      B. ¿cuanto lleva sin correr cada minero?            -> por hallazgo, `visto_ultima`
      C. ¿hay mineros cableados que NUNCA han publicado?  -> capacidad instalada y sin usar
      D. ¿hay hallazgos de un minero que ya no existe?    -> huerfanos que nadie puede refrescar
      E. ¿cumple cada hallazgo el contrato?               -> tamano, evidencia, limite, denominador
    Sale con 1 si algo esta rancio o roto. Eso es lo que lo convierte en un mecanismo y no en
    un informe.

    Con `--correr` (LEE SAP): vuelve a correr los mineros que publican al bus, mide el DELTA
    -- que hallazgo es NUEVO, cual DESAPARECIO, cual cambio de tamano -- y regenera el registro.
    Un minero que no pudo correr se REPORTA; nunca se salta en silencio.

POR QUE EL DELTA IMPORTA MAS QUE LA LISTA
    Cada corrida de un minero REEMPLAZA lo suyo en el bus. Asi que lo que desaparece del
    registro es lo que DEJO DE ENCONTRARSE -- puede ser que se arreglara, o que el minero se
    rompiera y ya no mire. Sin delta, las dos cosas se ven igual: un hueco.

Solo LECTURA sobre SAP. La lista de mineros se DERIVA (quien importa `_hallazgos`), no se
mantiene a mano: cablear un minero nuevo lo mete aqui solo.
"""

QUALITY_CHECK = {
    "tier": "repo",
    "sobre": "process_mining/mining_findings.json + .agents/intelligence/PMO_OPORTUNIDADES.md",
    "needs": "nada (modo puerta) · rfc_p01 (modo --correr)",
    "what": "el registro de oportunidades y riesgos nota su propia ausencia: rancidez, mineros "
            "mudos, hallazgos huerfanos, contrato incumplido; y con --correr, el delta",
    "args": "[--correr] [--dias N]",
}

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BUS = os.path.join(REPO, "process_mining", "mining_findings.json")
REG = os.path.join(REPO, ".agents", "intelligence", "PMO_OPORTUNIDADES.md")
COMP = os.path.join(REPO, "companions", "oportunidades_y_desafios.html")
ESTADO = os.path.join(REPO, "process_mining", "opportunity_watch_state.json")
CLASES = ("OPORTUNIDAD", "RIESGO", "DESAFIO", "DATO")
OBLIGADOS = ("tamano", "evidencia", "limite", "denominador")


def hoy():
    return datetime.date.today()


def dias(fecha):
    """Dias desde una fecha ISO. None si no se puede leer -- y None NO es cero."""
    if not fecha:
        return None
    try:
        return (hoy() - datetime.date.fromisoformat(str(fecha)[:10])).days
    except ValueError:
        return None


def mineros_cableados():
    """DERIVADO, no mantenido a mano: quien importa el contrato `_hallazgos`.

    Mantener la lista a mano garantiza que el minero numero 8 no entre nunca. Se deriva del
    import porque ese es el acto que convierte un script en un minero que publica."""
    out = {}
    for d in ("Zagentexecution/quality_checks", "process_mining"):
        base = os.path.join(REPO, d)
        if not os.path.isdir(base):
            continue
        for f in sorted(os.listdir(base)):
            if not f.endswith(".py") or f.startswith("_"):
                continue
            p = os.path.join(base, f)
            try:
                with open(p, encoding="utf-8") as fh:
                    s = fh.read()
            except (OSError, UnicodeDecodeError):
                continue
            if re.search(r"from\s+_hallazgos\s+import|import\s+_hallazgos", s):
                out[f[:-3]] = os.path.relpath(p, REPO).replace("\\", "/")
    return out


def cargar_bus():
    with open(BUS, encoding="utf-8") as fh:
        d = json.load(fh)
    return [h for h in d.get("hallazgos", []) if h.get("clase") in CLASES]


def clave(h):
    """Identidad de un hallazgo entre corridas: minero + su frase. El `id` se renumera."""
    return "%s :: %s" % (h.get("minero"), (h.get("que") or "")[:120])


def auditar(a):
    hs = cargar_bus()
    cab = mineros_cableados()
    publican = set(h.get("minero") for h in hs)
    fallos, avisos = [], []

    print("=" * 96)
    print("EL REGISTRO DE OPORTUNIDADES Y RIESGOS, ¿SIGUE VIVO?")
    print("=" * 96)
    print("  %d hallazgos vivos · %d mineros cableados · %d de ellos han publicado alguna vez"
          % (len(hs), len(cab), len(publican & set(cab))))

    print("\n  A · ¿el registro refleja el bus?")
    if not os.path.exists(REG):
        fallos.append("el registro NO EXISTE: %s" % os.path.relpath(REG, REPO))
        print("      FALTA el registro")
    else:
        tb, tr = os.path.getmtime(BUS), os.path.getmtime(REG)
        if tb > tr + 1:
            fallos.append("el bus cambio DESPUES del registro: hay hallazgos publicados que "
                          "nadie ha volcado. Corre `python scripts/build_oportunidades.py`")
            print("      RANCIO — el bus es %d s mas nuevo que el registro" % int(tb - tr))
        else:
            print("      al dia")
        if os.path.exists(COMP) and os.path.getmtime(COMP) + 1 < tb:
            avisos.append("el companion va por detras del bus")

    print("\n  B · ¿cuanto lleva cada minero sin correr?  (umbral: %d dias)" % a.dias)
    ult = {}
    for h in hs:
        n = dias(h.get("visto_ultima") or h.get("visto_primero"))
        m = h.get("minero")
        if n is not None and (m not in ult or n < ult[m]):
            ult[m] = n
    for m in sorted(x for x in publican if x):
        n = ult.get(m)
        if n is None:
            avisos.append("%s: sus hallazgos no llevan fecha, no se puede medir rancidez" % m)
            print("      %-42s sin fecha" % m)
        elif n > a.dias:
            fallos.append("%s lleva %d dias sin correr (umbral %d)" % (m, n, a.dias))
            print("      %-42s %3d dias  <<< RANCIO" % (m, n))
        else:
            print("      %-42s %3d dias" % (m, n))

    mudos = sorted(set(cab) - publican)
    print("\n  C · mineros cableados que NUNCA han publicado: %d" % len(mudos))
    for m in mudos:
        print("      %-42s %s" % (m, cab[m]))
        avisos.append("%s esta cableado y nunca publico: o no encuentra nada, o no se corre" % m)

    huer = sorted(m for m in publican if m and m not in cab and "manual" not in m)
    print("\n  D · hallazgos de un minero que YA NO EXISTE en disco: %d" % len(huer))
    for m in huer:
        print("      %-42s <<< HUERFANO" % m)
        fallos.append("hay hallazgos vivos de '%s' y ese minero no esta en disco: nadie puede "
                      "refrescarlos ni retirarlos" % m)

    print("\n  E · ¿cumple cada hallazgo el contrato?")
    rotos = []
    for h in hs:
        falta = [k for k in OBLIGADOS if not str(h.get(k) or "").strip()]
        if falta:
            rotos.append((clave(h)[:74], falta))
    if not rotos:
        print("      los %d llevan tamano, evidencia, limite y denominador" % len(hs))
    for k, f in rotos:
        print("      %-74s falta: %s" % (k, ", ".join(f)))
        fallos.append("hallazgo sin %s: %s" % ("/".join(f), k))

    print("\n" + "-" * 96)
    for x in avisos:
        print("  aviso  · %s" % x)
    if fallos:
        print("\nFAIL — %d cosa(s) que hacen que este registro mienta por omision:" % len(fallos))
        for x in fallos:
            print("   - %s" % x)
        print("\n  Un registro que nadie refresca no envejece a la vista: envejece en silencio.")
        return 1
    print("\nOK — el registro esta vivo: refleja el bus, ningun minero rancio, contrato completo.")
    return 0


def correr(a):
    """Vuelve a correr los mineros y mide el DELTA. LEE SAP."""
    antes = dict((clave(h), h) for h in cargar_bus())
    cab = mineros_cableados()
    ok, roto = [], []
    for m, ruta in sorted(cab.items()):
        print("\n--- %s ---" % m)
        try:
            r = subprocess.run([sys.executable, os.path.join(REPO, ruta)],
                               cwd=REPO, capture_output=True, text=True, timeout=1800)
            rc, cola = r.returncode, (r.stderr or r.stdout or "")
        except subprocess.TimeoutExpired:
            rc, cola = -9, "timeout a los 1800 s"
        (ok if rc == 0 else roto).append(m)
        if rc:
            print("    NO CORRIO (exit %s): %s"
                  % (rc, " | ".join(cola.strip().splitlines()[-2:])))
        else:
            print("    ok")

    despues = dict((clave(h), h) for h in cargar_bus())
    nuevos = [k for k in despues if k not in antes]
    idos = [k for k in antes if k not in despues]
    camb = [k for k in despues if k in antes
            and str(despues[k].get("tamano") or "") != str(antes[k].get("tamano") or "")]

    print("\n" + "=" * 96)
    print("DELTA DE ESTA CORRIDA")
    print("=" * 96)
    print("  mineros: %d corrieron · %d NO pudieron correr%s"
          % (len(ok), len(roto), (" -> " + ", ".join(roto)) if roto else ""))
    if roto:
        print("  (lo que un minero roto NO encuentra se ve igual que lo que ya no existe:")
        print("   por eso se reportan, nunca se saltan en silencio)")
    for etiqueta, items in (("NUEVO", nuevos), ("DESAPARECIO", idos), ("CAMBIO DE TAMANO", camb)):
        print("\n  %s: %d" % (etiqueta, len(items)))
        for k in items[:12]:
            h = despues.get(k) or antes.get(k)
            print("     [%s] %s" % (h.get("clase"), k[:88]))
            if etiqueta == "CAMBIO DE TAMANO":
                print("         antes : %s" % str(antes[k].get("tamano") or "")[:82])
                print("         ahora : %s" % str(despues[k].get("tamano") or "")[:82])

    subprocess.run([sys.executable, os.path.join(REPO, "scripts", "build_oportunidades.py")],
                   cwd=REPO, capture_output=True, text=True)
    print("\n  registro regenerado")

    with open(ESTADO, "w", encoding="utf-8") as fh:
        json.dump({"ultima_corrida": hoy().isoformat(),
                   "mineros_ok": ok, "mineros_rotos": roto,
                   "nuevos": nuevos, "desaparecidos": idos, "cambiaron": camb,
                   "_por_que": ("el DELTA es el producto, no la lista: cada corrida REEMPLAZA lo "
                                "suyo en el bus, asi que lo que desaparece es lo que dejo de "
                                "encontrarse -- y eso puede ser un arreglo o un minero roto.")},
                  fh, ensure_ascii=False, indent=1)
    print("  estado -> %s" % os.path.relpath(ESTADO, REPO))
    return 1 if roto else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--correr", action="store_true",
                    help="vuelve a correr los mineros (LEE SAP) y mide el delta")
    ap.add_argument("--dias", type=int, default=30,
                    help="a partir de cuantos dias un minero se considera rancio")
    a = ap.parse_args()
    return correr(a) if a.correr else auditar(a)


if __name__ == "__main__":
    sys.exit(main())
