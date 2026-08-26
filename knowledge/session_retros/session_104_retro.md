# Sesión 104 — 2026-08-26 · INC-000016338 (UIL / panel de firmantes BCM)

**Forma:** caso de soporte Track B (acción operativa) que acabó siendo, sobre todo, una sesión de
**mejora del modelo**. Tercera ocurrencia del escenario "panel de firmantes", la primera con el skill
`sap_bcm_signatory_maintenance` ya escrito.

---

## 1. El caso, en una línea

Añadir a Bettina REISS al panel de UIL "y sus límites bancarios". Se hizo el alta **y** se construyó el
tramo ≤10.000 en las dos reglas. Verificado por `Simulate rule resolution`: **10.000 → 6 aprobadores,
10.001 → 4**. Bloquea el cierre el rol `BNK_APP` de `B_REISS`.

---

## 2. Lo que estuvo bien

- **El coordinador de herramientas fue el momento de más apalancamiento, y costó un comando.**
  `graph_queries.py tool` enrutó a `sap_bcm_signatory_maintenance`; sin él habría acabado en
  `sap_payment_bcm_agent` — 106 KB de F110/FBZP, ninguno de firmantes.
- **El barrido pagó otra vez.** El ticket pedía dos filas; salieron tres hallazgos que nadie pidió:
  Basoglu **dos años sin tope**, Yli-Hietanen **31 meses fuera en dos entidades**, Reiss sin rol.
- **Verificar antes de alarmar**: el susto de "incidentes 16 → 14" era un test mío mal planteado.
- **No recrear las 3 filas borradas** de `HRP1001`: fabricar historia es peor que perderla.
- **ADR-008 aguantado cuatro veces** sin commitear a mitad de rebuild, pese a la insistencia del hook.
- **No hacer `push`** sin que lo pidiera el operador.
- **Re-examinar al ser discutido** en vez de defender — eso es lo que llevó a la simulación.

## 3. Lo que estuvo mal — y es **un solo fallo, repetido cinco veces**

| Afirmé | Lo refutó | Coste |
|---|---|---|
| Las bandas deben ser disjuntas | `Simulate rule resolution` | **horas**, y casi un cambio que quitaba autorización a 4 firmantes |
| El check de reconciliación es asimétrico | leer 40 líneas de Python | diagnóstico invertido, llamado "la deuda de más valor" |
| Progreso: *"TERMINADO 7/7"* | el fichero de background en 0 bytes | casi se reporta como hecho |
| `backup_location.json` no existe | `git status` | ruido |
| `algorithms.json` son 84 claves raíz | contar tras escribir | clave en el nivel equivocado |

**El patrón: afirmar por inferencia con la medición a un comando de distancia.** El simulador existía,
el código del check existía, el estado del proceso existía, el fichero existía, la estructura existía.

Y dos de disciplina: **incumplí la regla de referencias cruzadas del propio proyecto** (el `SKILL` decía
"nodo único" después de documentar cuatro nodos) y **lancé un proceso de 45 min con `| tail`**,
cegándome 40 minutos.

---

## 4. Phase 4b — QUÉ APRENDIMOS DE SAP

1. **La determinación de agentes BCM devuelve la UNIÓN** de todos los nodos que encajan, y el borde de
   banda es **inclusivo** (10.000,00 abajo, 10.001,00 arriba). Depende de que `Priority` de `OOCU_RESP`
   esté vacía. **Claim 612.** Esto es lo que hace válido un solape de bandas.
2. **Quién firma se decide en TRES niveles encadenados**: regla de agrupación (`TBNK_RULE`) → selección
   de nodo (IT1218) → procedimiento (`TBCA_RELPROC_*`). Los niveles 1 y 3 **no son legibles por RFC** con
   el usuario SNC: se leen del Gold. **Claim 609.**
3. **La aridad de la regla de agrupación difiere por entidad**: UBO 4 criterios y UIS 3 (los dos con
   `AMT_RULECU`), **UIL sólo 2 y sin importe** — y es su única regla. En UIL la banda del nodo es la
   **única** discriminación por importe que existe.
4. **`AMT_RULECU` se guarda NEGATIVO** (`'10000.00-'`): `GT -10000` significa *hasta 10.000*. Leer
   `GT`/`LE` sin ver el signo **invierte la regla**.
5. **`T042A` está VACÍA en P01.** El gate de completitud del runbook apuntaba a una tabla inexistente;
   el universo real es `T012K` + `T042I`. `BNK_BATCH_HEADER` tampoco es legible por el usuario SNC.
   *(Contradicción abierta: `DQ-2026-063-04` dice que sí se consultó en s63 — reabierto `needs_review`.)*
