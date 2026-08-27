# -*- coding: utf-8 -*-
"""INC-000016471 - publica en el bus de mineros lo MEDIDO sobre el canal ADS.

Idempotente: `publicar` sustituye el hallazgo del MISMO minero sobre el MISMO sujeto y
aspecto, asi que se puede volver a correr tras re-medir con la ventana 23-26 completa.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "process_mining"))
from mining_bus import publicar, preguntar, consultar  # noqa: E402

M = "inc16471_ads_log_mining"
S = 105

publicar(M, "REALIDAD", "ADS",
 "el render Adobe NO DEJA HUELLA en el log de auditoria de P01: cero eventos de FP_JOB_OPEN, "
 "FP_FUNCTION_MODULE_NAME o FP_GET_LAST_ADS_ERRSTR en NINGUNA superficie (SLGREPNA, SLGTC, "
 "PARAM1, PARAM3) en 6,5 meses. La transaccion SFP se abrio 2 veces en todo el corpus, las dos "
 "por el desarrollador N_MENARD. No se puede fechar una caida de ADS con este instrumento: no es "
 "que la traza este apagada, es que el evento no existe. AUSENCIA DE DATO, NO DE PROBLEMA.",
 evidencia="rsau_audit_history 28,58M filas 2026-02-03..2026-08-24; SLGREPNA LIKE 'FP%' = 14 filas "
           "(FPINTERFACEPARTYPESINTERNAL 12, FP_START_FORM_BUILDER 2); PARAM3 LIKE 'FP%' = 8; "
           "SLGTC LIKE 'SFP%' = 2 (N_MENARD, 2026-03-12 y 2026-06-23)",
 autoridad="MEDIDO_EN_DATOS", sesion=S, aspecto="OBSERVABILIDAD")

publicar(M, "REALIDAD", "ADS",
 "RADIO MEDIDO POR EL CATALOGO, no por el log: 50 formularios Adobe (SFPF) y 17 interfaces (SFPI) "
 "propios en el grafo del brain. Si ADS cae, cae TODO esto a la vez: 15 del convenio de practicas "
 "(YHRINT_AGREEMENT*, con 6 anexos EN/FR), certificados y evaluacion de practicas, 8 contratos de "
 "personal (YHR_CONTRACT_*), 7 atestaciones de trabajo (YHRPA_ATT_*), el PAF de acciones de personal "
 "(YHRPA_PAF*), 5 cartas de reclamacion FI (YFI_DUNNING_FORM*) y 6 de patrimonio (YRE_*). ES UN SUELO: "
 "solo cuenta lo Y*/Z* presente en el grafo, no el repositorio entero ni lo estandar.",
 evidencia="brain_v2/output/brain_v2_graph.json: 50 nodos OBJ:SFPF y 17 OBJ:SFPI",
 autoridad="MEDIDO_EN_DATOS", sesion=S, aspecto="RADIO_DE_ALCANCE")

publicar(M, "REALIDAD", "RSAU_AUDIT_HISTORY",
 "TRAMPA MEDIDA: `PARAM3 LIKE '%ADS%'` devuelve 2.831 filas y NINGUNA es ADS. El LIKE de SQLite es "
 "insensible a mayusculas en ASCII y 'Downloads' contiene 'oads'. Todas son rutas de descarga de "
 "puesto de trabajo. Quien busque ADS por subcadena publica un canal vivo que no existe.",
 evidencia="SELECT PARAM3,COUNT(*) WHERE PARAM3 LIKE '%ADS%' GROUP BY 1 -> 40/40 valores del top "
           "son rutas de fichero terminadas en .XLSX/.DAT/.txt",
 autoridad="MEDIDO_EN_DATOS", sesion=S, aspecto="TRAMPA_DE_LECTURA")

publicar(M, "REALIDAD", "RSAU_AUDIT_HISTORY",
 "EL ULTIMO DIA DEL CORPUS SIEMPRE ESTA INCOMPLETO y se lee como una caida. Comprobar el volumen del "
 "dia y su MAX(SAL_TIME) ANTES de leer cualquier serie como un corte.",
 evidencia="20260820:158.783 20260821:157.305 22:23.834 (hasta 05:31) 23:84.369 24:22.987 (hasta 05:14), "
           "con el acumulador corriendo el 2026-08-26; un dia laborable completo son ~157.000 filas",
 autoridad="MEDIDO_EN_DATOS", sesion=S, aspecto="VENTANA")

publicar(M, "CANAL_Y_ACTOR", "ZPAWF_INT_AGREE",
 "LA APP 'Internship Agreement' del INC-000016471 ES ESTO: una Web Dynpro ABAP NUESTRA (autor "
 "N_MENARD), servida por ICF sobre HTTP en el propio P01 -- no un satelite, no un Fiori. Se entra por "
 "ZPAWF_INT_HP. NO es un usuario con un problema: 3.751 arranques por 210 USUARIOS DISTINTOS en 6,5 "
 "meses, y la familia ZPAWF* la usan entre 18 y 32 personas CADA DIA LABORABLE. El PDF es el paso "
 "TERMINAL: sin el, el expediente queda validado y sin firmar.",
 evidencia="rsau PARAM1='R3TR WDYA ZPAWF_INT_AGREE' 3.751 arranques / 210 usuarios; ZPAWF_INT_HP "
           "3.088 / 257; E_WINTENBERG en ZPAWF_INT_HP el 2026-07-21 y el 2026-08-21; el 20260821, "
           "70 arranques ZPAWF por 20 usuarios distintos. Inventario de objetos: "
           "knowledge/abap-style-guide/N_MENARD-OBJECT-INVENTORY.md seccion 9 (WDYA/WDYN/SICF/SFPF)",
 autoridad="MEDIDO_EN_DATOS", sesion=S, aspecto="IDENTIDAD_Y_POBLACION")

publicar(M, "CANAL_Y_ACTOR", "HQ-SAP-SBP",
 "EL HOST DEL DESTINO ADS ES EL DE SOLUTION MANAGER (SID SBP), IP 172.16.4.107. Misma maquina: "
 "instancia ABAP 01 para SolMan, instancia Java 03 (puerto 50300) para ADS. Consecuencia "
 "arquitectonica: un reinicio, parcheo o saturacion de la maquina de SolMan se lleva por delante "
 "TODOS los PDF de la institucion. Y da un SENSOR DE DISPONIBILIDAD que SI podemos leer: llama a P01 "
 "como un metronomo, ~2.120-2.290 eventos cada dia, de 00:00 a 23:58, sin un hueco.",
 evidencia="rsau PARAMX LIKE '%HQ-SAP-SBP%' = 416.193 filas, usuario SMTMSBP, PARAMX literal "
           "'caller: host=HQ-SAP-SBP_SBP_01, dest=SM_P01CLNT350_READ/TRUSTED/LOGIN', usuarios "
           "SOLMAN_BTC y SM_EFWK, extractores /SDF/*; serie diaria 20260801..21 entre 2.118 y 2.288; "
           "SLGLTRM2='172.16.4.107' lleva a la vez a SMTMSBP y a ADS_AGENT; "
           "rfcdes ADS: H=hq-sap-sbp.hq.int.unesco.org I=50300",
 autoridad="MEDIDO_EN_DATOS", sesion=S, aspecto="TOPOLOGIA")

publicar(M, "CANAL_Y_ACTOR", "ADS_AGENT",
 "NO ES el usuario del destino: va EN SENTIDO CONTRARIO. ADS_AGENT entra al ABAP por HTTP (tipo de "
 "logon 'H', programa SAPMHTTP, tcode S000) desde 172.16.4.107 -- es el Java de ADS llamando de vuelta "
 "a P01. ADSUSER es la credencial que el ABAP usa para ir HACIA el Java y vive en el UME de Java. "
 "Confundirlos hace buscar un 401 en el log equivocado. 287 eventos en 6,5 meses, TODOS AU1 "
 "(correctos), cero fallidos, 1-6 al dia y no todos los dias: su AUSENCIA un dia NO PRUEBA NADA, "
 "solo vale su presencia.",
 evidencia="rsau SLGUSER='ADS_AGENT': PARAM1='H', SLGREPNA='SAPMHTTP', SLGLTRM2='172.16.4.107', "
           "SLGTC='S000'; ultimo evento 2026-08-21 14:35:30; USR02 no contiene ADSUSER",
 autoridad="MEDIDO_EN_DATOS", sesion=S, aspecto="DIRECCION_DEL_CANAL")

publicar(M, "REALIDAD", "ADSUSER",
 "ESTRUCTURALMENTE INVISIBLE PARA NOSOTROS. La causa #2 del incidente (ADSUSER bloqueado o con "
 "contrasena caducada) produce un HTTP 401 EN EL UME DE JAVA. ADSUSER no existe en USR02 de P01 "
 "-- MEDIDO --, luego no hay sujeto ABAP al que atribuir un evento: el log de auditoria de P01 no "
 "puede registrar ese fallo ni en principio. Ningun barrido nuestro la confirmara ni la refutara. "
 "Solo se ve desde NWA / el UME del AS Java de hq-sap-sbp.",
 evidencia="usr02: ADSUSER ausente (ADS_AGENT si existe: USTYP=B, UFLAG=0, GLTGB=00000000, "
           "TRDAT=20260821); rfcdes ADS D=ADSUSER Q=B (basic) s=N (HTTP plano) T=N (traza off)",
 autoridad="DECLARADO_POR_SAP", sesion=S, aspecto="FRONTERA_DEL_INSTRUMENTO")

publicar(M, "REALIDAD", "SNAP_HISTORY",
 "CIEGO POR CONSTRUCCION, dos veces. (a) 0 filas: accumulate_logs.py lleva SNAP DESACTIVADO porque "
 "P01 devuelve TABLE_NOT_AVAILABLE por RFC_READ_TABLE; no se llenara solo. (b) Aunque se llenara, su "
 "esquema es DATUM/UZEIT/AHOST/UNAME/MODNO/SEQNO: NO lleva programa, ni clase de error, ni texto, asi "
 "que jamas podria contestar 'un volcado que mencione ADS'. st22_dumps_history SI lleva "
 "ERROR_CLASS/OBJECT/MESSAGE pero tiene 1 fila (2026-06-21, DBIF_REPO_SQL_ERROR).",
 evidencia="snap_history COUNT(*)=0; st22_dumps_history COUNT(*)=1; accumulate_logs.py lineas 114-117",
 autoridad="MEDIDO_EN_DATOS", sesion=S, aspecto="INSTRUMENTO_CIEGO")

publicar(M, "REALIDAD", "SM21_SYSLOG_HISTORY",
 "EL INSTRUMENTO CORRECTO, SIN ALIMENTAR. Su contenido SI llevaria la respuesta: tiene mensajes de "
 "plugin HTTP (AREA R2 / SUBID G, programa SAPMHTTP) y UNCAUGHT_EXCEPTION (E0/A). Pero solo tiene "
 "2.402 filas y TODAS del 15..22 de JUNIO de 2026: una extraccion suelta, no un flujo. "
 "accumulate_logs.py acumula exactamente cuatro flujos -- TBTCO, TBTCP, CDHDR y RSAU -- y SM21 no "
 "esta entre ellos. La ventana de agosto no existe y no va a llegar sola.",
 evidencia="sm21_syslog_history 2.402 filas, TS 2026061512290900..2026062213393400; "
           "LOG_TABLES en accumulate_logs.py = {TBTCO, TBTCP, CDHDR} mas RSAU por su propia via",
 autoridad="MEDIDO_EN_DATOS", sesion=S, aspecto="INSTRUMENTO_CIEGO")

publicar(M, "REALIDAD", "P01_BATCH",
 "NO HUBO OLA DE ABORTOS EN BATCH el 24-26 de agosto: 2.259 / 5.321 / 3.156 jobs, TODOS en estado F. "
 "Los dos unicos abortos del periodo son del 21 (RPCIPE00_OLD) y del 23 "
 "(SAP_SLD_DATA_COLLECT_STARTUP), ninguno relacionado. Compatible con un fallo SINCRONO del lado "
 "dialogo, no con una caida global. OJO: 'F' es TERMINADO, no CORRECTO -- RFFOAVIS_FPAYM (aviso de "
 "pago, unico programa de nuestro corpus extraido con formulario Adobe) corrio 7 veces el 25 y 19 el "
 "26 y acabo en F las 26. Eso NO prueba que su PDF saliera.",
 evidencia="tbtco_history 20260818..20260826 agrupado por STATUS; tbtcp_history JOIN tbtco_history "
           "por PROGNAME='RFFOAVIS_FPAYM'",
 autoridad="MEDIDO_EN_DATOS", sesion=S, aspecto="CONTROL_NEGATIVO")

preguntar(M, "ADSUSER",
 "Esta ADSUSER bloqueado o con la contrasena caducada en el UME del AS Java de hq-sap-sbp "
 "(instancia 03, puerto 50300)? Y esta arrancada la aplicacion AdobeDocumentServices en NWA?",
 para="Basis / dueno del AS Java",
 porque="ADSUSER no existe en USR02 de P01 (medido). Un 401 suyo ocurre en Java y no puede generar "
        "ninguna fila en el log ABAP. Es la unica de las cuatro causas que no puedo ni confirmar ni "
        "refutar desde aqui, y encaja con el patron 'funcionaba ayer, falla desde esta manana'.")

preguntar(M, "HQ-SAP-SBP",
 "Se reinicio, parcheo o quedo sin recursos la maquina hq-sap-sbp (Solution Manager, 172.16.4.107) "
 "entre el 24 y el 25 de agosto de 2026 por la manana?",
 para="Basis",
 porque="El destino ADS apunta a esa misma maquina en el puerto 50300. Si se movio la maquina, se "
        "movieron los PDF de toda la institucion. El latido de SolMan hacia P01 es el unico proxy de "
        "disponibilidad que tenemos de esa maquina, y se lee con "
        "Zagentexecution/tasks/2026_08_26_inc16471_ads_log_mining/ads_outage_window_check.py")

print("publicado.")
for s in ("ADS", "ZPAWF_INT_AGREE", "HQ-SAP-SBP", "ADS_AGENT", "ADSUSER"):
    print(f"  {s}: {len(consultar(s))} hallazgos en el bus")
