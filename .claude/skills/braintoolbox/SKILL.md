---
name: braintoolbox
description: >
  Como se trabaja en este proyecto: que instrumento usar para cada tarea y como no publicar
  una cifra falsa. Usala ANTES de escribir un script, proponer un modelo, crear un skill o un
  agente, medir cualquier poblacion, o cuando no sepas si algo ya existe. Contesta: ¿esto es
  un SKILL, un AGENTE o un MINERO? ¿ya existe? ¿que infla la senal que estoy a punto de
  publicar? Es el modelo operativo, no documentacion de fondo.
when_to_use: >
  "voy a escribir un script" · "necesito un skill/agente nuevo" · "cuantos X hay" · "esto no
  se usa" · "que herramienta uso para" · "propongo un framework" · antes de publicar cualquier
  porcentaje · cuando un instrumento devuelve 0 o verde
---

# Braintoolbox — el modelo operativo

**El modelo MEDIDO vive en `brain_v2/braintoolbox.yaml`** y su puerta
(`Zagentexecution/quality_checks/braintoolbox_check.py`) comprueba que cada cifra suya siga
coincidiendo con los ficheros vivos. Aqui esta lo que hay que HACER; alli, lo que se mide.
No dupliques cifras aqui: envejecen y nadie las vigila.

## 1. Antes de construir nada: pregunta si ya existe

```bash
python brain_v2/graph_queries.py tool para "<tu tarea en una frase>"
```

Devuelve, en este orden: **qué SKILL leer primero**, qué algoritmo ya existe, qué agente lo
hace, qué puerta lo vigila y **qué sabemos ya** (claims, incidentes, dominios).

⛔ **El orden no es decorativo y saltárselo es el fallo más caro de este proyecto.** Medido en
s107: el coordinador respondió `1_LEE_ESTO_PRIMERO: sap_payment_bcm_agent` y no se leyó →
se publicaron **tres errores** en una etapa del circuito P2P (5 tipos de documento en vez de
14; "el workflow termina" cuando en realidad aparca esperando un evento; sin declarar la
sociedad). Las tres cosas estaban escritas en ese skill.

## 2. Qué es cada cosa, y su primitiva real

> **Si es para leer es SKILL; si decide, es AGENTE; si descubre, es MINERO.**

| rol | se consume | se especializa por | primitiva |
|---|---|---|---|
| **SKILL** | se LEE | DOMINIO | `.claude/skills/<n>/SKILL.md` |
| **AGENTE** | se INVOCA | DOMINIO | `.claude/agents/<n>.md` |
| **MINERO** | se EJECUTA | **TIPO DE EXPLORACIÓN** | script + ficha en `algorithms.json` |
| **GATE** | vigila un store, sale con 1 | — | script con `QUALITY_CHECK` |
| **STORE** | ahí ATERRIZA | — | fichero |

Los dos primeros ejes son **ortogonales**: por eso un minero sirve a cualquier dominio — no es
que sea general, es que está especializado en el otro eje.

**Criterio de corte** cuando un método vive dentro del prompt de un agente: *lo que necesita
CRITERIO se queda en el agente; lo que es DETERMINISTA sale como minero.*

**Tercer eje, la PROCEDENCIA** — PROPIO (versionado) · DEL HARNESS (lo da el runtime a la
sesión, no al disco: **no enumerable**) · DE OTRO PROYECTO. Un agente del harness no puede
aparecer en ningún grafo derivado del repo, **jamás**. Declara `UNOBSERVABLE`, nunca cero.

## 3. Los seis modos de publicar algo falso

Todos son la misma falta: **afirmar sobre una población sin comprobar que el método de medida
se le aplica**.

