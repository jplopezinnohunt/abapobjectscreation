r"""INC-000016471 - las consultas que SOLO pueden contestarse cuando el acumulador
traiga la ventana 2026-08-23..26 a rsau_audit_history.

POR QUE EXISTE
    El 2026-08-26 se mino el corpus para fechar el corte de ADS y el corpus TERMINABA
    EL 22. Las consultas quedaron escritas para no volver a derivarlas. Correr esto en
    cuanto `accumulate_logs.py` cierre.

QUE MIDE, Y QUE NO
    NO mide el render Adobe: MEDIDO 2026-08-26, el render NO DEJA HUELLA en el log de
    auditoria de este inquilino (0 filas de FP_JOB_OPEN / FP_FUNCTION_MODULE_NAME /
    FP_GET_LAST_ADS_ERRSTR en ninguna superficie, en 6,5 meses). Mide los TRES PROXIES
    que si existen:
      P1  latido del HOST hq-sap-sbp (= Solution Manager, SID SBP) hacia P01. El destino
          ADS apunta a ese mismo host, puerto 50300 (instancia Java 03). Si el latido
          cae a cero, la MAQUINA se cayo -- y eso explicaria ADS.
      P2  logons HTTP de ADS_AGENT desde 172.16.4.107 (SAPMHTTP, tipo de logon 'H'):
          es el Java de ADS llamando de vuelta al ABAP. Cadencia esporadica (1-6/dia,
          ~55% de los dias): su AUSENCIA UN DIA NO PRUEBA NADA. Solo vale su presencia.
      P3  poblacion de formularios HR ASR (HR_ASR_UPD_POBJ_AND_APPL_DATA por RFC) y del
          resto de superficies PDF -- cuanta gente sigue intentandolo.

TRAMPAS QUE YA COSTARON UNA MEDIDA (no repetirlas)
    - `PARAM3 LIKE '%ADS%'` devuelve 2.831 filas y TODAS son rutas 'C:\Users\x\Downloads\...':
      LIKE es insensible a mayusculas y 'Downloads' contiene 'oads'. Cero de esas filas es ADS.
    - El ULTIMO DIA del corpus siempre esta INCOMPLETO (el 22-ago trajo 23.834 filas contra
      ~157.000 de un dia normal = 15%). Un dia parcial NO es una caida. Comprobar el volumen
      total del dia ANTES de leer cualquier serie como una caida.
    - Estado 'F' de un job es TERMINADO, no CORRECTO. Un render fallido dentro de un job
      que acaba no cambia el estado.

SOLO LECTURA sobre el Gold DB (mode=ro). No escribe en SAP ni en el golden.
"""
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
GOLD = REPO / "Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"
DESDE = sys.argv[1] if len(sys.argv) > 1 else "20260815"

c = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True, timeout=900)
c.execute("PRAGMA busy_timeout=900000")
q = c.cursor()

print("=" * 78)
print("0. HASTA DONDE LLEGA EL INSTRUMENTO (y si el ultimo dia esta completo)")
print("=" * 78)
vol = list(q.execute(
    "SELECT SAL_DATE,COUNT(*) FROM rsau_audit_history WHERE SAL_DATE>=? GROUP BY 1 ORDER BY 1",
    (DESDE,)))
