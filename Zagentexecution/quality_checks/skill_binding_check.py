"""GATE: un agente o un algoritmo que trabaja sobre un tema CON SKILL tiene que nombrarlo.

POR QUE EXISTE, y es el fallo mas caro y mas repetido de este proyecto
    Hay 48 skills con cientos de KB de metodo curado -- `sap_payment_bcm_agent` son 108 KB,
    `sap_transport_intelligence` 38 KB -- y NADIE los lee. Medido 2026-08-26:
      * 57 de 75 algoritmos no nombran ningun skill
      * 7 de 13 agentes tampoco, incluido `bcm-signatory-panel`, que hace trabajo de BCM
        teniendo delante el skill de 108 KB de BCM
      * `A40_config_transport_prerelease_check` se escribio y se ARREGLO dos veces sin abrir
        `sap_transport_intelligence`, que tiene una seccion entera sobre OBJFUNC (M borra la
        tabla ENTERA en destino antes de insertar) y otra que dice que E071K vacio TAMBIEN
        significa "rol", no solo "orden padre". Las dos cosas cambian el veredicto del check.

    El operador lo dijo asi: «siempre el mismo error de no mirar lo que hay». No es un
    descuido: es que nada lo MEDIA. Una promesa de mirar no es un control.

QUE ES CADA COSA -- la respuesta que este gate encarna
    SKILL      el metodo acumulado de un DOMINIO: que saber, que trampas tiene, que NO hacer.
               Es lo unico que ha sobrevivido a las sesiones. Es la fuente.
    AGENTE     QUIEN hace el trabajo y CUANDO. Debe ser delgado y DECLARAR que skills lee:
               un agente que lleva su metodo dentro compite con el skill y envejece solo.
    ALGORITMO  la medida MECANIZADA y repetible. Debe citar el skill que implementa, para que
               arreglarlo no signifique re-derivar su metodo.
    No son alternativas. Lo que faltaba era el VINCULO, y que alguien lo comprobara.

COMO CRUZA -- por NOMBRES DE TABLA SAP, no por palabras
    Cruzar por palabras sueltas ("variant", "job") engancha cualquier cosa: la primera version
    de esta medida decia que A34_account_behaviour_classes debia leer sap_variant_analysis
    porque en su ficha aparece la palabra "variante". Los nombres de tabla SAP (T030H, E071K,
    REGUH, APQI) son inequivocos: si un skill habla de E071K y un algoritmo opera sobre E071K,
    hablan de lo mismo. Se exige un solape MINIMO para no disparar por una tabla comun.

Uso:  python Zagentexecution/quality_checks/skill_binding_check.py [--json]
Salida: exit 0 limpio · exit 1 si alguien trabaja a ciegas sobre un tema que tiene skill
"""
QUALITY_CHECK = {
    "tier": "gate",
    "needs": "files",
    # `sobre` dice SOBRE QUE comprueba, que es un eje distinto de `tier` (que dice COMO corre).
    # Tres familias: datos_sap (el sistema de verdad), conocimiento (lo que hemos escrito) y
    # herramientas (nuestros propios instrumentos). Mezclarlas hace que un fallo NUESTRO se lea
    # como un fallo de SAP, y al reves.
    "sobre": "herramientas",  # datos_sap | conocimiento | herramientas
    "what": ("agentes y algoritmos que operan sobre un dominio con SKILL y no lo nombran: "
             "re-derivan metodo ya escrito"),
}
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILLS = os.path.join(ROOT, ".agents", "skills")
AGENTS = os.path.join(ROOT, ".claude", "agents")
ALGOS = os.path.join(ROOT, "brain_v2", "methods", "algorithms.json")

# Tablas demasiado comunes para probar nada: casi todo el SAP financiero las toca.
DEMASIADO_COMUNES = {
    # tablas que toca casi todo el SAP financiero: coincidir en ellas no prueba tema comun
    "T001", "TADIR", "USR02", "BKPF", "BSEG", "MANDT", "T000", "SPRAS",
    # nombres de SISTEMA: aparecen en todo lo que hable de este paisaje
    "P01", "D01", "V01", "TS2", "UNESCO", "UNES",
    # palabras genericas que el brain sintetizo como objeto y no distinguen nada.
    # Se listan una a una y con motivo: una exclusion sin motivo es un hueco disfrazado.
    "ALL", "OUTPUT", "DELETE", "POSTING", "CHANGE", "REPORT", "SELECT", "FILE", "TEXT",
    # codigos de MODULO: dicen el area, no el tema. Dos artefactos de FI no hablan de lo mismo.
    "HCM", "FI", "MM", "PS", "CO", "SD", "BASIS",
}
SOLAPE_MINIMO = 2          # una tabla en comun puede ser casualidad; dos ya es el mismo tema

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------------------
# Este gate existe porque «una promesa de mirar no es un control». Correrlo sin leer lo que el
# proyecto ya midio sobre gates seria exactamente el mismo fallo, un piso mas arriba.
#
# LA RUTA SE BUSCA SUBIENDO hasta el directorio que CONTIENE process_mining; no se cuenta con
# dirname(). Contarla mal es como quedo ciego el bloque de fsv_coverage_check: dos dirname
# desde quality_checks/ apuntan a Zagentexecution/process_mining, que NO existe, el import
# fallaba en silencio dentro de un `except Exception` y la puerta lo daba por bueno porque
# greppeaba la CADENA, no el efecto.
import os as _os, sys as _sys                                             # noqa: E401
_d = _os.path.dirname(_os.path.abspath(__file__))
while _d != _os.path.dirname(_d):
    if _os.path.isdir(_os.path.join(_d, "process_mining")):
        _sys.path.insert(0, _os.path.join(_d, "process_mining"))
        break
    _d = _os.path.dirname(_d)
