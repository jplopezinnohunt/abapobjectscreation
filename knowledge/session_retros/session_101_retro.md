# Session #101 — Purpose of Payment / Egipto: de especificación a fichero probado

**Fecha**: 2026-08-19 · **Tema**: `INC-EGYPT-PPC` (ticket real `INC-000016101`), deadline Citi 2026-09-05
**Commits**: `81b0baa`, `06e5244`, y el de cierre
**Auditoría Phase 0**: `session_101_retro_audit.md` — veredicto inicial **FAIL**, 8 bloqueantes. Este retro se escribe *después* de resolverlos.

---

## 0. Qué se pedía y qué pasó realmente

La petición era doble: reabrir el tema con el protocolo de apertura y recuperar los dos companions. Lo que apareció al mirar el sistema fue otra cosa: **la configuración ya estaba construida en D01 esa misma mañana, por el usuario, y se desviaba de la especificación en cinco puntos** — uno de ellos daño colateral a un país que no tenía nada que ver.

La sesión dejó de ser "recuperar contexto" y pasó a ser "verificar lo construido, corregirlo y probarlo". Terminó con un fichero `pain.001` real conteniendo la cadena esperada, carácter por carácter.

**Resultado técnico**: el control queda probado por las dos mitades. Bloquea sin código (`ZFI-036`, `GB931` UNES paso 012) y renderiza con código (`<Ustrd>/Payment for goods or services received/INV/224938`). Cero ABAP, confirmado por ejecución y no por lectura de fuente.

---

## 1. Las cinco cosas que merecen sobrevivir a esta sesión

### 1.1 El cerebro te da la LÍNEA BASE. Sólo el sistema te da el ESTADO.

El protocolo de apertura funcionó: `BRAIN_INDEX` → `load_domain.py "purpose of payment"` → 79 partes, ~688K tokens, dos companions, el incidente, los claims. Eso me dio la especificación de la sesión 99 con precisión.

**Y no me habría dicho jamás que esa especificación ya estaba superada por los hechos.** Lo que discriminó fue leer D01 en vivo y diferenciarlo contra P01. Sin esa lectura habría pasado la sesión explicando un plan que la realidad había dejado atrás hacía horas.

La regla #208 dice *"el índice orienta, no da competencia"*. Su hermana, que faltaba: **incluso una carga de dominio completa te orienta sobre el pasado. El presente hay que leerlo.** Toda revisión de un cambio empieza por leer el sistema, no por leer lo que dijimos del sistema.

### 1.2 El diff que ve el daño colateral es el de la TABLA ENTERA

Configurando Egipto en `SM30` se borró el separador `/` de `YTFI_PPC_STRUC ID/USTRD/O/01` — **Indonesia** — y esa clave quedó dentro del transporte de Egipto. Liberado así, cambiaba el fichero de Bank Indonesia sobre 921 líneas con código de propósito.

**Ninguna revisión centrada en "¿está Egipto bien configurado?" lo habría visto**, porque Egipto estaba bien. Lo vio el diff de las tres tablas completas D01 vs P01, que devolvió exactamente una deriva ajena.

Matiz que hay que saber: un transporte de tabla guarda la **clave** y exporta el **valor al liberar**. Por eso restaurar el valor neutraliza el daño aunque la clave siga dentro — pero deja al vecino *acoplado* al transporte hasta la liberación.

→ Mecanizado: `Zagentexecution/quality_checks/config_transport_prerelease_check.py <TRKORR>`. Clasifica VIAJA / INTRUSA / NO-OP / DERIVA y falla si hay una clave de entidad ajena. Regla `feedback_diff_the_whole_table_before_releasing_a_config_transport` (CRITICAL). Claim 526.

### 1.3 Tres defectos en un día, invisibles en pantalla, cazados por el mismo instrumento

| Defecto | Qué habría salido al banco |
|---|---|
| Los seis `SEPARATOR` vacíos | `Payment for goods or services receivedINV5105551234` — todo pegado |
| Separador puesto como un espacio | lo mismo: `PPC_VALUE` es `CHAR(60)` y el blanco final **es** el relleno |
| `T015L EG4` = `OTHR··Others` (dos espacios) | `/ Others/INV/…` — un blanco suelto tras la barra |

Los tres parecían correctos en `SM30`. Los tres los cazó `RFC_READ_TABLE` **sin `.strip()`**, contando blancos delante y detrás.

La regla de fondo no es sobre PPC: **un blanco final no se puede almacenar en un campo `CHAR`; uno inicial sí.** Por eso la separación puede ir *delante* de cualquier literal y nunca *detrás*, y por tanto nunca justo antes de un `PAY_FIELD`, que es dinámico y no admite prefijo.

→ Regla `feedback_a_char_field_cannot_store_a_trailing_blank` (HIGH). Claim 524.

### 1.4 La mecanización se pagó sola en su primera ejecución

