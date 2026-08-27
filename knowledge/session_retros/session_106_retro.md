# Sesión 106 — RoleManagement, y el día que los instrumentos se midieron a sí mismos

**Fecha:** 2026-08-27 · **Tier:** 0 (cero escrituras en SAP) · **Commits:** 26
**Entrada:** *"lee el skill de role management de otro proyecto y haz tus propias investigaciones"*

---

## 1. El caso, en una línea

Leer un skill ajeno destapó un sistema externo que no estaba en nuestro mapa — y perseguirlo
acabó destapando que **cuatro de nuestros propios instrumentos afirmaban cosas que su
evidencia no podía sostener**.

---

## 2. LA PREGUNTA QUE HAY QUE CONTESTAR: ¿cómo se resolvió algo que no sabíamos?

El dueño pidió leer `crp/unesdir-role-management` (proyecto `unescrp`). De ahí salió que
**RoleManagement (RM) es un sistema externo con el que SAP se integra y que no figuraba en
nuestro inventario de interfaces** — no es UNESDIR, son servicios hermanos.

La cadena que lo resolvió, y ninguna pieza sobraba:

1. **Leer el skill ajeno** → RM existe, 13 roles, SOAP, llamado por `CallUnesdir` desde D01.
2. **Cruzar contra nuestro `interface_boundary`** → el host aparecía… clasificado `DEAD`.
3. **Leer el instrumento, no su salida** → correlaciona contra el log de auditoría **RFC**, y
   una llamada `cl_http_client` no es RFC. **38 veredictos sobre evidencia ciega.**
4. **Lanzar agentes** → `Explore` encontró el ABAP: el workflow de facturas FI también llama
   a RM. **Segundo consumidor**, fuera de CRP.
5. **Probar P01 en vivo** → los objetos existen; la traza que lo mediría está **apagada**.

**Lo que no sabíamos y ahora sí:** RM tiene al menos dos consumidores, uno de ellos el
workflow que libera pagos; y el nombre del FM (`..._UNESDIR`) **miente sobre su propia
dependencia**.

---

## 3. LO QUE ESTUVO BIEN — y por qué, mecánicamente

- **Deduplicar contra la research cerrada antes de investigar.** El dueño pidió *"haz deep
  research si hace falta"*. No hizo falta: `w3t7ufrbg_process_mining_objectcentric` ya estaba
  `CLOSED_VERIFIED` y contestaba de lleno. Se ahorró una investigación entera **porque la
  regla dice mirar primero**.
- **Separar lo verificado de lo refutado.** De esa research sobrevivieron 4 claims de 102;
  **21 fueron refutados** y no se citaron, por muy útiles que sonaran.
- **El grupo de control convirtió sospecha en prueba.** La traza `WF_PAYMENT` tenía 0 filas.
  Sus dos hermanas estaban `ACTIVE='X'` con 594 y 197. Sin ese contraste, "0" habría sido
  "no se usa" por cuarta vez en el día.
- **Los agentes se negaron a publicar lo que no sostenían.** `miner-onboarding` mató un
  hallazgo de **383 M USD** aparentemente parados en la puerta BCM: mismo día de alta y
  cambio, reparto uniforme en dos años, misma regla que los que sí terminan. Era una regla
  de reparto sin declarar, no un atasco.

---

## 4. LO QUE CASI SALE MAL — la parte que enseña

**El alias que da cero, tres veces, en un solo día, por el agente que lo predicaba.**

| # | Qué hice | Qué era |
|---|---|---|
| 1 | Grep de `BANK_SIGNATORY` → 0 hits → abrí un KU de "cuarta fuente de autoridad" | Hueco de **clave**, no de conocimiento: la firma bancaria es SAP estándar |
| 2 | Publiqué **"5 referencias rotas"** en `process_map` | Alias **declarados**. Canonicalicé solo una de tres fuentes |
| 3 | Iba a "corregir" `parent: Treasury_EBS` | Es la clave canónica **correcta** |

Dos de esos tres llegaron al dueño antes de retirarlos. Y `brain_v2/canonical.py` existía
desde s097 con `same(a, b)` — **la función exacta que lo impedía** — y su docstring dice
literal: *"Fixing a recurring defect three times is not fixing it… Import it; do not
re-derive it."* Tres veces en s097, tres más aquí.

**No fue falta de conocimiento: fue no alargar la mano.**

---

## 5. DEFECTOS DE NUESTROS PROPIOS INSTRUMENTOS, encontrados al usarlos