6. **El panel y sus nodos se mantienen en P01 y NO generan transporte** (claim 611). Un cambio en quién
   puede liberar dinero se hace en producción **sin transporte, sin ATC, sin cuatro ojos técnicos y sin
   rastro auditable**. El único control es el proceso documental + el readback: por eso el readback no
   es opcional.
7. **Dos patrones de tramo válidos conviven** (claim 613, `DESIGN_DECISION`): UBO disjunto con panel alto
   subconjunto; UIL solapado con el nodo bajo conteniendo sólo a los limitados. **Decisión del operador**,
   por legibilidad contra el cartón. **No armonizar UIL hacia UBO**: quitaría a los cuatro sin tope los
   pagos <10.000.
8. **Se borraron 3 filas de `HRP1001`** en vez de delimitarlas, incluida la de Basoglu de 2024-09-27. El
   rastro *en SAP* de sus 23 meses sin tope ya no existe. Detectado cuadrando el conteo del Gold
   (269 esperadas → 266), no por una alerta.

---

## 5. Lo que se mecanizó, y qué habría cazado

| Mecanismo | Habría cazado |
|---|---|
| `bcm_band_consistency_check.py` — razona por **tramo efectivo** (unión), no por nodo, así que vale para los dos patrones | Yli-Hietanen en los 4 tramos, el hueco de `BEGDA`, y el quórum de doble control |
| `rebuild_progress.py` (+ `A48`) | los 40 minutos de "sigue corriendo" sin saber por dónde |
| **2.ª parte de `artifact_wiring_check.py`** — instrumentos **sin artefacto**, que contestan en pantalla | que `rebuild_progress.py` quedara descolgado del toolgraph **para siempre** |
| **Triángulo en `incident_record_coverage_check.py`** — brief + referencias bidireccionales | que aterrizara 6 claims con el companion desfasado y sin brief |
| 3 reglas nuevas: `simulate_before_deciding_the_shape` · `delimit_never_delete_pd_infotype_row` · `a_long_process_must_be_able_to_report_its_own_progress` | los tres fallos de arriba |
| 2.ª mitad de `at_incident_close_check_for_related_domain_knowledge`: **ajustar el detector** | el `SKILL` diciendo "nodo único" |
| 4 agentes actualizados: `bcm-signatory-panel`, `authority-doc-reader`, `incident-analyst`, `brain-steward` | que el próximo caso rehaga el análisis de hoy |

**Lo que se decidió NO mecanizar:** un lint de "claim que afirma un negativo sobre nuestras herramientas
debe citar su salida". Detectarlo por palabras clave es frágil y el ruido es cómo mueren los checks. Vive
mejor como regla (la de contrastar) que como código malo.

---

## 6. La lección de la sesión

**Anotar → mecanizar → contrastar.** Tres escalones, no dos.

- **Anotar** deja el conocimiento; depende de que alguien lo lea. *La regla de delimitar-nunca-borrar
  estaba escrita en el skill y se violó igual.*
- **Mecanizar** lo hace consultable; depende de que el mecanismo sea correcto. *La v1 de
  `rebuild_progress` mintió con autoridad.*
- **Contrastar** contra una señal que no comparta el fallo es lo único que impide **automatizar el error
  y darle autoridad**.

Las cinco equivocaciones de la sesión las cazó una señal independiente, **ninguna un razonamiento mejor**.

Corolario medido: **un check puede pasar en verde con el defecto vivo si mide la FORMA y no el EFECTO.**
`artifact_wiring_check` daba `HUÉRFANOS: 0` con la herramienta descolgada, e
`incident_record_coverage_check` daba verde con el companion desfasado. Los dos eran correctos en lo que
medían.

---

## 7. Estado al cerrar

**Brain:** 4.562 objetos · 612 claims · 246 reglas · cobertura 100% · `blind_spots` 0. Desbloqueado —
llevaba sin poder reconstruirse desde s103 (4 dominios no declarados; resuelto **declarando**, no
reescribiendo claims).

**Gates:** `incident_coverage` 0 · `ontologia` 0 · `cableado` 0.

**Abierto:** rol `BNK_APP` de `B_REISS` (bloquea el cierre del incidente) · correo a Ingrid con las 4
preguntas a TRS · plazo del AO **2026-09-03** · 16 commits sin subir · backup `--claude-only` pendiente
de reconectar `D:` · PMO H127–H132.

**Sin retro:** la sesión **103** tampoco dejó el suyo. No es excusa de ésta, pero es un hueco.
