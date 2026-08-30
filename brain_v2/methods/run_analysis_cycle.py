"""run_analysis_cycle.py — actually RUN the on-demand algorithms (s097).

"On demand" is a euphemism for "never runs" when nobody demands it. The status check found
twelve algorithms in that state: real code, bound to real tools, producing nothing because
no trigger fires them.

That is a structural hole, not a detail. An algorithm that does not run is documentation.

This runs the analysis algorithms — the ones that need no SAP connection, only the golden
data we already hold — **in dependency order**, because the nesting is real: the boundary
must be discovered before satellites can be derived from it, and objects must resolve to
components before anything can be attributed to a domain.

**The order IS the knowledge.** A trigger must never name a script to run — that is a
decision taken on demand, and on-demand decisions are exactly what stops being taken. A
trigger reports EVIDENCE; this file holds what to run and in which sequence, so adding an
algorithm means placing it in the chain, not remembering to call it. Write-path attribution
sits at L2 for a concrete reason: when it classifies a class as INTERFACE it names the
calling function modules, and those functions are what the satellite derivation groups on
— so attribution has to precede boundary discovery, not follow it.

Deliberately NOT included: anything requiring RFC. Extraction depends on a VPN and on
someone deciding it is time; those stay explicit. This runs what can always run.

    python brain_v2/methods/run_analysis_cycle.py            # the full cycle
    python brain_v2/methods/run_analysis_cycle.py --quick    # skip the slow log scans
    python brain_v2/methods/run_analysis_cycle.py --con-rfc  # + los pasos que NECESITAN P01

Los pasos de RFC_REQUERIDO estan FUERA por defecto, y eso es la promesa de arriba, no una
omision: sin --con-rfc el ciclo corre sin VPN y sin depender de que alguien decida que toca
extraer. Cuando se saltan se DICEN uno a uno -- un paso que no corrio por falta de conexion
y uno que no corrio por ser lento son cosas distintas, y mezclarlos hace que nadie sepa que
le falta al resultado.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

# A child's output can carry characters the Windows console encoding cannot print, and an
# UnicodeEncodeError here would abort the whole cycle over a cosmetic detail.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def say(text):
    """print() that cannot kill the run."""
    try:
        print(text)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "ascii"
        print(text.encode(enc, "replace").decode(enc, "replace"))

REPO = Path(__file__).resolve().parents[2]
STATE = Path(__file__).parent / "cycle_state.json"

# (script, label, needs_full_log_scan) — ORDER IS THE DEPENDENCY ORDER.
CYCLE = [
    ("process_mining/executed_objects_domain_map.py",
     "L1 classify every executed object", True),
    ("process_mining/attach_object_text.py",
     "L1 attach readable text — makes the frontier reviewable", False),
    # A19 va DESPUES de clasificar y ANTES de todo lo que cuente: separa objetos de
    # instancias generadas, y sin eso cualquier conteo trata ~3.500 nombres generados como
    # si fueran objetos. A20 va detras porque consume las dos cosas.
    ("process_mining/log_reality_filter.py",
     "L1 objeto vs instancia generada vs actor — clasificar antes de contar", True),
    ("brain_v2/comprehension_index.py",
     "L3 indice de comprension: esta CERRADA la superficie de ejecucion?", True),
    ("brain_v2/parse_abap_edges.py",
     "L0 code edges from extracted source", False),
    ("process_mining/derive_object_roles.py",
     "L1 what each object is FOR", False),
    ("process_mining/attribute_changes_to_programs.py",
     "L2 what WRITES each object class, and through which channel", True),
    # LA CADENA DE DESCUBRIMIENTO, delegada entera (2026-08-25).
    #
    # Este ciclo existia y corria media docena de scripts de process_mining, pero NO la columna
    # vertebral de casos ni la familia B -- DFG, variantes, cuellos, conformidad, OCEL2. Por eso
    # llevaban meses sin ejecutarse: el mecanismo estaba, la cadena no. Once algoritmos
    # registrados sin llamador, medido con graph_landing_check.py.
    #
    # Se delega en vez de copiar los pasos aqui porque el ORDEN tiene dependencias reales -- A21
    # es la puerta de B1-B5, y sin columna vertebral un DFG dibuja un proceso que no existe --
    # y ese orden debe estar definido en UN sitio. `--desde 2` salta la fase de realidad, que
    # este ciclo ya corre arriba, y la de ingesta, que es un grifo periodico aparte.
    # --desde 1, NO 2. Con `--desde 2` la fase 1 entera se saltaba, y ese salto dejaba a A3
    # (rfc_process_classifier) y A31 (bdc_channel_mining) SIN NINGUN LLAMADOR: este ciclo corre
    # A19 y A4 mas arriba, pero no esos dos. A31 es el metodo que encontro ALLOS y se mecanizo
    # precisamente para que fuera repetible y comparable con la corrida del mes pasado -- y con
    # la delegacion anterior no volvia a correr nunca. Que A19 y A4 se repitan cuesta minutos;
    # que A31 no corra cuesta la capacidad entera.
    ("process_mining/run_discovery_pipeline.py --desde 1",
     "L2-L3 cadena de descubrimiento: realidad -> columna vertebral -> familia B -> cruce",
     True),
    ("brain_v2/build_interface_inventory.py",
     "L2 every interface as a RECORD — prose is not queryable knowledge", False),
    ("process_mining/interface_boundary.py",
     "L2 discover the boundary: live / dead / undeclared", True),
    ("process_mining/derive_satellites.py",
     "L3 derive satellites -> origin -> flow", True),
    ("process_mining/detect_drift.py",
     "L3 concept drift over the accumulated history", True),
    ("process_mining/extract_business_rules.py",
     "L2 the rules that live in code, not in configuration", False),
    # A41 — enchufado 2026-08-26, el dia que corrio por PRIMERA VEZ. Estuvo registrado como
    # capacidad siendo codigo muerto (NameError antes del primer RFC), y mientras estuvo ROTO
    # la puerta lo dejaba pasar sin llamador -- correctamente: enchufar codigo que no corre
    # seria el error. Al arreglarlo, la puerta pidio su llamador en la misma corrida.
    #
    # ⛔ NECESITA RFC, y el contrato de este fichero (ver docstring) es «esto corre lo que
    # SIEMPRE puede correr». Por eso va en RFC_REQUERIDO y SOLO corre con --con-rfc. Meterlo
    # en la lista normal habria roto la promesa del ciclo en silencio: la proxima corrida sin
    # VPN habria dado un fallo que parece del ciclo y es de la conexion.
    ("Zagentexecution/sap_data_extraction/scripts/extract_fund_center_hierarchy.py",
     "L2 la jerarquia de centros gestores (SETCLASS medida por sonda, no por catalogo)", True),
    ("process_mining/chain_lineage.py",
     "L2 the address chain — how funding reaches work when no foreign key says so", False),
    ("brain_v2/system_profile/build_profile_links.py",
     "L6 cross the profile against the model", False),
    ("brain_v2/system_profile/build_model_graph.py",
     "L6 ascent + coherence + cross-cutting", False),
    ("brain_v2/methods/build_domain_assets.py",
     "L6 asset bundle per domain", False),
    ("brain_v2/methods/build_domain_capability_matrix.py",
     "L6 is capability where the work is?", False),
    ("brain_v2/methods/measure_portability.py",
     "L6 what survives installation #2", False),
    ("brain_v2/methods/validate_paths.py",
     "the path gate — a path field must hold a path, never prose", False),
    ("brain_v2/methods/algorithm_status.py",
     "L6 which algorithms are real", False),
    ("brain_v2/methods/improve_algorithms.py",
     "L6 which algorithm to improve next", False),
    ("brain_v2/build_channel_registry.py",
     "L2 lift the DECLARED channel taxonomy out of prose so A8 can check against it", False),
    ("brain_v2/methods/audit_prose_classifications.py",
     "L6 which analysis is trapped in prose, where no algorithm can reach it", False),
    ("brain_v2/methods/audit_agent_freshness.py",
     "L6 do the agents still know what the model knows?", False),
    ("brain_v2/build_security_posture.py",
     "L6 the security store — built empty so findings never land in prose", False),
    ("brain_v2/build_s4_readiness.py",
     "L6 S/4 readiness as a SUBJECT — a column with no owner stays empty", False),
    ("brain_v2/system_profile/compose_profile.py",
     "L7 compose the profile from what everything above produced", False),
    ("brain_v2/methods/check_triggers.py",
     "L6 what needs re-running on current evidence", False),
]

# Los pasos que NO pueden correr sin conexion a SAP. Se declara aparte del paso a proposito:
# `heavy` es "tarda", esto es "no puede". Confundirlos hace que un ciclo sin VPN informe de un
# fallo que no es suyo, o peor, que alguien quite el paso para que el ciclo salga verde.
RFC_REQUERIDO = {
    "Zagentexecution/sap_data_extraction/scripts/extract_fund_center_hierarchy.py",
}


def main():
    quick = "--quick" in sys.argv
    con_rfc = "--con-rfc" in sys.argv
    sin_rfc = []
    say(f"[analysis cycle] {len(CYCLE)} steps, dependency order"
          f"{' (quick: skipping full log scans)' if quick else ''}\n")
    ok, failed, skipped = 0, [], 0

    # Stamp STARTED before anything runs. Two reasons, and the second is the better one:
    #   1. the path gate runs INSIDE this cycle, and on a fresh machine it would fail on
    #      cycle_state.json not existing yet — a chicken-and-egg of my own making;
    #   2. a cycle that STARTED AND NEVER FINISHED is now visible. Writing only on
    #      completion makes a crashed run indistinguishable from one that never began.
    import datetime
    _started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    try:
        json.dump({"status": "RUNNING", "started_utc": _started,
                   "_why": "a run that starts and dies must not look like a run that never began"},
                  open(STATE, "w", encoding="utf-8"), indent=1)
    except OSError:
        pass

    for idx, (script, label, heavy) in enumerate(CYCLE, 1):
        if quick and heavy:
            say(f"  SKIP  {label}")
            skipped += 1
            continue
        if script.split()[0] in RFC_REQUERIDO and not con_rfc:
            # NO se cuenta como saltado sin mas: se DICE que necesita RFC. Un paso que no
            # corrio por falta de conexion y uno que no corrio por ser lento son cosas
            # distintas, y mezclarlos hace que nadie sepa que le falta al resultado.
            say(f"  SKIP  {label}  (necesita RFC: usa --con-rfc)")
            skipped += 1
            sin_rfc.append(script.split()[0])
            continue
        # un paso puede llevar argumentos: "ruta.py --desde 2". Hizo falta para delegar la
        # cadena de descubrimiento sin duplicar aqui el orden de sus fases.
        partes = script.split()
        script_rel, extra = partes[0], partes[1:]
        p = REPO / script_rel
        if not p.exists():
            say(f"  MISS  {label}  ({script_rel} not found)")
            failed.append(script)
            continue
        # ⛔ DECIR POR QUE PASO VA, no solo que arranco. Hasta s110 este fichero se escribia
        # UNA vez y el progreso salia por stdout -- que cuando lanza un disparador no lo lee
        # nadie. Durante 151 minutos lo unico observable fue la palabra RUNNING, y eso hace que
        # "esta trabajando" y "se colgo hace dos horas" sean el MISMO sintoma. Con un ciclo que
        # bloquea a todo lo demas por ser el unico escritor, no poder distinguirlos es caro.
        try:
            json.dump({"status": "RUNNING", "started_utc": _started,
                       "paso": label, "script": script_rel,
                       "indice": idx, "de": len(CYCLE),
                       "desde_utc": datetime.datetime.now(datetime.timezone.utc)
                                    .isoformat(timespec="seconds"),
                       "ok_hasta_ahora": ok, "fallidos_hasta_ahora": len(failed),
                       "_why": "a run that starts and dies must not look like a run that never "
                               "began -- y uno que corre debe decir POR DONDE VA"},
                      open(STATE, "w", encoding="utf-8"), indent=1)
        except OSError:
            pass
        t0 = time.monotonic()
        r = subprocess.run([sys.executable, str(p)] + extra, cwd=str(REPO),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        dt = time.monotonic() - t0
        if r.returncode == 0:
            ok += 1
            tail = [x for x in (r.stdout or "").strip().split("\n") if x.strip()]
            head = tail[1] if len(tail) > 1 else (tail[0] if tail else "")
            say(f"  OK    {label}  ({dt:.0f}s)")
            if head:
                say(f"        {head.strip()[:110]}")
        else:
            failed.append(script)
            err = (r.stderr or r.stdout or "").strip().split("\n")
            say(f"  FAIL  {label}  ({dt:.0f}s)")
            say(f"        {(err[-1] if err else '')[:110]}")

    print(f"\n  {ok} ran · {len(failed)} failed · {skipped} skipped")
    if sin_rfc:
        # LO QUE FALTA SE NOMBRA. Un resumen que dice "N saltados" sin decir cuales convierte
        # una corrida PARCIAL en una que parece completa, que es como se lee un verde falso.
        print(f"  ⛔ {len(sin_rfc)} paso(s) NO corrieron por necesitar RFC: "
              f"{', '.join(x.split('/')[-1] for x in sin_rfc)}")
        print("     Esta corrida es PARCIAL. Para incluirlos: --con-rfc (necesita VPN a P01).")
    # RECORD THAT IT RAN — before the exit, and whether or not steps failed.
    #
    # Written even on failure ON PURPOSE. A cycle that ran and failed half its steps is WORSE
    # than one that did not run, because its artifacts look fresh; recording only successes
    # would hide exactly that case. And it is written before sys.exit(1), because the run
    # happened regardless of how it ended.
    #
    # Without this file, "run it weekly" cannot be verified and "it did not run" cannot be
    # detected — the loop would go back to depending on someone remembering, which is the
    # hole this file exists to close.
    try:
        json.dump({
            "status": "COMPLETE",
            "started_utc": _started,
            "_what_this_is": "when the cycle last ran, and how it went",
            "_why": ("a schedule that fails silently is worse than no schedule: the absence "
                     "of fresh artifacts reads as 'nothing changed'. This makes it visible."),
            "last_run_utc": datetime.datetime.now(
                datetime.timezone.utc).isoformat(timespec="seconds"),
            "steps_ran": ok, "steps_failed": len(failed), "steps_skipped": skipped,
            "failed": failed,
            "saltados_por_rfc": sin_rfc,
            "corrida_completa": not sin_rfc,
        }, open(STATE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    except OSError as e:
        say(f"  could not record the run: {e}")

    if failed:
        say("  failed: " + ", ".join(failed))
        sys.exit(1)
    say("  Every analysis algorithm ran. 'On demand' now has a demander.")


if __name__ == "__main__":
    main()