Los checks **E** y **F** añadidos a `ppc_country_consistency_check.py` no se escribieron para buscar nada: se escribieron para que el defecto encontrado a mano no volviera. En la primera corrida encontraron **un defecto vivo en P01**:

```
T015L  INA  ZWCK1 = 'P1203  Maintenance of international institutions such as offices of IM'
                          ^^ dos espacios
India separa con ';'  →  P1203; Maintenance of…;INV;<XBLNR>
```

Única fila rota de las 73, esperando en producción desde que se configuró India. Nadie la buscaba. Claim 529.

Esto es el argumento más fuerte de la sesión a favor de *promover a check* en vez de *anotar la lección*: la nota habría protegido a Egipto; el check protegió a India.

### 1.5 Predecir la salida ANTES de generarla es un instrumento, no una floritura

Antes de lanzar el F110 se simuló `CM003`/`CM004` sobre las filas leídas en vivo y se publicó la cadena esperada. El fichero trajo exactamente esa cadena.

Eso valida **dos cosas y las separa**: que la configuración es correcta, y que nuestro modelo del código es correcto. Si hubieran diferido, la diferencia habría dicho cuál de las dos fallaba — información que "leer el fichero y ver si tiene buena pinta" no da nunca. Y la misma simulación, corrida antes, es la que hizo visibles los separadores vacíos.

→ Regla `feedback_predict_the_output_before_you_generate_it` (HIGH). Claim 527.

---

## 2. Lo que hice mal

Sin esto el retro es propaganda.

### 2.1 Ascendí un riesgo por herencia, sin medirlo

El companion decía *"lo único que no hay que copiar: la R que falta"*. Lo repetí marcándolo en **rojo** como *"lo único que hoy rompería"*. El usuario preguntó lo correcto: *"¿dónde tenemos R en otro país que justifique ponerlo?"*.

Medido: en `REGUH` completa (3.707.737 líneas, 2016-2026, ejecutadas), `HR-PY` 180.372 y `TR-CM-BT` 713, y **ninguna llega a ninguno de los diez países**. Los seis países que sí tienen filas `R` no las han disparado nunca.

El aviso del companion tampoco se había medido jamás. Yo lo convertí en crítico por transmisión. **Coste real**: gastar atención del usuario en lo que no pasa, mientras lo que sí importaba — avisar a El Cairo de que el bloqueo empieza el día del transporte — no estaba en ninguna lista hasta el final.

→ Regla `feedback_a_warning_in_a_document_is_not_a_measurement` (HIGH). Claim 528.

### 2.2 Escribí un check que informó OK estando roto

`config_transport_prerelease_check.py`, primera versión: troceaba el `TABKEY` de `E071K` usando `INTLEN` (longitud interna Unicode, 2 bytes por carácter) en vez de `LENG`. Ninguna clave del transporte casaba con las de la tabla, así que **todo salió NO-OP y el check dijo OK** — sobre el mismo transporte cuyo defecto acababa de encontrar a mano.

Es exactamente el modo de fallo contra el que existe el check. Lo detecté porque la salida *parecía* rara, no porque el check lo dijera. Corregido, y añadida una autocomprobación: si ninguna clave del transporte existe en ninguno de los dos sistemas, aborta con error en vez de informar OK.

### 2.3 Violé una regla escrita ese mismo día porque no leí el store antes de escribir en él

Reescribí `claims.json` con `indent=1` y generé un diff de 27.000 líneas para tres claims. Existía ya `feedback_read_the_store_before_writing_to_it` (CRITICAL, creada horas antes en otra sesión) que documenta **exactamente** ese error, y un `store_schema_check.py` que lo detecta. No los leí. Lo corregí al ver el diff, no al escribir.

### 2.4 Dejé el conocimiento contradiciéndose, y no lo vi yo

La auditoría Phase 0 encontró que `claims.json` y `incidents.json` **discrepaban sobre el estado actual de D01**: el claim 526 seguía afirmando que el separador de Indonesia estaba borrado y que `SALA` estaba en la lista, cuando ambas cosas se habían arreglado horas antes. Y el claim 527 tenía un `resolution_notes` que contradecía su propio cuerpo.

Escribí el registro cuando descubrí el problema y **nunca volví a él cuando el problema se resolvió**. Un claim no es un acta de lo que vi; es lo que la próxima sesión creerá.

Igual con los dos companions: el usuario tuvo que decírmelo — *"parece que no lo hiciste"* — y tenía razón. Seguían diciendo `SPEC_READY` y *"the one thing still unproven"* cuando el fichero ya existía.

### 2.5 Detalles menores, dichos para no barrerlos

- Dije que el indicador SCB estaba en la pestaña *Payment* de FB60. Está en **Details**. Afirmé conocimiento de UI que no había verificado.
- Expliqué la pérdida del blanco final culpando a la plantilla de string ABAP. La razón real es el relleno del `CHAR`. Misma acción, mecanismo equivocado.
- Tres fallos de comillas escribiendo Python inline en bash antes de pasarme a `Write`.

