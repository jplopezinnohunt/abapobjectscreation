# Learning Asset — Recuperar objetos borrados/rotos en D01 por Transport of Copies desde V01

> **Cuándo usar:** un objeto custom (clase, programa, función, DDIC…) quedó **borrado o roto en D01**
> (ej. TADIR presente pero sin definición) y existe **sano en V01** (u otro sistema del mismo dominio de
> transporte). Recuperás trayéndolo por **Transport of Copies**, sin escribir código a mano y sin ADT write.
>
> **Probado:** 2026-06-12, INC-CLASS-LOSS — 3 clases FI recuperadas (TR `V01K910259`). Ver "Ejemplo trabajado".
> Promovible a skill (`sap_object_recovery`). Regla origen: nunca recuperar con el canal que causó el daño.

---

## 0. Principios
- **Recuperar SOLO por mecanismos SAP nativos y trazables** (transport of copies / version management).
  **NUNCA** `write_source`/`deploy`/ADT ad-hoc ni `RFC_ABAP_INSTALL_AND_RUN` — son los canales que rompen.
- **GUI la hace el operador, la verificación la hace el agente por RFC read-only.** Los FMs de transporte
  (`TR_*`, `TMS_*`) **no son RFC-enabled** → no se automatizan por RFC sin caer en ABAP arbitrario.
- **Distinguir daño real vs borrado legítimo previo** con un baseline pre-incidente (ej. TS2) ANTES de recuperar.

## 1. Decisión de alcance — ¿qué recuperar?
Usá un **sistema baseline anterior al incidente** (una copia de D01; ej. TS2 = "TEST UPGRADE"):
- **Sano en el baseline + roto en D01 = daño a recuperar.**
- **Ausente/roto en el baseline también = "borrado real"** (deleción legítima previa, NO recuperar; el
  TADIR-huérfano es pre-existente).
> Cuidado: un objeto "tocado" por el incidente que **ya estaba borrado** antes (errores `ResourceNotFound`)
> NO es daño tuyo — no lo recuperes.

## 2. Elegir la FUENTE por DOMINIO de transporte (no solo por salud)
El objeto puede estar sano en varios sistemas, pero la fuente debe estar en el **mismo dominio de transporte
que D01** para que el import sea directo.

```python
# RFC read-only: ¿qué sistemas conoce cada sistema en su dominio?
rt(conn, 'TMSCSYS', ['SYSNAM','SYSTXT','DOMNAM'], '')   # buscar D01 en la lista
# Resultado real: V01 -> DOMAIN_P01 (incluye D01,P01,TS1,TS3,V01...) => D01 conocido  ✅
#                 TS2 -> DOMAIN_TS2 (aislado)                         => D01 NO conocido ❌
```
- **V01 (DOMAIN_P01)** entrega a D01 directo (mismo dominio, mismo directorio de transportes). **Fuente preferida.**
- **TS2 (DOMAIN_TS2 aislado)** → al crear la TR da *"Target D01 unknown in transport configuration"* y NO
  entrega sin que Basis mueva archivos. Solo sirve como **baseline**, no como fuente.

## 3. Procedimiento — Transport of Copies V01 → D01

### PARTE A — Crear la TR (en V01, GUI)
1. SAP GUI → **V01** ("02 - V01"), client 350.
2. Transacción **`SE09`** (⚠️ **NO** la pestaña *Deliveries* de SE01 — esa da "Delivery Transport (Upgrade/OCS)",
   que no sirve).
3. **Create** (hoja en blanco / F6) → popup "Create Request" → radio **"Transport of Copies"** → check verde.
4. **Short Description** + **Owner** (vos) + **Target = `D01`** (sin warning, porque V01 conoce D01) → Guardar.
   → número **`V01K9xxxxx`**.

### PARTE B — Agregar objetos (en V01)
5. En la TR → pestaña **Objects** → insertar una fila por objeto: `PgmID` `R3TR` | `Object` `<tipo>` | `Object Name`.
   - Tipos comunes: `CLAS` (clase), `PROG` (programa), `FUGR` (grupo func.), `INTF` (interface), `TABL`/`DTEL`/`DOMA` (DDIC).
   - `R3TR <tipo> <nombre>` arrastra todos los subobjetos. Guardar.
   - Alternativa: SE80 mostrar el objeto → click derecho → *Write transport entry* → elegir la TR.

### PARTE C — Release (en V01)
6. SE09 → seleccionar la TR → **Release Directly** (camión / Ctrl+F3). Esperar export (log con RC(0)).
   → graba la **versión actual sana de V01** en el transporte.

