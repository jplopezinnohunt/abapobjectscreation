# ZSAPFPAYM_REPLAY — Payment Medium Replay para Debug DMEE

**Origen:** copia controlada de `SAPFPAYM` extraído de P01 sesión #072.
**Sistema target:** D01 (no P01 — feedback_p01_readonly_absolute).
**Run de prueba:** D01 / LAUFD=20260507 / LAUFI=10003B / GRPNO=100 / FORMI=/SEPA_CT_UNES.

## Qué hace

Re-procesa un run F110 ya consolidado en `DFPAYG` para regenerar el output DMEE
(XML SEPA, CGI, CITI, etc.) **sin** alterar `REGUV.STATUS` / `DFPAYG.ANZ_ERL`.
Permite escribir el XML a disco local o pantalla y entrar al debugger
exactamente en el momento donde el motor DMEE mapea los campos.

## Diferencias vs SAPFPAYM original

8 bloques comentados en `ZFPAYM_STA`:

| Líneas orig. | Bloque removido | Por qué |
|---|---|---|
| 17-28 | `SELECT REGUV.X_DD_PRENOTIF` + STOP | Gate prenotif DD irrelevante |
| 31-56 | `FIBL_PAYMENT_RUN_MERGE_CHECK` + STOP | Gate cross-payment merge |
| 92-100 | `check_reguv_status(sapfpaym_schedule)` + STOP | Gate REGUV.STATUS |
| 103-132 | `FI_CHECK_PAYMENT_DATA` + `FI_UPDATE_PAYMENT_DATA` | Pre-service refresh (genera UPDATE) |
| 136-155 | `FI_PAYGROUP_F4` popup | Reemplazado por `PM_GRPNO` obligatorio |
| 161-184 | `ENQUEUE_EFDFPAYG` + STOP | Lock |
| **205-232** | **`anz_erz LE anz_erl` + STOP** | **★ EL CHECK CRÍTICO QUE BLOQUEA RE-EJECUCIÓN** |
| 378 | `COMMIT WORK` | Diferido — ROLLBACK al final |

1 bloque comentado en `ZFPAYM_GET`:
- 11-40: `FI_REF_DOCUMENT_CHECK` + `REJECT`

1 inserción en `ZFPAYM_GET`:
- antes de línea 71: `BREAK-POINT ID 'YDMEE_REPLAY'.`

1 línea añadida en `ZFPAYM_END`:
- `ROLLBACK WORK.` al final → descarta UPDATE de DFPAYG.ANZ_ERL, REGUV.STATUS, REGUH.XEB1, etc.

## Archivos del paquete

| Archivo | Origen | Modificado |
|---|---|---|
| `ZSAPFPAYM_REPLAY.abap` | nuevo (driver) | nuevo |
| `ZFPAYM_TOP.abap` | = `FPAYM_TOP` | no |
| `ZFPAYM_INI.abap` | = `FPAYM_INI` | no |
| `ZFPAYM_SEL.abap` | = `FPAYM_SEL` | no |
| `ZFPAYM_STA.abap` | = `FPAYM_STA` | **sí** (8 bloques) |
| `ZFPAYM_GET.abap` | = `FPAYM_GET` | **sí** (1 bloque + 1 inserción) |
| `ZFPAYM_END.abap` | = `FPAYM_END` | **sí** (ROLLBACK WORK) |
| `ZFPAYM_LNS.abap` | = `FPAYM_LNS` | no |
| `ZFPAYM_SUB.abap` | = `FPAYM_SUB` | no |

## Deploy en D01 (SE38 / SE80)

### Opción A — manual paste

1. SE38 → crear `ZSAPFPAYM_REPLAY` (REPORT, paquete YPMW_DMEE_REPLAY)
2. SE38 → crear los 8 includes `ZFPAYM_*` (Type I)
3. Pegar contenido de cada `.abap`
4. Activar todos (Ctrl-F3 cada uno)

### Opción B — RFC `RFC_ABAP_INSTALL_AND_RUN` con `INSERT REPORT`

(El script `deploy_zsapfpaym_replay.py` se entrega aparte si la opción A es lenta.)

## Ejecución

### Selection screen (variant `ZREPLAY_10003B`)

```
PM_LAUFD  = 20260507
PM_LAUFI  = 10003B
PM_XVORL  = ' '
PM_GRPNO  = 100
PAR_FORM  = /SEPA_CT_UNES
PAR_XPY3  = 'X'                  (DMEE output)
PAR_XFIL  = 'X'                  (filesystem mode)
PAR_FILE  = C:\tmp\dmee_10003B_sepa.xml
PAR_BOTH  = ' '                  (no TemSe parallel)
PAR_XLST  = 'X'                  (accompanying list visible)
PAR_XERR  = 'X'                  (error log to spool)
```

### Debug ladder

| Nivel | Cómo | Cuándo |
|---|---|---|
| L1 — sin debug | F8 directo | Primer test "smoke": ¿genera XML? ¿coincide con archivo F110 original? |
| L2 — BREAK-POINT estructuras | SAAB → activar `YDMEE_REPLAY` → F8 | Inspeccionar `fpayh` / `gt_fpayp` / `par_form` ANTES del motor DMEE |
| L3 — BP en exit BAdI | SE24 USER-BP en `YCL_IDFI_CGI_DMEE_FALLBACK_CM001->GET_CREDIT` | Ver mapeo `i_node_path → c_value` por nodo del árbol |
| L4 — BP en motor SAP std | SE24 USER-BP en `CL_DMEE_CONVERSION->INTERPRET_NODE` | Solo si necesitas entender la traversal interna |

## Verificación post-ejecución

Después de F8:

```sql
-- Esto NO debe haber cambiado (ROLLBACK efectivo):
SELECT ANZ_ERL FROM DFPAYG WHERE LAUFD='20260507' AND LAUFI='10003B';
-- Antes y después del replay → debe ser el mismo número.

-- Esto SÍ debe existir (file I/O no transaccional):
DIR C:\tmp\dmee_10003B_sepa.xml
-- Tamaño ~1-3 KB para un solo pago SEPA EUR.
```

## Referencias

- Origen extracción: `Zagentexecution/mcp-backend-server-python/extract_sapfpaym_full_p01.py`
- Builder de los 3 modificados: `Zagentexecution/mcp-backend-server-python/build_zsapfpaym_replay.py`
- Estructuras DDIC consumidas: `extracted_code/FI/SAPFPAYM/structures/{FPAYH,FPAYHX,FPAYP,REGUH,REGUP}.json`
- BAdI exit canónico: `extracted_code/FI/DMEE_p01_canonical/YCL_IDFI_CGI_DMEE_FALLBACK====CM001.abap`
- Brain rule: `feedback_search_dfpayg_for_sapfpaym_runs` (sesión #072)
- Brain rule: `feedback_p01_readonly_absolute` (sesión #052) — replay solo en D01
