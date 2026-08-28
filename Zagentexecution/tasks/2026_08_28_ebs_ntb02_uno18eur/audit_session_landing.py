# -*- coding: utf-8 -*-
"""AUDITORIA de aterrizaje de s108: ¿esta cada cosa generada en su mecanismo, o se perdio algo?

No se afirma "esta todo": se comprueba fichero a fichero LEYENDO EL DESTINO. Cada linea es una
pregunta con respuesta binaria y su evidencia. Lo que falte sale como FALTA, no se maquilla.
"""
import json, io, os, subprocess, sys, collections

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OK, NO = "OK  ", "FALTA"
res = []


def chk(mecanismo, que, cond, evid=""):
    res.append((OK if cond else NO, mecanismo, que, evid))


# ---------- 1. MINEROS / instrumentos -----------------------------------------
INSTR = ["house_bank_ebs_wiring_check", "bank_statement_channel_census",
         "bank_account_nature_model", "bank_config_profile_by_nature",
         "bank_account_behaviour_signature", "ebs_format_consolidation"]
alg = io.open("brain_v2/methods/algorithms.json", encoding="utf-8").read()
for i in INSTR:
    p = "Zagentexecution/quality_checks/%s.py" % i
    chk("MINERO", "%s existe en disco" % i, os.path.exists(p), p)
    chk("MINERO", "%s registrado en algorithms.json" % i, i in alg)
# ¿tienen failure_mode? un registro sin el no sirve
a = json.load(io.open("brain_v2/methods/algorithms.json", encoding="utf-8"))
for k, v in a.items():
    if isinstance(v, dict) and v.get("_session") == 108:
        chk("MINERO", "%s declara failure_mode" % k, bool(v.get("failure_mode")))
        chk("MINERO", "%s declara bound_in" % k, bool(v.get("bound_in")))

# ---------- 2. CONOCIMIENTO de dominio ----------------------------------------
DOCS = ["knowledge/domains/Treasury/ebs_file_pipeline_and_jobs.md",
        "knowledge/domains/Treasury/bank_statement_channels_by_company.md",
        "knowledge/domains/Treasury/bank_account_nature_model.md",
        "knowledge/domains/Treasury/ebs_format_models.md",
        "knowledge/incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md"]
readme = io.open("knowledge/domains/Treasury/README.md", encoding="utf-8").read()
for d in DOCS:
    chk("DOC", "%s existe" % os.path.basename(d), os.path.exists(d), d)
for d in DOCS[:4]:
    b = os.path.basename(d)
    chk("DOC", "%s enlazado desde el README del dominio" % b, b in readme)

# ---------- 3. CLAIMS ----------------------------------------------------------
cl = json.load(io.open("brain_v2/claims/claims.json", encoding="utf-8"))
s108 = [c for c in cl if c.get("created_session") == 108]
chk("CLAIM", "hay claims de s108 (esperado 7)", len(s108) >= 7, "%d encontrados" % len(s108))
for c in s108:
    chk("CLAIM", "claim %s tiene evidencia" % c["id"], bool(c.get("evidence_for")))

# ---------- 4. INCIDENTE -------------------------------------------------------
inc = json.load(io.open("brain_v2/incidents/incidents.json", encoding="utf-8"))
r = [x for x in inc if x.get("id") == "INC-000013624"]
chk("INCIDENTE", "registro de primera clase existe", bool(r))
if r:
    chk("INCIDENTE", "estado actualizado a SAP completo", "ESCALATED_UPSTREAM" in r[0].get("status", ""),
        r[0].get("status", ""))
    chk("INCIDENTE", "apunta a su analysis_doc", bool(r[0].get("analysis_doc")))
    chk("INCIDENTE", "declara puerta recurrente", bool(r[0].get("recurring_check")))

# ---------- 5. SKILLS ----------------------------------------------------------
sk = io.open(".claude/skills/sap_bank_statement_recon/SKILL.md", encoding="utf-8").read()
for t, q in [("T028B", "T028B"), ("EFART", "canal E/M"), ("CLOSED", "cuentas cerradas por texto"),
             ("YBANK", "YBANK"), ("behaviour_signature", "clasificacion por comportamiento"),
             ("first statement lands", "FF67: cuenta nueva no sale hasta el primer extracto"),
             ("TDAT GRW_SET", "YBANK se transporta como tabla completa")]:
    chk("SKILL recon", q, t in sk)
hb = io.open(".claude/skills/sap_house_bank_configuration/SKILL.md", encoding="utf-8").read()
for t, q in [("house_bank_ebs_wiring_check", "puerta en el Pre-Close Checklist"),
             ("ACCOUNT NUMBER of an existing account changes", "camino de cambio de numero")]:
    chk("SKILL housebank", q, t in hb)

