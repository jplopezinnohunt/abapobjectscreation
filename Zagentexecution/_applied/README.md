# `_applied/` — escritores directos del brain, YA APLICADOS. **NO RE-EJECUTAR.**

> Cuarentena de gobernanza. Todo lo que está acá es **deuda técnica histórica**, no herramienta viva.

## (a) Qué son estos scripts

Scripts "one-shot" escritos en sesiones pasadas (s054 → s078) que **escriben DIRECTO** a los stores
core de `brain_v2/` (`claims/claims.json`, `agent_rules/feedback_rules.json`,
`annotations/annotations.json`, `incidents/incidents.json`, `agi/known_unknowns.json`,
`agi/data_quality_issues.json`) **sin pasar por el brain-steward**.

Su efecto ya está aplicado y materializado en el brain. Mantenerlos en el árbol de trabajo era un
riesgo activo:

- **Duplicación de claims/reglas.** Casi todos asignan id con `max(id) + 1` sobre el store cargado:
  re-correr cualquiera inserta el mismo conocimiento otra vez con un id nuevo. El dedupe por `id`
  no lo detecta; el dedupe por contenido no existe.
- **Reescritura de esquema.** `scrp_temp/migrate_claims_evidence_schema.py` reescribe el store
  `claims.json` **entero** (migración `evidence` → `evidence_*` estructurado). Re-correrlo sobre
  claims ya migrados degrada el esquema. Su backup (`claims.json.pre_session054_backup`) es de s054
  y ya no representa el estado actual.
- **Puerta trasera al single source of truth.** Escriben sin validación de ontología, sin gate del
  rebuild, sin trazabilidad de quién escribió qué.

Se movieron con `git mv` — **mover ≠ borrar** (CP-002 preserve-first). La historia de cada archivo
está intacta (`git log --follow <path>`). Se verificó que **ningún módulo vivo los importa**
(grep de `import`/`from` sobre todo el repo `.py`: 0 referencias; `.claude/` hooks y agentes: 0
referencias; `brain_v2/*.py`: 0 referencias).

## (b) La regla

> **El único escritor legítimo de los stores de `brain_v2/` es el `brain-steward`**
> (`.claude/agents/brain-steward.md`): escribe en los stores EXISTENTES, no inventa esquema, y
> dispara el rebuild. **Cualquier script que escriba directo a un store es deuda** y debe archivarse
> acá o refactorizarse para pasar por el steward.

Si necesitás promover conocimiento al brain, invocá el steward. No escribas un `update_brain_X.py`.

## (c) Inventario completo

Método: recorrido AST de `Zagentexecution/**` + `scratch/**` (34 candidatos = `.py` que mencionan un
store core Y llaman `json.dump` / `write_text`), resolviendo el **target real** del dump —
incluyendo el patrón helper `def save(path, data): json.dump(data, open(path,'w'))`, que a simple
vista parece un parámetro genérico pero se resuelve en el call site. Herramienta:
[`_tools/inventory_direct_writers.py`](_tools/inventory_direct_writers.py).

Veredictos: **ESCRITOR_REAL** (el dump aterriza en un store core) · **SOLO_LECTOR** (lee el store,
escribe a otra cosa: companion, reporte, backup) · **AMBIGUO** (no resoluble o no es one-shot).

Resultado: **33 ESCRITOR_REAL movidos · 1 AMBIGUO sin mover · 0 SOLO_LECTOR.**