### PARTE D — Import (en D01, GUI) — ⚠️ los 2 detalles que rompen o salvan
7. SAP GUI → **D01** → **`STMS`** → *Import Overview* → doble click **D01** → *Import Queue*.
8. La TR aparece sola en la cola (mismo dominio). Si no: *Extras → Other Requests → Add* → número → Add.
9. **Seleccionar SOLO tu TR** (no "Import All Requests" — la cola puede tener SPAU/upgrade de terceros con RC rojo).
10. **Import Request** (F11):
    - **Target Client = `350`**.
    - Pestaña **Options → ✅ `Overwrite Originals`** ⚠️ **CRÍTICO.** El objeto es **original de D01** (su home
      system) → sin este flag el import lo **saltea en silencio** (RC 0/4 pero NO restaura). Con el flag,
      reescribe la definición rota con la versión buena.
    - (Opcional: `Ignore Invalid Component Version` si se queja por versión.)
    - Date: Immediate. Confirmar (RC 4 amarillo = warning esperado de overwrite = OK).

### PARTE E — Activación
11. El import suele dejar el objeto **activo** (verificá; si no, SE80/SE24 → Activate).

## 4. Verificación (RFC read-only — el agente)
```python
# Por objeto: ¿volvió y está activo? (ejemplo para CLAS)
SEOCLASS  -> existe (CLSNAME)
SEOCOMPO  -> nº de componentes == baseline (V01)         # métodos/atributos
SEOCLASSDF-> VERSION=1, STATE=1 (activo), CHANGEDON=hoy   # versión del import encima
# Comparar método por método contra la fuente: ver verify_recovery.py (compara V01/TS2 vs D01).
```
- Historial de versiones: el borrado de la definición **NO borra el historial** (VRSD sobrevive en D01) →
  al restaurar la versión activa, SE80 → Versions vuelve a mostrar las versiones previas. El import añade 1
  versión nueva encima. **No hay que recuperar versiones aparte.**

## 5. Conexión RFC (referencia, read-only para verificar)
| SID | host:sysnr | dominio | gateway pyrfc | nota |
|---|---|---|---|---|
| D01 | 172.16.4.66:00 | DOMAIN_P01 | :4800 | destino |
| V01 | hq-sap-v01:00 | DOMAIN_P01 | :4800 | fuente |
| TS2 | hq-sap-ts2(172.16.4.82):00 | DOMAIN_TS2 | **:3300** (no :4800) | baseline; `gwhost=hq-sap-ts2 gwserv=3300` |

Auth = SNC/SSO (`snc_mode=1`, `snc_partnername=p:CN=<SID>`, `snc_qop=9`). Vars en `.env` (`SAP_<SID>_*`).
`RFC_READ_TABLE`: líneas de OPTIONS ≤ 72 chars (partir el WHERE en `AND`). `REPOSRC` no es legible por RFC.

## 6. Lecciones (gotchas reales)
1. **`Overwrite Originals` es obligatorio** al re-importar a su home system; sin él, el import saltea sin avisar.
2. **Elegí la fuente por dominio** (`TMSCSYS`), no solo por salud. Cross-domain (TS2) = "target unknown" = no entrega.
3. **SE09**, no la pestaña Deliveries de SE01.
4. **Importá solo tu TR** (no toda la cola).
5. **SE24/SE80 version-retrieve NO sirve** para una clase totalmente borrada (no la abre) → transport.
6. **El historial (VRSD) sobrevive** a la deleción de la definición.
7. Los **FMs de transporte no son RFC-enabled** → no automatizar; GUI + verificación RFC.
8. **TS2 por RFC** necesita `gwserv=3300`.

## 7. Ejemplo trabajado — INC-CLASS-LOSS (2026-06-12)
Recuperadas 3 clases FI (daño nuestro; 11 más eran "borrado real" pre-existente, no tocadas):
`YCL_FI_ACCOUNT_SUBST_BL` (32 métodos) · `YCL_FI_ACCOUNT_SUBST_READ` (1) · `YCL_FI_BANK_RECONCILIATION_BL` (54).
TR `V01K910259` (Transport of Copies, V01→D01, Overwrite Originals, client 350). RC 4 = OK. 3/3 activas,
historial intacto (BANK v0-8). Registro paso-a-paso + **pantallas**:
`Zagentexecution/tasks/2026_06_12_class_loss_recovery/EXECUTION_LOG.md` (+ `screenshots/`, `verify_recovery.py`).
Incidente: `knowledge/incidents/INC-CLASS-LOSS-2026-06_adt_rfc_write_corruption.md`.
