# -*- coding: utf-8 -*-
"""Cuanto tiempo se fue en cada cosa en esta sesion, MEDIDO.

La medida es indirecta y se declara como tal: cada instrumento que se construye deja
una marca de tiempo en disco (mtime). El hueco entre una marca y la siguiente es el
tiempo de esa fase — construir el instrumento MAS correrlo MAS leer su salida.

No mide el tiempo de pensar por separado del de ejecutar: no hay reloj para eso. Lo
que si mide, y es la pregunta real, es DONDE se va el tiempo entre fases.
"""
import os, sys, json, datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))

# que fase representa cada artefacto (en el orden en que se creo)
FASE = {
    "session_timing.json": "00 arranque: indice del brain + parseo del .eml",
    "read_ntb02_config.py": "01 leer la config del banco casa en vivo (T012K)",
    "extract_images.py": "02 extraer y LEER las capturas del correo",
    "read_febko_ntb02.py": "03 medir que extractos han entrado (FEBKO)",
    "find_uno12eur.py": "04 localizar el campo que guarda UNO12EUR (ABSND)",
    "absnd_and_job.py": "05 alcance: quien sigue entrando y quien no",
    "ebs_job_and_files.py": "06 buscar el job y las rutas de fichero",
    "ebs_integration_job.py": "07 pasos del job (fallido, se rehizo)",
    "ebs_bank_config.py": "08 config del EBS por numero de cuenta -> T028B",
    "confirm_t028b.py": "09 CONFIRMAR la causa contra un control (NTB01)",
    "read_job_log.py": "10 intentar el log del job (no accesible por RFC)",
    "job_step_and_dir.py": "11 programa del job + sondeo de directorios",
    "feb_file_handling.py": "12 fuente del programa: de donde salen las rutas",
    "feb_import_config.py": "13 customizing de importacion FEB_IMP_* + variante",
    "ebs_error_trail.py": "14 rastro de rechazo: log de aplicacion + rutas fisicas",
    "list_ebs_dirs.py": "15 primer intento de listar directorios",
    "list_coupa_dir.py": "16 listar el directorio de Coupa (se colgo, share de red)",
    "../../../knowledge/incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md":
        "17 escribir el incidente",
    "../../../knowledge/domains/Treasury/ebs_file_pipeline_and_jobs.md":
        "18 escribir el conocimiento: pipeline + variantes",
    "../../quality_checks/house_bank_ebs_wiring_check.py":
        "19 construir la PUERTA y barrer la poblacion",
    "register_incident.py": "20 registro de primera clase en el brain",
    "closed_accounts_by_text.py": "21 el corte de cuentas CERRADAS por texto",
}

items = []
for fn, fase in FASE.items():
    p = os.path.join(HERE, fn)
    if os.path.exists(p):
        items.append((os.path.getmtime(p), fn, fase))
items.sort()

if not items:
    print("sin artefactos")
    sys.exit(0)

t0 = items[0][0]
now = datetime.datetime.now().timestamp()
print("=" * 78)
print("REPARTO DEL TIEMPO — sesion s108, incidente NTB02/EUR01 (INC-000013624)")
print("=" * 78)
print("inicio de la primera marca: %s" % datetime.datetime.fromtimestamp(t0).strftime("%H:%M:%S"))
print("ahora:                      %s" % datetime.datetime.fromtimestamp(now).strftime("%H:%M:%S"))
print("total transcurrido:         %.1f min\n" % ((now - t0) / 60))

print("%-4s %-8s %-7s  %s" % ("#", "hora", "dur", "fase"))
print("-" * 78)
tot = now - t0
buckets = {}
for i, (m, fn, fase) in enumerate(items):
    nxt = items[i + 1][0] if i + 1 < len(items) else now
    dur = nxt - m
    pct = 100.0 * dur / tot if tot else 0
    bar = "#" * int(pct / 2)
    print("%-4d %-8s %5.1fm  %-52s %4.1f%% %s"
          % (i + 1, datetime.datetime.fromtimestamp(m).strftime("%H:%M:%S"),
             dur / 60, fase[:52], pct, bar))
    grupo = ("1 ENTENDER el caso" if fase[:2] in ("00", "01", "02", "03", "04")
             else "2 AISLAR la causa" if fase[:2] in ("05", "08", "09")
             else "3 el PIPELINE de ficheros" if fase[:2] in ("06", "07", "10", "11", "12", "13", "14", "15", "16")
             else "4 DEJARLO ESCRITO + puerta + barrido")
    buckets[grupo] = buckets.get(grupo, 0) + dur

print("\n" + "=" * 78)
print("POR BLOQUE")
print("=" * 78)
for k, v in sorted(buckets.items(), key=lambda x: -x[1]):
    print("  %-26s %6.1f min   %4.1f%%  %s" % (k, v / 60, 100 * v / tot, "#" * int(50 * v / tot)))

print("\nNOTA DE METODO: la medida es el hueco entre marcas de disco. Incluye construir el")
print("instrumento, correrlo y leer su salida. NO separa pensar de ejecutar: no hay reloj")
print("para eso. Dos fases (07 y 15) fallaron y hubo que rehacerlas — su tiempo se cuenta.")

json.dump([{"orden": i + 1, "hora": datetime.datetime.fromtimestamp(m).isoformat(timespec="seconds"),
            "artefacto": fn, "fase": fase,
            "minutos": round((items[i + 1][0] if i + 1 < len(items) else now) - m, 1) / 60}
           for i, (m, fn, fase) in enumerate(items)],
          open(os.path.join(HERE, "session_timing_measured.json"), "w"), indent=2, ensure_ascii=False)