| Script (origen) | Store(s) que escribe REALMENTE | Veredicto | Destino |
|---|---|---|---|
| `Zagentexecution/incidents/INC-000005240_add_annotations.py` | annotations | ESCRITOR_REAL | `_applied/incidents/INC-000005240_add_annotations.py` |
| `Zagentexecution/incidents/INC-000005240_add_feedback_rules.py` | feedback_rules | ESCRITOR_REAL | `_applied/incidents/INC-000005240_add_feedback_rules.py` |
| `Zagentexecution/incidents/INC-000005240_brain_v2_updates.py` | claims, data_quality_issues, incidents, known_unknowns | ESCRITOR_REAL | `_applied/incidents/INC-000005240_brain_v2_updates.py` |
| `Zagentexecution/incidents/INC-000005240_retag_wrongpath.py` | annotations, claims | ESCRITOR_REAL | `_applied/incidents/INC-000005240_retag_wrongpath.py` |
| `Zagentexecution/incidents/_patch_6906_pivot.py` | incidents | ESCRITOR_REAL | `_applied/incidents/_patch_6906_pivot.py` |
| `Zagentexecution/mcp-backend-server-python/add_session073_rules.py` | feedback_rules | ESCRITOR_REAL | `_applied/mcp-backend-server-python/add_session073_rules.py` |
| `Zagentexecution/mcp-backend-server-python/phase0_brain_update.py` | claims, feedback_rules | ESCRITOR_REAL | `_applied/mcp-backend-server-python/phase0_brain_update.py` |
| `Zagentexecution/mcp-backend-server-python/phase1_brain_companion_update.py` | claims, feedback_rules | ESCRITOR_REAL | `_applied/mcp-backend-server-python/phase1_brain_companion_update.py` |
| `Zagentexecution/mcp-backend-server-python/phase1_final_brain_update.py` | claims | ESCRITOR_REAL | `_applied/mcp-backend-server-python/phase1_final_brain_update.py` |
| `Zagentexecution/mcp-backend-server-python/session075_fill_fpayhx_brain_update.py` | annotations, claims, data_quality_issues | ESCRITOR_REAL | `_applied/mcp-backend-server-python/session075_fill_fpayhx_brain_update.py` |
| `Zagentexecution/mcp-backend-server-python/update_brain_bank_recon_family.py` | annotations, claims, incidents | ESCRITOR_REAL | `_applied/mcp-backend-server-python/update_brain_bank_recon_family.py` |
| `Zagentexecution/py_finance_investigation/add_sfsf_context.py` | claims, known_unknowns | ESCRITOR_REAL | `_applied/py_finance_investigation/add_sfsf_context.py` |
| `Zagentexecution/py_finance_investigation/fix_hr_workflows.py` | claims | ESCRITOR_REAL | `_applied/py_finance_investigation/fix_hr_workflows.py` |
| `Zagentexecution/py_finance_investigation/register_hr_workflows.py` | claims, known_unknowns | ESCRITOR_REAL | `_applied/py_finance_investigation/register_hr_workflows.py` |
| `Zagentexecution/py_finance_investigation/register_incident.py` | incidents, known_unknowns | ESCRITOR_REAL | `_applied/py_finance_investigation/register_incident.py` |
| `Zagentexecution/sap_data_extraction/scripts/delta_refresh_2026.py` | known_unknowns | **AMBIGUO** | **(sin mover)** |
| `Zagentexecution/scrp_temp/add_4_rules_session054.py` | feedback_rules | ESCRITOR_REAL | `_applied/scrp_temp/add_4_rules_session054.py` |
| `Zagentexecution/scrp_temp/annotate_incident_chains.py` | incidents | ESCRITOR_REAL | `_applied/scrp_temp/annotate_incident_chains.py` |
| `Zagentexecution/scrp_temp/backfill_rules_cp_derivation.py` | feedback_rules | ESCRITOR_REAL | `_applied/scrp_temp/backfill_rules_cp_derivation.py` |
| `Zagentexecution/scrp_temp/enrich_dq_items.py` | data_quality_issues | ESCRITOR_REAL | `_applied/scrp_temp/enrich_dq_items.py` |
| `Zagentexecution/scrp_temp/enrich_known_unknowns.py` | known_unknowns | ESCRITOR_REAL | `_applied/scrp_temp/enrich_known_unknowns.py` |
| `Zagentexecution/scrp_temp/enrich_superseded_claims.py` | claims | ESCRITOR_REAL | `_applied/scrp_temp/enrich_superseded_claims.py` |
| `Zagentexecution/scrp_temp/h48_final_brain_update.py` | annotations, claims, known_unknowns | ESCRITOR_REAL | `_applied/scrp_temp/h48_final_brain_update.py` |
| `Zagentexecution/scrp_temp/h48_findings_update.py` | annotations, claims, known_unknowns | ESCRITOR_REAL | `_applied/scrp_temp/h48_findings_update.py` |
| `Zagentexecution/scrp_temp/migrate_claims_evidence_schema.py` | claims (**reescribe el store entero**) | ESCRITOR_REAL | `_applied/scrp_temp/migrate_claims_evidence_schema.py` |
| `Zagentexecution/session074_annotations.py` | annotations | ESCRITOR_REAL | `_applied/session074_annotations.py` |
| `Zagentexecution/session074_brain_claims.py` | claims | ESCRITOR_REAL | `_applied/session074_brain_claims.py` |
| `Zagentexecution/session074_feedback_rules.py` | feedback_rules | ESCRITOR_REAL | `_applied/session074_feedback_rules.py` |
| `Zagentexecution/session075_brain_updates.py` | claims, feedback_rules | ESCRITOR_REAL | `_applied/session075_brain_updates.py` |
| `Zagentexecution/session078_odp_compliance_brain.py` | claims, feedback_rules | ESCRITOR_REAL | `_applied/session078_odp_compliance_brain.py` |
| `Zagentexecution/update_brain_inc6313.py` | claims, data_quality_issues, feedback_rules, incidents, known_unknowns | ESCRITOR_REAL | `_applied/update_brain_inc6313.py` |
| `Zagentexecution/update_brain_inc_budgetrate.py` | claims, feedback_rules, incidents | ESCRITOR_REAL | `_applied/update_brain_inc_budgetrate.py` |
| `Zagentexecution/update_brain_inc_budgetrate_v2.py` | annotations, feedback_rules | ESCRITOR_REAL | `_applied/update_brain_inc_budgetrate_v2.py` |
| `scratch/add_session076_to_brain.py` | claims, feedback_rules | ESCRITOR_REAL | `_applied/from_scratch/add_session076_to_brain.py` |