tipico = sorted(v for _, v in vol)[len(vol) // 2] if vol else 0
for d, n in vol:
    marca = "  <-- DIA PARCIAL, no leer como caida" if tipico and n < tipico * 0.5 else ""
    print(f"  {d}  {n:>9,}{marca}")
if not vol or vol[-1][0] < "20260826":
    print("\n  *** EL CORPUS SIGUE SIN LLEGAR AL 23-26. Las series de abajo no pueden")
    print("      fechar el corte: ausencia de dato NO es ausencia de problema. ***")

print()
print("=" * 78)
print("P1. LATIDO DEL HOST hq-sap-sbp (SolMan SBP) HACIA P01 -- el mejor proxy de 'la maquina cayo'")
print("=" * 78)
for r in q.execute("""SELECT SAL_DATE,COUNT(*),COUNT(DISTINCT SLGUSER),MIN(SAL_TIME),MAX(SAL_TIME)
    FROM rsau_audit_history WHERE PARAMX LIKE '%HQ-SAP-SBP%' AND SAL_DATE>=?
    GROUP BY 1 ORDER BY 1""", (DESDE,)):
    print("  ", r)
print("  LECTURA: cae a cero o se abre un hueco horario -> la maquina que aloja ADS se fue.")
print("           sigue plana -> la maquina esta viva y el fallo es del proceso Java, del")
print("           usuario ADSUSER en el UME, o de la ruta al puerto 50300. NINGUNA de esas")
print("           tres se ve desde aqui (ver bloque LIMITE).")

print()
print("=" * 78)
print("P2. ADS_AGENT: el Java de ADS llamando de vuelta al ABAP (logon HTTP, SAPMHTTP)")
print("=" * 78)
for r in q.execute("""SELECT SAL_DATE,SLGUSER,MSG,COUNT(*),MIN(SAL_TIME),MAX(SAL_TIME)
    FROM rsau_audit_history WHERE SLGLTRM2='172.16.4.107' AND SAL_DATE>=?
    GROUP BY 1,2,3 ORDER BY 1""", (DESDE,)):
    print("  ", r)
print("  MSG AU1 = logon correcto. Un AU2/AU6 de ADS_AGENT seria la primera prueba directa")
print("  de un problema de credencial EN ESTE LADO -- pero el 401 de ADSUSER es del otro.")
print("  Su AUSENCIA no prueba nada: la cadencia normal ya es intermitente.")

print()
print("=" * 78)
print("P3. POBLACION QUE TOCA PDF / FORMULARIOS -- cuanta gente mas esta expuesta")
print("=" * 78)
for r in q.execute("""SELECT SAL_DATE,COUNT(*),COUNT(DISTINCT SLGUSER)
    FROM rsau_audit_history WHERE PARAM3='HR_ASR_UPD_POBJ_AND_APPL_DATA' AND SAL_DATE>=?
    GROUP BY 1 ORDER BY 1""", (DESDE,)):
    print("   HR_ASR ", r)
for r in q.execute("""SELECT SAL_DATE,SLGREPNA,COUNT(*),COUNT(DISTINCT SLGUSER)
    FROM rsau_audit_history
    WHERE SLGREPNA IN ('RSTXPDFT4','Z_FO_PAYROLL_PDF','YHR_ADMIN_DETAILS_PDF',
                       'YBC_DOCX_TO_PDF_FOR_SHORTCUT','YHR_WF_INTERN_SEPARATION')
      AND SAL_DATE>=? GROUP BY 1,2 ORDER BY 1,2""", (DESDE,)):
    print("   PDF-surf", r)
print("  OJO: RSTXPDFT4 convierte SPOOL a PDF. NO pasa por ADS. Contarlo como victima")
print("  de este incidente seria inflar el radio con un canal que no usa Adobe.")

print()
print("=" * 78)
print("LIMITE DEL INSTRUMENTO -- lo que este script NO puede ver, dicho en voz alta")
print("=" * 78)
print("""  1. El 401 de ADSUSER ocurre en el UME de JAVA. ADSUSER NO EXISTE en USR02 de P01
     (medido). Un fallo de autenticacion suyo NO PUEDE generar fila en el log ABAP:
     no hay sujeto que registrar. Causa #2 del incidente = ESTRUCTURALMENTE INVISIBLE.
  2. SM21 (sm21_syslog_history) SI lleva mensajes de plugin HTTP y UNCAUGHT_EXCEPTION
     -- comprobado en su contenido -- pero solo tiene 2.402 filas del 15..22 de JUNIO.
     NO hay acumulador para SM21: la ventana de agosto no existe y no llegara sola.
  3. ST22: snap_history tiene 0 filas y st22_dumps_history 1 (21-jun). accumulate_logs.py
     lleva SNAP DESACTIVADO -- P01 devuelve TABLE_NOT_AVAILABLE por RFC_READ_TABLE.
     Los volcados de este incidente no se pueden buscar. Y el esquema de snap_history no
     lleva ni programa ni texto: aunque se llenara, no diria 'ADS'.
  4. Transportes: E070 llega al 31-jul y cts_transports al 11-mar. 'Que se importo el
     21-25 de agosto' no se puede contestar con este corpus.""")