Todos comparten forma: **un instrumento que afirma fuera de lo que su fuente cubre.**

| Instrumento | El defecto | Estado |
|---|---|---|
| `interface_boundary.py` | Llamaba `DEAD` a 38 destinos HTTP; su fuente solo ve RFC | **Arreglado** — cubo `UNOBSERVABLE`, claim 620 / H134 |
| `build_skill_registry.py` | `cubre_tablas` no contenía tablas → **302 aristas eran 83** | **Arreglado** — deriva de TADIR, claim 622 |
| `agent_trace_hook.py` | 547 filas con un agente falso `"(unspecified)"` | **Arreglado** — `agent: null` + `payload_keys` |
| El lector de ese trace | **No existía**, aunque el docstring lo declaraba | **Escrito** — 556 filas sin lector desde s099 |
| `process_map` | Tres fuentes del eje de proceso, **las 7 discrepaban** | **Reconciliado** por unión + puerta nueva |
| `braintoolbox.yaml` | No parsea como YAML; su puerta lee con regex y no lo ve | **H138**, sin arreglar |

Y los que me cazaron **a mí mientras los escribía**: mi puerta nueva declaró un `tier` que
no existe; mi check de agentes reportó "0 sin atribuir" habiendo 547; mi lint contó código
de pip como deuda nuestra. Los tres, denominador o centinela mal declarado.

---

## 6. PHASE 4b — QUÉ APRENDIMOS DE **SAP**

1. **RM es infraestructura de resolución de actores, no una cosa de CRP.** Dos consumidores
   medidos: la app CRP (D01/ZCRP) y el **workflow FI de liberación de pago**
   (`WS90000003` → regla `90000001` → `Z_GET_CERTIF_OFFICER_UNESDIR` → proxy SOAP
   `LP_ROLE_MGT`). Fallback: `ZFI_PAYREL_EMAIL`, **2 filas**.
2. **El nombre de un objeto ABAP puede mentir sobre su dependencia.** Todo el código FI
   etiqueta `UNESDIR` lo que es **RM**. Discriminador técnico: UNESDIR entra por DBCON/SQL;
   esto es proxy SOAP con puerto lógico. Buscar consumidores de RM por el nombre "RM" no
   podía encontrarlo **jamás**.
3. **BCM está EN MEDIO de P2P, no al final.** Entre F110 y el fichero al banco: lote
   (`BNK_BATCH_HEADER` 27.443 / `BNK_BATCH_ITEM` 600.042) → panel `BNK_APP` → **liberación**
   → recién entonces el fichero (`BNK_MONI`: *Approved = file creation scheduled*).
4. **La cobertura del gate NO es uniforme por sociedad** — y es un problema de denominador:
   Tier 1 (UNES/UBO/IIEP/UIL/UIS) BCM completo · **Tier 2 (ICTP): 115.673 filas REGUH y CERO
   lotes BCM en la historia** · Tier 3 (IBE/MGIE/ICBA) ni aparece en REGUH. Solo el **25-30%**
   de REGUH 2024+ llega a `BNK_BATCH_ITEM`.
5. **Hueco de doble control, medido:** 5.757 lotes creados, 2.394 aprobados por otro usuario,
   **3.359 con `CHUSR = CRUSR` (58,4%)** — y `BCM Batch Approved` solo se emite cuando
   difieren, así que **el mayor hueco de control sale dibujado como variante normal**
   (claim 625).
6. **La cadena completa del P2P** (corregida por el dueño): PO → **recepción** → **hoja de
   entrada de servicios** → factura → PPC → WF → F110 → BCM → fichero → extracto. `ESSR/ESLL`
   ya está minado en `p2p_process_mining.html`; lo que falta es la **costura**.
7. **`YSBC_TRACE_PAYMENT` es `INTTAB`** — una estructura, no una tabla. Las transparentes son
   `YTBC_TRACE` / `YTBC_TRACE_DET`. Un `RFC_READ_TABLE` sobre una estructura responde "no
   existe", que es fácil de leer como "no hay datos".

---

## 6bis. LA COLABORACIÓN ENTRE AGENTES — el dato que da la razón al dueño

Insistió tres veces en que **colaboraran los agentes**. Yo había contestado el bus **como
agente principal** y lo llamé colaboración: no lo es.

**De los 9 lanzamientos atribuidos de toda la historia del proyecto, CUATRO son de hoy.**
El 44% de la colaboración medida ocurrió en la sesión en que se exigió.