Nota sobre `from_scratch/`: `scratch/` está en `.gitignore` (línea 143) y el patrón matchea cualquier
directorio `scratch` a cualquier nivel — por eso el destino se llama `from_scratch/`, para que el
archivo quede **versionado** en vez de seguir invisible a git.

## (d) AMBIGUOS — pendiente de verificar

| Script | Por qué queda pendiente |
|---|---|
| `Zagentexecution/sap_data_extraction/scripts/delta_refresh_2026.py` | Escritor real confirmado sobre `agi/known_unknowns.json`, **pero NO es one-shot**: es un script operativo del pipeline de extracción (delta refresh de la Gold DB para FY2026), con `argparse`/`sys.argv`, pensado para re-ejecutarse. Archivarlo rompería el pipeline. **Acción pendiente: refactorizar** para que la escritura de known_unknowns pase por el steward (o emita un artefacto que el steward consuma), en lugar de mover el script. |

### Verificaciones aún no hechas (fuera del alcance de este pase)

- El barrido cubrió `Zagentexecution/**` y `scratch/**`. **No** cubrió escritores directos que
  pudieran vivir en otros árboles (`companions/`, `brain_v2/**` — este último es territorio del
  steward y del `rebuild_all.py`, deliberadamente excluido).
- No se verificó si el contenido que estos scripts insertaron sigue siendo correcto en los stores;
  esta tarea fue sobre los **escritores**, no sobre el **contenido**.

---
_Pase de gobernanza, 2026-07-25. Los 32 renames de archivos versionados quedaron capturados en el
commit `5f87218` (una sesión paralela hizo un commit tipo `add -A` mientras este pase corría);
la historia se preserva igual (`R100` en `git show --name-status 5f87218`)._