try:
    # ImportError y no Exception: cubre "metodo.py no esta" sin tragarse un fallo REAL dentro
    # de metodo.py. Y AVISA: un gate que corre sin memoria tiene que decirlo, no callarlo.
    from metodo import lo_que_ya_aprendimos as _aprendido                 # noqa: E402
except ImportError as _e:
    print("  AVISO: corriendo SIN memoria de metodo (%s)" % _e)
    _aprendido = None

# Temas elegidos PROBANDOLOS (`python process_mining/metodo.py <tema>`), no por sonar bien.
# Devuelven 6 memorias y las cuatro que importan hablan de ESTE instrumento:
#   decoration  A18: «un check que reporta CANDIDATOS y no puede registrar "revisado,
#               excluido" repetira el mismo hallazgo para siempre y se dejara de leer;
#               entonces PARECE un control siendo decoracion, que es peor que no tenerlo».
#               Es el failure_mode declarado de A53 (GRITAR EN FALSO) medido por otro.
#   exclusion   misma memoria por su implicacion: da a cada check una lista de exclusion CON
#               MOTIVO y prueba las DOS cosas -- que calla sobre lo revisado y que sigue
#               disparando en un caso nuevo. La segunda prueba es la que demuestra que no
#               apagaste el check. Aqui la lista es DEMASIADO_COMUNES, ya con motivo escrito.
#   puerta      A37: «una puerta que comprueba que la llamada esta ESCRITA no comprueba que
#               LLEGUE» -- cinco mineros tenian el import y recibian None. Este bloque es
#               justo esa clase de codigo, y por eso se mide el efecto, no la cadena.
#   patron      A34 + A4: clasificar por PATRON sobre texto libre de SAP produce cifras
#               plausibles, seguras y falsas; un patron ingenioso captura de mas (^AB[AZ] se
#               traga ABAP4_CALL_TRANSACTION). Es por lo que aqui se cruza por nombres SAP
#               validados contra el brain y el Gold, nunca por forma.
TEMAS_APRENDIDOS = ("decoration", "exclusion", "puerta", "patron")