---

## 3. El hallazgo del auditor que más duele, y es el mejor

`knowledge_reachability_check.py` **sale con código 0** mientras el índice que vigila es materialmente engañoso. Comprueba que el `id` aparezca en el índice; **nunca comprueba que lo que el índice dice sea actual**. Durante toda la sesión el índice decía `SPEC_READY` y proponía un plan equivocado en tres puntos, y el guardián lo daba por bueno.

Es el patrón del claim 496 — *"el control prueba presencia, no corrección"* — **reproducido dentro de nuestro propio instrumental**. Encontramos ese defecto en el código de SAP y lo tenemos en el nuestro.

No se ha arreglado en esta sesión. Queda como acción.

---

## 4. Estado al cierre

**Egipto**: configurado en D01, probado por las dos mitades, transporte `D01K9B0FXE`/`D01K9B0FXF` **sin liberar**.

Abierto, y nada de ello es técnico:

| # | Qué | Quién |
|---|---|---|
| 1 | Partir el transporte en dos antes de liberar; quitar la clave `350ID USTRD O01` | FI config |
| 2 | Avisar a El Cairo: el bloqueo empieza el día del transporte, 716 proveedores afectados | BFM |
| 3 | Confirmar los cinco motivos y su redacción | BFM / CitiService |
| 4 | Arreglar `T015L INA` en P01 (claim 529) | FI config |
| 5 | Opcional: tipo de pago `R` — medido cero tráfico en 10 años | — |

**Promovido**: claims 524-529 · 4 reglas nuevas · 2 checks nuevos (`config_transport_prerelease_check.py`, y E/F en `ppc_country_consistency_check.py`) · los dos companions actualizados con la evidencia · `MEMORY.md` corregido · artefacto `pain.001` archivado.

---

## 5. Phase 4b — Qué aprendimos sobre SAP

1. **`YCL_IDFI_CGI_DMEE_UTIL->BUILD_VALUE` concatena sin separador implícito.** `ev_value_c = |{ iv_value_c }{ iv_value_to_add }|`. Un `SEPARATOR` vacío no separa: pega.
2. **`SPLIT ... AT space INTO a b` asigna al último destino el resto *incluyendo los separadores*.** Por eso dos espacios en `ZWCK1` meten un blanco al principio de la narrativa.
3. **El nodo `<Ustrd>` de `/CGI_XML_CT_UNESCO` (`N_6995550560`) lleva `MP_EXIT_FUNC = FI_CGI_DMEE_EXIT_W_BADI`** y admite `LENGTH=140`. `DMEE_TREE_NODE` rechaza un `WHERE` por sus columnas string: se lee entera y se filtra en Python.
4. **Los dos países del mecanismo son observables en el fichero**: `DbtrAgt/BIC` (el nuestro) elige la clase, `CdtrAgt/Ctry` (el suyo) elige las filas.
5. **`GB931` no tiene campo `BOOLCLASS`** — está en `GB93`. Y D01 y P01 tienen validaciones idénticas: `UNES`, 12 pasos, el 012 es purpose of payment.
6. **La validación `UNES` obliga a `GSBER ∈ {GEF, MBF, OPF, PFF}`** (paso 001, `ZFI-015`) y a rellenar `BVTYP` (paso 011, `ZFI-012` = `U915`).
7. **El método de pago `N` está atado a `/CGI_XML_CT_UNESCO`** en `T042Z` país FR, con `XEIPO='X'` en `T042E` para UNES.
8. **`RFC_READ_TABLE` falla con `TABLE_WITHOUT_DATA` cuando un campo del `FIELDS` no existe** — no con un error de campo. Un `WHERE` sobre un campo más corto que el valor da `SAPSQL_DATA_LOSS` (pasó con `E071K.OBJECT`, CHAR(4)).
9. **Un replay (`ZSAPFPAYM_REPLAY`) sólo puede probar fontanería, nunca contenido**: los pagos antiguos llevan `LZBKZ` vacío, así que `PPC_DESCR` no emitiría nada.

---

## 6. La pregunta incómoda

La sesión produjo trabajo técnico sólido y una gestión del conocimiento mediocre hasta que dos cosas externas la corrigieron: **el usuario**, que notó que los companions no estaban actualizados, y **un auditor fresco**, que encontró los claims contradiciéndose.

Sin ninguno de los dos, el cierre habría dejado un cerebro que se contradice a sí mismo sobre el estado de un sistema productivo, once días antes de un deadline regulatorio.

La conclusión no es "hay que revisar mejor". Es que **actualizar el registro cuando el hecho cambia tiene que ser parte de arreglar el hecho, no una fase posterior** — porque la fase posterior es exactamente donde se pierde.