# ---------- 6. AGENTE ----------------------------------------------------------
ag = io.open(".claude/agents/bank-process-discovery.md", encoding="utf-8").read()
for t, q in [("house_bank_ebs_wiring_check", "conoce los instrumentos nuevos"),
             ("receiving_accounts", "declara el solape a reconciliar"),
             ("load_domain", "lleva la leccion de metodo")]:
    chk("AGENTE", q, t in ag)

# ---------- 7. COMPANIONS ------------------------------------------------------
co = io.open("companions/bank_statement_ebs_companion.html", encoding="utf-8").read()
for t, q in [("Step 0", "identificacion de cuenta / T028B"),
             ("Mismo modelo de extracto, uso distinto", "mismo modelo, uso distinto"),
             ("La oportunidad, dimensionada", "oportunidad dimensionada"),
             ("NO aparece en FF67", "FF67 no sale hasta el primer extracto"),
             ("YBANK", "YBANK y lo que no clasifica")]:
    chk("COMPANION EBS", q, t in co)
ch = io.open("companions/house_bank_configuration_companion.html", encoding="utf-8").read()
chk("COMPANION HB", "paso 6 corregido a V_T028B", "V_T028B</b> (NOT V_T035D)" in ch)

# ---------- 8. PMO + MEMORIA ---------------------------------------------------
pmo = io.open(".agents/intelligence/PMO_BRAIN.md", encoding="utf-8").read()
chk("PMO", "H144 dado de alta", "H144" in pmo)
chk("PMO", "H144 lleva el enlace a la propuesta", "artifact/35649321" in pmo)
M = "C:/Users/jp_lopez/.claude/projects/c--Users-jp-lopez-projects-abapobjectscreation/memory"
for f in ("project_bank_account_nature.md", "incident_ebs_account_number_change_orphans_t028b.md"):
    chk("MEMORIA", "%s existe" % f, os.path.exists(os.path.join(M, f)))
mem = io.open(os.path.join(M, "MEMORY.md"), encoding="utf-8").read()
chk("MEMORIA", "MEMORY.md apunta a los dos", "project_bank_account_nature" in mem and "incident_ebs_account" in mem)

# ---------- 9. REGLAS ----------------------------------------------------------
fr = io.open("brain_v2/agent_rules/feedback_rules.json", encoding="utf-8").read()
chk("REGLA", "name_the_source extendida con la forma (e)", "(e) UNA LECTURA QUE SALE BIEN" in fr)

# ---------- 10. retro y modelo de capacidad -----------------------------------
# Estas dos comprobaciones estaban MAL escritas en la primera version: la del retro buscaba
# 's108_retro.md' cuando el fichero se llama 'session_108_retro.md', y la del modelo estaba
# HARDCODEADA a False. Las dos daban FALTA con el trabajo ya hecho. Es medir la forma y no el
# efecto, dentro del propio instrumento que audita.
RD = "knowledge/session_retros"
retro = [f for f in os.listdir(RD) if "108" in f] if os.path.isdir(RD) else []
chk("RETRO", "retro de sesion escrita", bool(retro), ", ".join(retro))

cmj = json.load(io.open("brain_v2/capability_model/capability_model.json", encoding="utf-8"))
tre = cmj.get("domains", {}).get("Treasury_EBS", {})
chk("MODELO", "capability_model registra lo aprendido en Treasury_EBS", "s108_note" in tre)
chk("MODELO", "F_INTERFACE_FILE subio a HAVE", tre.get("F_INTERFACE_FILE") == "HAVE",
    tre.get("F_INTERFACE_FILE", ""))
chk("MODELO", "G_CONFORMANCE ya no es NONE", tre.get("G_CONFORMANCE") not in (None, "NONE"),
    tre.get("G_CONFORMANCE", ""))
chk("MODELO", "S_STANDARD_REF sigue declarado NONE (no se comparo con el estandar)",
    tre.get("S_STANDARD_REF") == "NONE", tre.get("S_STANDARD_REF", ""))

# ---------- salida --------------------------------------------------------------
print("=" * 92)
print("AUDITORIA DE ATERRIZAJE — sesion s108")
print("=" * 92)
por = collections.OrderedDict()
for st, m, q, e in res:
    por.setdefault(m, []).append((st, q, e))
for m, lst in por.items():
    faltan = sum(1 for x in lst if x[0] == NO)
    print("\n%s  (%d comprobaciones, %d fallan)" % (m, len(lst), faltan))
    for st, q, e in lst:
        if st == NO:
            print("   %s  %s %s" % (st, q, ("-- " + e) if e else ""))
    if faltan == 0:
        print("   OK   todo aterrizado (%d/%d)" % (len(lst), len(lst)))

tot = len(res); mal = sum(1 for x in res if x[0] == NO)
print("\n" + "=" * 92)
print("TOTAL: %d comprobaciones · %d OK · %d FALTAN" % (tot, tot - mal, mal))
