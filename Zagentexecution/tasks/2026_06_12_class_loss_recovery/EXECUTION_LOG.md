# Execution Log — Recuperación 3 clases N_MENARD (INC-CLASS-LOSS 2026-06)

Registro de la **ejecución real** del runbook (`~/.claude/plans/logical-finding-sedgewick.md`), paso a paso,
con evidencia. Las imágenes van en `screenshots/` (dejá cada PNG con el nombre indicado y queda referenciado).

- **TR de recuperación:** `V01K910259` — Transport of Copies, owner JP_LOPEZ, target D01, source client 350.
- **Fecha:** 2026-06-12 · **Operador GUI:** jp_lopez · **Verificación RFC read-only:** Claude.
- **Objetos (3):** YCL_FI_ACCOUNT_SUBST_BL (32 métodos), YCL_FI_ACCOUNT_SUBST_READ (1), YCL_FI_BANK_RECONCILIATION_BL (54).

| # | Paso | Acción real | Evidencia (screenshots/) | Verificación RFC |
|---|---|---|---|---|
| 0 | Baseline TS2 | Confirmado 3 sanas en TS2 (32/1/54); 11 = borrado real | `00_ts2_conn.png`, `00_ports.png` | `verify_recovery.py` baseline OK |
| A.1 | SE01 Deliveries (desvío) | Create dio "Delivery Transport" (no servía) → cambiamos a SE09 | `A1_se01_deliveries_wrong.png` | — |
| A.2 | SE09 Create Request | Popup tipos → elegido **Transport of Copies** | `A2_create_request_types.png` | — |
| A.3 | TS2 target D01 (descartado) | Warning "Target D01 unknown" → TS2 dominio aislado → pivote a V01 | `A3_ts2_target_unknown.png` | TMSCSYS: TS2=DOMAIN_TS2 (no conoce D01); V01=DOMAIN_P01 (conoce D01) |
| A.4 | Crear TR en V01 | SE09 V01 → Transport of Copies → target D01 → `V01K910259` | `A4_v01_tr_created.png` | E070: TRFUNCTION=T, TRSTATUS=D, TARSYSTEM=D01 ✓ |
| B | Agregar 3 objetos | Objects tab → 3 filas R3TR/CLAS | `B_objects_added.png` | E071 = 3 objetos CLAS ✓ |
| C | Release | SE09 → Release Directly → export | `C_release_log.png` | E070 TRSTATUS=R; log RC(0) Checks/Pre-Export/Export + D01 Selection ✓ |
| D | Import en D01 | STMS → import SOLO V01K910259 (fila 9), Target client 350, **Overwrite Originals** ✓, async | `D1_import_queue.png`, `D2_import_options.png`, `D3_start_import.png`, `D4_import_rc4.png` | RC **4** (warning esperado de overwrite originals) = OK ✓ |
| E | Activar | No hizo falta — el import dejó las 3 **activas** (SEOCLASSDF state=1) | — | SEOCLASSDF version=1 state=1, CHANGEDON=20260612 ✓ |
| V | Verificación final | `verify_recovery.py` | `V_verify_ok.png` | **3/3 RECOVERED**: 32/1/54 métodos == V01/TS2; VRSD intacto (BANK 00000-00008) ✓ |

## Notas de la ejecución (lecciones reales)
- La pestaña **Deliveries** de SE01 NO sirve para Transport of Copies (da Delivery/OCS). Usar **SE09 → Create**.
- **TS2 está en DOMAIN_TS2 aislado** → no puede entregar a D01 (warning "target unknown"). La fuente correcta
  es **V01** (DOMAIN_P01, mismo dominio que D01). TS2 sirvió solo como **baseline**.
- TS2 por RFC: gateway en **:3300** (no :4800 como D01/V01).
- Importar en D01 **solo** la TR nuestra (fila 9), NO toda la cola (hay SPAU/upgrade de terceros con RC rojo).
- Versiones previas: **no se tocan** — el historial (VRSD) sobrevivió en D01; el import agrega 1 versión nueva encima.

## Resultado final ✅
**3/3 RECUPERADAS** (2026-06-12 ~15:52). Verificado por RFC en D01:
- YCL_FI_ACCOUNT_SUBST_BL → activa, 32 métodos, VRSD v00000-00001
- YCL_FI_ACCOUNT_SUBST_READ → activa, 1 método, VRSD v00000-00001
- YCL_FI_BANK_RECONCILIATION_BL → activa, 54 métodos, VRSD v00000-00008
Todas con SEOCLASSDF state=1 (activas), CHANGEDON=20260612 (versión del import encima), **historial previo
preservado**. Vía: Transport of Copies `V01K910259` (V01→D01, Overwrite Originals). Cero ADT write.
Las 11 "borrado real" NO se tocaron (no eran daño nuestro).