| modo | pasa cuando | defensa |
|---|---|---|
| **DENOMINADOR INCOMPLETO** | mides una población contra un patrón sin demostrar que se le aplica | el instrumento DERIVA su denominador; nunca lo supone |
| **EL ALIAS QUE DA CERO** | una clave canónica no es la clave del registro | usa `canonical.same()`. Un alias mal resuelto **no da error: da un cero** |
| **CREERSE EL PROPIO PRINT** | reportas éxito por lo que se imprime, no por lo que queda escrito | verifica **leyendo el destino** |
| **EL HUÉRFANO PROPIO** | creas un instrumento y no lo declaras | decláralo en su store el mismo día |
| **REINVENTAR LO QUE EXISTE** | propones sin mirar el toolgraph | paso 1 de este documento |
| **MEDIR LA FORMA, NO EL EFECTO** | compruebas que la comprobación *existe*, no que *funciona* | ver §4 |

**Y la señal se infla por vocabulario ubicuo — tres veces medido.** `rfc_read_table` está en
20 de 50 skills; las sociedades en 10; el inglés genérico de las descripciones, en todas.
**Antes de publicar un ranking por solape, pesa por IDF y exige al menos un término raro.**

**Variante medida en s109, a caballo entre EL HUÉRFANO PROPIO y MEDIR LA FORMA, NO EL EFECTO:**
un registro puede estar DECLARADO (no es un huérfano) y aun así ser invisible, si se escribió
en la clave equivocada del mismo fichero — D1-D7 se registraron en la RAÍZ de
`brain_v2/methods/algorithms.json`, fuera de la clave `algorithms` que
`algorithm_landing_check.py` recorre, y el gate daba PASS sin haberlos mirado nunca (un verde
por no mirar, peor que un rojo). Y como el prefijo D1/D4/D5/D6 ya existía DENTRO con otro
significado, ni siquiera una lectura completa del JSON lo habría distinguido a simple vista.
**Defensa: al declarar, comprueba que el CONTEO del gate subió en el número exacto de entradas
añadidas — un PASS que no movió su denominador no te vio.** Regla:
`feedback_gate_coverage_is_bounded_by_what_it_walks`.

**Variante de REINVENTAR LO QUE EXISTE, medida en s109: reconstruí a mano una resolución que
el sistema ya hacía.** Medir "cuántos incidentes nombran un dominio inventado" a mano dio
"11 de 19" y luego "9 de 16" — ambas falsas por denominador incompleto (ignoraban
`cross_cutting_keys` y `domains[].aliases`/`subdomain_aliases`). La cifra buena, **5 de 16**,
salió de llamar a `validate_ontology.load_index()`, el resolvedor canónico (64 nombres, no 40).
No basta con recordar que `canonical.py` existe: hay que preguntar, para ESE vocabulario
concreto, si ya hay una función que lo resuelve, antes de reconstruirlo a mano. Regla:
`feedback_declare_the_denominator_before_publishing_a_number` (caso 8).

## 4. Un instrumento no está terminado hasta que falla a propósito

Correr sin error no es validación. Dar verde no es validación. **Escribir la advertencia en el
docstring no protege de cometerla** — medido seis veces en s107, incluida una puerta que
avisaba de un defecto en su cabecera y lo cometió en su primera corrida.

1. construye el caso que **DEBE** fallar — rompe el fichero, inyecta el duplicado, mete el valor vacío
2. córrelo y comprueba que falla **por la razón correcta**
3. restaura y comprueba que vuelve a verde

Si no se te ocurre un caso que deba fallar, el instrumento no discrimina nada — y **eso** es
el hallazgo. **El criterio tiene que estar en el `if`, no en la prosa.**

Y tras cualquier parche automático: **asegura el EFECTO, no el parseo.** Un `\1` puede acabar
en el fichero como el byte `0x01`: parsea perfecto, corre, sale con 0 y no casa nunca.

**Misma familia, medida en s109 sobre un hallazgo ya publicado, no sobre un parche:** un bloque
de código puede parsear perfecto y no ejecutarse NUNCA si vive después de un `return` — el
hallazgo más grave de `bank_statement_sod_check.py` (el ciclo de 4 eslabones) se publicó al bus
como agregado ("60 pagos, 9 pares") sin los pares en sí, porque el bloque que los serializaba
estaba tras el `return` de `informe()`. Un agregado correcto con el detalle perdido **parece**
un hallazgo terminado y no lo es: Auditoría no puede revisar "9 pares", solo 9 pares con
nombre. Corre el instrumento y lee el JSON de salida, no el código. Regla:
`feedback_an_aggregate_finding_without_named_subjects_is_not_actionable`.