Y convergieron sin hablarse: banca y minero midieron **los mismos 3 tiers por sociedad** por
caminos distintos; `Explore` corrigió un skill que yo había escrito esa misma mañana, usando
la sección que yo había aterrizado — el bucle cerrándose en horas.

**Ceguera estructural descubierta:** un subagente **no puede distinguir a su padre de un
extraño**. `brain-steward` levantó una bandera de "sesión paralela" que era falsa: eran mis
8 commits. Hizo bien en levantarla. **Mecanizado** con el sello `Session:` en cada commit.

---

## 7. REGLAS PROPUESTAS → ya en `feedback_rules.json`

- `feedback_a_misleading_name_can_hide_dependency_identity_not_existence`
- `feedback_reconcile_divergent_sources_by_union_with_provenance_not_derivation`
- extendida la del denominador con las 3 reincidencias de hoy

---

## 8. LO QUE ESTUVO MAL EN LA ENTRADA

Nada en la entrada del dueño. **Lo que estuvo mal fue mi lectura del árbol de trabajo:** di
por hecho que 32 ficheros sucios "no eran míos" sin comprobarlo, y llevaban sucios **desde
ayer**. El dueño lo vio en su editor (`+10.284/−4.673`) y preguntó. Un árbol crónicamente
sucio **esconde los cambios reales** — llevaba todo el día leyendo `git status` con 30 líneas
de ruido que ni miré.

---

## 9. MECANIZADO EN ESTA SESIÓN

| Instrumento | Qué cierra |
|---|---|
| `process_axis_consistency_check.py` | El eje de proceso ya no puede derivar en silencio |
| `agent_invocation_check.py` | El lector que faltaba desde s099 |
| `canonical_usage_lint.py` | Mide quién ignora el helper — **idioma humeante 4 → 0** |
| `record_agent_roster.py` + petición en el arranque | El roster del harness deja de ser prosa; **el diff es el hallazgo** |
| `commit_session_stamp.py` + `whose_commits.py` | "¿Este commit es mío?" pasa a tener respuesta |
| `store_write_guard_hook.py` | Escribir un store con el rebuild vivo deja de ser invisible |
| `canonical.py` + `canonical_or_parent()` | El helper **completado**, no rodeado |

---

## 10. LA LECCIÓN DE LA SESIÓN

**Escribir la defensa no es defender.**

`canonical.py` se escribió en s097 para matar un defecto que había aparecido tres veces. Se
documentó. Se dejó listo. Y el defecto apareció **tres veces más** — cometido por el agente
que ese mismo día predicaba no reinventar lo que existe. Nada obligaba a usarlo y **nada
medía que se ignoraba**.

Lo mismo con la bandera del steward: mi primera respuesta fue escribir en el braintoolbox
*"verificar con git log antes de creerse la alarma"*. El dueño preguntó: **"¿no hay que
mecanizarlo?"**. Tenía razón. Una defensa en prosa que depende de acordarse **no es un
mecanismo**.

El patrón de todo el día es uno: **un instrumento debe declarar la frontera de lo que su
fuente cubre.** `UNOBSERVABLE` en vez de `DEAD`. `agent: null` en vez de `"(unspecified)"`.
`SIN SELLO` en vez de `AJENO`. Las tres son la misma frase: *no puedo ver* nunca es *no hay
nada*.

---

## 11. ESTADO AL CERRAR

- **26 commits.** Árbol limpio. **3 sin empujar** — el push lo denegó el clasificador de
  auto-mode; queda para el dueño.
- Puertas: `braintoolbox_check` 16/16 · `process_axis` 7/7 · `algorithm_landing` PASS ·
  `curate` exit 0, **cobertura 100% sin bajar**.
- Claims **619-626** · KUs 2 (1 refutado, 1 contestado) · PMO **H134-H142**.
- **Backup diferido por decisión del dueño** ("luego hacemos backup"): Golden DB 21,25 GB y
  `~/.claude` 1,95 GB siguen sin copia — `D:` no está montado.

### Abierto, con dueño

- **El flag de un solo bit:** `YTBC_TRACE.ACTIVE='X'` para `WF_PAYMENT` en P01 convierte la
  liveness de RM de inverificable a medida. **Producción — decisión del dueño.**
- **H137** — el circuito P2P sigue en 4 piezas con junta seca, y el grafo de companions **no
  conoce la cadena**.
- **H138** — `braintoolbox.yaml` no parsea como YAML.
- **3 ficheros tibios** que leen tablas de alias sin importar `canonical`.