def _nombres_sap_conocidos():
    """La lista de nombres SAP REALES — del brain y del Gold, no de un patron inventado.

    ⛔ La primera version de esto reconocia "lo que parece una tabla" por forma: mayusculas,
    algun digito o guion bajo. Enganchaba CRITICAL, NEVER, FROM, SELECT, MARTIN, RISK -- y con
    esa lista el gate dijo «43 ciegos», mezclando emparejamientos buenos (bcm-signatory-panel
    con sap_payment_bcm_agent por HRP1000/HRP1001/BNK_APP) con basura (brain-steward con el
    mismo skill por 'ABAP, FILE, NEVER, ONLY'). Publicar eso habria sido, otra vez, un detector
    ruidoso presentado como medida.

    Lo que hay que hacer es lo mismo que este gate predica: USAR LO QUE YA EXISTE.
    brain_state.objects tiene ~4.400 nombres SAP curados y el Gold tiene sus tablas. Un nombre
    que no este en ninguno de los dos NO se cuenta como tabla.
    """
    conocidos = set()
    try:
        st = json.load(open(os.path.join(ROOT, "brain_v2", "brain_state.json"),
                            encoding="utf-8"))
        conocidos |= {str(k).upper() for k in (st.get("objects") or {})}
    except Exception:
        pass
    try:
        import sqlite3
        g = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                         "p01_gold_master_data.db")
        if os.path.exists(g):
            con = sqlite3.connect("file:%s?mode=ro" % g, uri=True, timeout=60)
            conocidos |= {str(r[0]).upper().replace("P01_", "").replace("D01_", "")
                          for r in con.execute(
                              "SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
            con.close()
    except Exception:
        pass
    return conocidos - DEMASIADO_COMUNES


NOMBRES_SAP = None


def tablas(texto):
    """Nombres SAP REALES citados en el texto. Precision antes que cobertura."""
    global NOMBRES_SAP
    if NOMBRES_SAP is None:
        NOMBRES_SAP = _nombres_sap_conocidos()
    out = set()
    for m in re.findall(r"\b([A-Z][A-Z0-9_/]{2,29})\b", texto or ""):
        if m in NOMBRES_SAP:
            out.add(m)
    return out


def main():
    # ANTES de medir nada. Un aviso que llega despues no sirve: para entonces el veredicto ya
    # esta escrito. Con --json va a STDERR, no se calla: este gate publica JSON en stdout y
    # ensuciarlo rompe a quien lo parsee -- pero silenciar la memoria para no ensuciar seria
    # cambiar una salida limpia por un minero ciego, que es el defecto que este check persigue.
    if _aprendido:
        _hacia = (lambda s: print(s, file=sys.stderr)) if "--json" in sys.argv else None
        _aprendido(*TEMAS_APRENDIDOS).avisar(salida=_hacia, minero="A53_skill_binding_gate")
        print("", file=sys.stderr if "--json" in sys.argv else sys.stdout)
    if not os.path.isdir(SKILLS):
        print("no hay directorio de skills")
        return 0
    perfil = {}
    for d in sorted(os.listdir(SKILLS)):
        p = os.path.join(SKILLS, d, "SKILL.md")
        if os.path.isfile(p):
            t = open(p, encoding="utf-8", errors="ignore").read()
            perfil[d] = {"tablas": tablas(t), "bytes": len(t)}

    h, ciegos = [], []

    def revisar(quien, texto, blob_tablas, fuente):
        if any(s in texto for s in perfil):
            return                       # ya nombra algun skill: basta
        # CANDIDATOS, NO VEREDICTO. Nombrar UN skill -- el de mayor solape -- es una respuesta
        # segura y a veces falsa: a A40 le señalaba sap_master_data_sync cuando el suyo es
        # sap_transport_intelligence, solo porque compartia mas nombres. El solape dice "aqui
        # se habla de lo mismo"; CUAL de ellos es el bueno lo decide quien lo lea.
        cands = []
        for s, meta in perfil.items():
            comunes = sorted(blob_tablas & meta["tablas"])
            if len(comunes) >= SOLAPE_MINIMO:
                cands.append({"skill": s, "bytes": meta["bytes"], "comun": comunes[:6],
                              "n": len(comunes)})
        if cands:
            cands.sort(key=lambda x: (-x["n"], -x["bytes"]))
            ciegos.append({"quien": quien, "fuente": fuente,
                           "candidatos": cands[:3],
                           "_como_se_elige": ("el solape dice que se habla del mismo tema, no "
                                              "cual es el skill bueno: leelos y elige")})

    for f in sorted(os.listdir(AGENTS)) if os.path.isdir(AGENTS) else []:
        if not f.endswith(".md"):
            continue
        t = open(os.path.join(AGENTS, f), encoding="utf-8", errors="ignore").read()
        revisar(f[:-3], t, tablas(t), "agente")

    try:
        A = json.load(open(ALGOS, encoding="utf-8")).get("algorithms") or {}
    except Exception:
        A = {}
    for k, v in A.items():
        blob = json.dumps(v, ensure_ascii=False)
        revisar(k, blob, tablas(blob), "algoritmo")

    if ciegos:
        h.append({"gravedad": "TRABAJA_SIN_LEER_SU_SKILL", "cuantos": len(ciegos),
                  "casos": ciegos,
                  "que_pasa": ("operan sobre las mismas tablas que un SKILL ya documenta y no "
                               "lo nombran: re-derivan metodo ya escrito, y pierden sus "
                               "trampas. Medido: A40 se arreglo DOS VECES sin abrir el skill "
                               "de transportes, que tiene una seccion sobre OBJFUNC=M -- borra "
                               "la tabla ENTERA en destino -- y otra que dice que E071K vacio "
                               "tambien significa 'rol'"),
                  "como_se_arregla": ("nombra el skill en el agente (.claude/agents/<x>.md) o "
                                      "en la ficha del algoritmo (algorithms.json), y LEELO "
                                      "antes de tocar su tema")})

    rep = {"_que_es": "quien trabaja sobre un tema que ya tiene skill sin nombrarlo",
           "skills": len(perfil), "agentes_y_algoritmos_ciegos": len(ciegos),
           "hallazgos": h}
    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2, default=str))
        return 1 if h else 0

    print(f"[skills] {len(perfil)} skill(s) con metodo curado")
    if not h:
        print("  OK - quien trabaja sobre un tema con skill lo nombra")
        return 0
    for x in h:
        print(f"  [{x['gravedad']}] {x['cuantos']}")
        print(f"      {x['que_pasa']}")
        for c in x["casos"][:20]:
            print(f"      {c['fuente']:10s} {c['quien']}")
            for k in c["candidatos"]:
                print(f"          candidato: {k['skill']:32s} ({k['bytes']:>7,} B) "
                      f"{k['n']} en comun: {', '.join(k['comun'])}")
        if len(x["casos"]) > 20:
            print(f"      ... y {len(x['casos']) - 20} mas")
        print(f"      ARREGLO: {x['como_se_arregla']}")
    return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
