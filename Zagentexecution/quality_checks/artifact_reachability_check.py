"""GATE: un artefacto que nadie enlaza es invisible, y eso es una perdida silenciosa.

POR QUE EXISTE, Y ES UN FALLO MEDIDO
    La sesion 103 produjo CINCO stores nuevos -- log_reality.json, comprehension_index.json,
    domain_composition.json, case_spine.json, rfc_caller_apps.json -- y al auditarlos solo UNO
    era alcanzable desde el indice de entrada. Los otros cuatro existian, tenian contenido
    correcto, se regeneraban en cada rebuild... y nadie podia llegar a ellos.

    Peor: nombres centrales de esos analisis -- EPAM-RFC, YTFM_WRTTP_GR, FMW2,
    RHRFPM_SET_CLOSED_INDICATOR, APQI -- no estaban ni en claims ni en brain_state.objects. El
    conocimiento existia y el grafo no lo tenia.

    Ya habia un gate para esto (unlanded_discoveries.py) pero vigila IDENTIFICADORES QUE EL
    CODIGO TOCA. Un store nuevo no es un identificador, asi que caia por el hueco entre los dos.

QUE COMPRUEBA
    Para cada artefacto JSON generado por un algoritmo registrado en algorithms.json:
      1. ALGUIEN LO LEE          -- otro script lo abre, o esta en el rebuild
      2. SE LLEGA DESDE LA ENTRADA -- BRAIN_INDEX.md o brain_state lo nombran
      3. SUS NOMBRES ESTAN EN EL GRAFO -- lo que `lands_in` promete, se cumple

    Un artefacto que falla (2) es el caso grave: se genera, es correcto, y es invisible.

LO QUE NO HACE
    No exige que todo este en el indice -- eso lo llenaria de ruido. Exige que este el
    artefacto o su CONCLUSION. Un dataset intermedio puede vivir referenciado por su algoritmo;
    lo que no puede es no tener a nadie que lo lea.

Uso:  python Zagentexecution/quality_checks/artifact_reachability_check.py [--json]
Salida: exit 0 limpio · exit 1 si hay artefactos invisibles
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRAIN = os.path.join(ROOT, "brain_v2")
INDEX = os.path.join(BRAIN, "BRAIN_INDEX.md")
ALGOS = os.path.join(BRAIN, "methods", "algorithms.json")
CLAIMS = os.path.join(BRAIN, "claims", "claims.json")

# Artefactos que son DATASET intermedio por diseno: se exige lector, no entrada en el indice.
INTERMEDIOS = {"executed_objects_text.json", "parsed_edges.json", "code_sections.json"}


def load(p, d=None):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return d if d is not None else {}


def main():
    algos = (load(ALGOS).get("algorithms") or {})
    idx = ""
    try:
        idx = open(INDEX, encoding="utf-8").read()
    except Exception:
        pass
    claims_txt = json.dumps(load(CLAIMS, []), ensure_ascii=False)

    # que artefactos promete cada algoritmo en lands_in
    prometidos = {}
    for aid, a in algos.items():
        li = str(a.get("lands_in") or "")
        for tok in li.replace(",", " ").replace("(", " ").replace(")", " ").split():
            if tok.endswith(".json") and "/" in tok:
                prometidos.setdefault(os.path.basename(tok), set()).add(aid)

    # todo el codigo del repo, para saber quien LEE que
    lectores = {}
    for base in ("brain_v2", "scripts", "process_mining", "Zagentexecution/quality_checks"):
        d = os.path.join(ROOT, *base.split("/"))
        for root, _, files in os.walk(d):
            if ".git" in root:
                continue
            for f in files:
                if not f.endswith((".py", ".md")):
                    continue
                try:
                    txt = open(os.path.join(root, f), encoding="utf-8",
                               errors="ignore").read()
                except Exception:
                    continue
                for art in prometidos:
                    if art in txt and f != art:
                        lectores.setdefault(art, set()).add(f)

    hallazgos = []
    for art, algs in sorted(prometidos.items()):
        # buscar en TODO brain_v2, no solo en su raiz: claims.json vive en claims/,
        # capability_model.json en capability_model/, incidents.json en incidents/.
        # Buscarlo solo en la raiz producia "AUSENTE" sobre ficheros que existen, y un gate
        # que grita en falso deja de leerse.
        # buscar en TODO el repo, no solo en brain_v2: job_classification.json vive en
        # Zagentexecution/sap_data_extraction/sqlite/, learned_rules.json en process_mining/,
        # los p2p_* en process_discovery/. Buscar solo en brain_v2 marcaba AUSENTE cinco
        # ficheros que existen, y un gate que grita en falso deja de leerse.
        p = None
        for base in ("brain_v2", "process_mining", "Zagentexecution", "scripts", "knowledge"):
            d = os.path.join(ROOT, base)
            if not os.path.isdir(d):
                continue
            for root, _, files in os.walk(d):
                if ".git" in root:
                    continue
                if art in files:
                    p = os.path.join(root, art)
                    break
            if p:
                break
        existe = p is not None
        leido = art in lectores and bool(lectores[art] - {art})
        en_indice = art in idx
        # su CONCLUSION puede estar en el indice aunque el fichero no se nombre
        alg_en_indice = any(a in idx for a in algs)
        intermedio = art in INTERMEDIOS

        if not existe:
            hallazgos.append({"artefacto": art, "gravedad": "AUSENTE", "algoritmos": sorted(algs),
                              "que_pasa": "el algoritmo promete este fichero y no existe"})
        elif not leido:
            hallazgos.append({"artefacto": art, "gravedad": "NADIE_LO_LEE",
                              "algoritmos": sorted(algs),
                              "que_pasa": "se genera y ningun otro script lo abre"})
        elif not (en_indice or alg_en_indice or intermedio):
            hallazgos.append({"artefacto": art, "gravedad": "INVISIBLE",
                              "algoritmos": sorted(algs),
                              "lectores": sorted(lectores.get(art, []))[:4],
                              "que_pasa": ("existe, es correcto y NO se llega a el desde "
                                           "BRAIN_INDEX: se genera para nadie")})

    # y los nombres que los algoritmos de log descubrieron: estan en claims?
    sin_claim = []
    for a in algos.values():
        for n in (a.get("_measured") or {}).get("names_discovered", []) or []:
            if n not in claims_txt:
                sin_claim.append(n)

    rep = {"_que_comprueba": ("que cada artefacto prometido en lands_in exista, lo lea alguien, "
                              "y se llegue a el desde el indice de entrada"),
           "_por_que": ("la sesion 103 produjo 5 stores y solo 1 era alcanzable. Un artefacto "
                        "correcto e invisible es una perdida silenciosa"),
           "artefactos_prometidos": len(prometidos),
           "hallazgos": hallazgos,
           "nombres_sin_claim": sin_claim[:40]}

    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"[alcanzabilidad] {len(prometidos)} artefactos prometidos por algoritmos")
        if not hallazgos:
            print("  OK - todos existen, alguien los lee, y se llega a ellos")
        for h in hallazgos:
            print(f"  [{h['gravedad']}] {h['artefacto']}")
            print(f"      {h['que_pasa']}")
            print(f"      algoritmos: {', '.join(h['algoritmos'])}")
        if sin_claim:
            print(f"  {len(sin_claim)} nombre(s) descubiertos sin claim que los promueva")
    return 1 if hallazgos else 0


if __name__ == "__main__":
    sys.exit(main())