## 5. Una cita, un import y una mención no son uso

Las tres aristas con las que medimos si el conocimiento se aplica cuentan un **proxy**:

- `LEE` cuenta que el **nombre** del skill aparezca en el texto → una cita
- `USA` cuenta un **import** → importar sin llamar puntúa igual
- `DELEGA` contaba que un agente **nombre** a otro → 4 de 26 eran menciones de estilo

Las tres se pueden llevar al 100% pegando texto. **Sirven para rankear dónde mirar; ninguna
vale como objetivo.** Publica siempre al lado la versión depurada y di si es **declarado** o
**observado**.

## 6. De cada trabajo quedan TRES cosas, y se pierden por separado

**objeto** (qué descubriste, clasificado en TODOS los sitios a los que pertenece) ·
**proceso** (cómo funciona: doc de dominio + companion) · **método** (cómo lo descubriste:
minero o algoritmo registrado). Sólo se echa de menos el proceso, porque es el entregable.
Puerta: `Zagentexecution/quality_checks/work_triad_check.py`.

## 7. Campos del front-matter que casi nunca usamos y deberíamos

- `user-invocable: false` — conocimiento de fondo que nadie teclea (**la mayoría de skills de dominio**)
- `disable-model-invocation: true` — lo que tiene efectos y cuyo momento decide la persona
- `allowed-tools` / `disallowed-tools` — permisos por skill
- `context: fork` — correr la skill en su propio subagente
- `scripts/` dentro de la skill — **se EJECUTA, no se carga**: coste de contexto cero

⚠️ Una skill cargada **se queda en contexto todo el turno**. Mantén el `SKILL.md` bajo 500
líneas y manda lo largo a `reference.md`.

## 8. Reconstruir el brain: TRES modos, y elegir mal cuesta en los dos sentidos

Correr de más son **56 minutos que nadie corre** — y un brain que no se reconstruye es cómo
el índice acaba mintiendo. Correr de menos deja un brain **coherente consigo mismo y
desfasado con el repo**, que es peor que uno claramente viejo.

| cuándo | comando |
|---|---|
| Añadiste un **claim, regla, incidente**, o tocaste `domains.json` — cambiaste un **store** | `python brain_v2/rebuild_all.py --rapido` · **~14 s** |
| Quieres repetir **un paso** que falló, o depurar uno | `python brain_v2/rebuild_all.py --solo <patrón>` |
| Tocaste **código, algoritmo, skill, agente, companion o gate** — lo que se DERIVA del repo | `python brain_v2/rebuild_all.py` · ~56 min |
| **No estás seguro de qué cambiaste** | el completo. La duda se resuelve con el completo |

`--rapido` corre tres pasos: ontología → `brain_state` → índice. **No** corre puertas, grafo,
casos golden, madurez ni companions. La ontología sí, y no es opcional: es la puerta que
impide materializar un dominio inventado — el 28-ago paró un rebuild entero por un claim con
un dominio que no existía.

Y **`--help` te lo dice**: desde s108 imprime este criterio y sale, igual que cualquier flag
desconocido. Antes `--help` no estaba manejado y **arrancaba el rebuild entero**: preguntar
qué hace una herramienta costaba 56 minutos.

**Dónde se van los minutos del completo** (medido sobre `curation.log`): enlazar docs 18,9% ·
la suite de puertas ~20% · casos golden 8,8% · índice de comprensión 7,8% · grafo NetworkX
7,6%. Cinco pasos son ~60% del tiempo.

## Para ir más lejos

- El modelo con sus cifras medidas y su historia: `brain_v2/braintoolbox.yaml`
- Cómo se mide la colaboración entre agentes: `brain_v2/research/wc0llab07_measuring_agent_collaboration.json`
- Qué instrumentos existen: `python brain_v2/graph_queries.py tool para "<tarea>"`
