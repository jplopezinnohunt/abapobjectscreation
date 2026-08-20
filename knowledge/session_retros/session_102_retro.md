# Session #102 — Egipto no hacía falta, y el modelo que faltaba debajo

**Fecha**: 2026-08-20 · **Commits**: `c1386b4` → `cbdf7b5` (+ los del cierre)
**Claims**: 530–536 · **Reglas**: +3 (219–220 + la del recargado) · **PMO**: H101/H102 cerrados, +H106–H111

---

## 0. Qué fue esta sesión

Empezó con una noticia del usuario —Société Générale confirma que Egipto no necesita purpose code— y terminó con un modelo de cómo opera la banca en UNESCO, un explorador, un agente y tres checks nuevos.

Pero lo que importa no es el inventario. Es **cómo se llegó ahí**, porque no lo conduje yo.

---

## 1. El patrón: un solo modo de fallo con seis caras

El usuario me corrigió seis veces. Las seis correcciones fueron **del mismo tipo**, y no lo vi hasta la quinta:

| # | Lo que hice | La corrección | Qué era en realidad |
|---|---|---|---|
| 1 | Construí el censo de bancos | *"la sociedad es el primer driver"* | modelé sin preguntar de quién es el modelo |
| 2 | Publiqué `SIN DESTINO CONOCIDO` | *"investiga los 4 bancos"* | **la etiqueta era falsa**: no era "no lo vemos", era "no hay tercero" |
| 3 | Escribí `house_bank_operating_roles.md` | *"el companion solo no es conocimiento, hay que linkearlo"* | dejé un nodo sin aristas |
| 4 | Medí `FEBKO` contra el Gold DB | *"los extractos llegan por fichero de un sistema externo"* | **ya estaba documentado**, no cargué el dominio |
| 5 | Creé checks, explorador, agente | *"¿está encadenado o es algo que no usamos más?"* | tres huérfanos |
| 6 | Publiqué porcentajes | (lo cacé yo, tres veces) | denominador incompleto |

**Es una sola falta: producir artefactos más rápido de lo que los conecto.**

Y tiene nombre en este proyecto. Es **CP-001** — *nunca sacrificar trazabilidad ni conocimiento por velocidad*. Violé el primer principio de la constitución seis veces en un día, **mientras construía la maquinaria para hacerlo cumplir**.

---

## 2. Lo que de verdad duele: quién me corrigió

Ninguna de las seis la cazó un control. Las seis las cazó **el usuario**.

Los 220 reglas del corpus no dispararon ni una vez. Lo que sí disparó fue mecánico:
- `store_schema_check.py` cazó que había escrito `claims.json` con el indent equivocado
- el hook de arranque me hizo cargar el dominio **al principio** (y por eso el fallo fue en el medio, no al inicio)

> **Una regla con forma de juicio, guardada en un JSON, no dispara. Un mecanismo sí. Una persona sí.**

Eso no es una observación blanda: es la respuesta a la pregunta de qué hacer con 195 reglas de prosa. **22 de ellas son CRITICAL y no se citan en ningún artefacto.** *(Corregido el mismo día: publiqué 95 sin citar y 28 CRITICAL; el corpus con el que medí excluía `claims.json` e `incidents.json`, donde se citan 31 reglas. Los números reales son 72 y 22.)*

Y una corrección más importante que el número, que vino de JP: **iba a retirar 9 reglas usando "no está citada" como prueba de que no sirven.** Eso no mide utilidad, mide citación — el patrón del claim 496 aplicado por mí a las reglas que me gobiernan. Dos de mis candidatas: `never_run_an_ungated_sap_writer`, que protege contra la clase de INC-CLASS-LOSS, y `never_sum_an_amount_across_currencies`, que **violé el día anterior**. Estaban trabajando; mi medidor no las veía. **La deuda de one-in-one-out no se paga borrando: se paga mecanizando o reubicando** — y hoy se mecanizaron 4 de las 7. Regla nueva: `feedback_never_retire_anything_without_evidence` (CRITICAL).

---

## 3. Lo que sí se mecanizó, y qué encontró cada cosa

Tres checks nuevos. **Los tres encontraron algo en su primera ejecución**, y eso dice más del estado del sistema que de los checks:

| Check | Qué mecaniza | Qué encontró al primer intento |
|---|---|---|
| `ppc_country_consistency_check` E/F | el blanco que no se puede almacenar | **un defecto VIVO en P01**: `T015L INA` con dos espacios, esperando desde que se configuró India (claim 529) |
| `domain_load_coverage_check` | recargar el dominio cuando el tema se mueve | **falla contra mí**: 227 líneas escritas en `Treasury` sin haber cargado nunca ese dominio |
| `artifact_wiring_check` | *"¿lo invoca alguien?"* | **8 huérfanos**, la mayoría anteriores a hoy |

Más `config_transport_prerelease_check` (de ayer), que clasifica `VIAJA / INTRUSA / NO-OP / DERIVA` y caza la clase de defecto que casi cambia Indonesia.

**Una tasa de acierto del 100% en primeras ejecuciones no es mérito de los checks.** Es la medida de cuánta superficie tenemos sin instrumentar. El 12% de mecanización no es un problema de madurez: es un indicador de oportunidad.

### Y una autocorrección que merece constar

`artifact_wiring_check` nació con una categoría —*quality checks sin declarar*— que **duplicaba un aviso que `run_all.py` ya da** en cada corrida. La quité. La preferencia del proyecto es *eliminar > mecanizar > reubicar > añadir*, y un segundo aviso para el mismo hecho es cómo se consigue que se ignoren los dos.

También nació con un falso positivo que habría hundido su credibilidad: marcaba como muertos 18 ficheros JSON de **estado**, que su propio autor relee en la vuelta siguiente. Corregido a 2. Un check que llora lobo 18 veces deja de leerse — que es exactamente el modo de fallo contra el que existe.

---

## 4. Lo que aprendimos del sistema (Phase 4b)

1. **El eje doméstico/internacional ya estaba escrito en SAP** y lo leíamos mal: `T042Z-TEXT1` dice literalmente `L` *"Payments in US in USD only"* y `N` *"Payments outside US non-EUR"*. Llevábamos meses leyendo los métodos como claves de enrutado y nunca como una afirmación sobre **qué clase de pago** es cada uno. La frase con la que BFM cerró Egipto es el nombre del método `L`.
2. **Tres capas, tres ejes**: la captura (`u917`) se clava en el banco del beneficiario, el fichero en el nuestro, y la aprobación BCM en la sociedad y el importe — `HBKID` no aparece en ninguna regla de BCM.
3. **De 47.399 líneas capturadas con purpose code, sólo el 80% llega a un fichero.** 171 son pagos domésticos a los que se exige un código transfronterizo que luego se tira.
4. **La topología se deriva de la diversidad de destinos, no del volumen**: `SOG01` alcanza 209 países, `ECO02` alcanza 3.
5. **36 de 37 bancos de oficina de campo pagan 100% en cheque.** Brasil y Canadá son las excepciones que prueban que se puede salir del papel.
6. **La palanca de la centralización no es centralizar**: de ~10.400 líneas en papel, sólo 647 (6%) son candidatas; 5.766 (55%) están bloqueadas por datos bancarios de proveedor ausentes. Y esa causa converge con dos casos que parecían distintos.
7. **El canal es de ficheros y lo mueven jobs** que ya teníamos medidos y sin conectar: acuse por sociedad, estado por banco, extracto cada hora.
8. **`FEBKO` en el Gold DB es el 37%** de lo que existe y cubre 3 sociedades de 6.

---

## 5. Qué falta por mecanizar — evaluado, no listado

Miré cada fallo de hoy y me pregunté si un mecanismo lo habría cazado:

| Fallo | ¿Mecanizable? | Estado |
|---|---|---|
| Medir un dominio sin cargarlo | **Sí** | hecho hoy |
| Artefacto que nadie invoca | **Sí** | hecho hoy |
| Blanco final imposible de almacenar | **Sí** | hecho ayer |
| Clave de un vecino en un transporte | **Sí** | hecho ayer |
| Etiqueta derivada de una **ausencia**, publicada sin investigar | **Sí, y no está** | ver abajo |
| Modelar sobre el eje equivocado | No | es juicio; vive en el agente |
| Repetir un aviso propio sin medirlo | No | es epistemología, no procedimiento |

**El único hueco mecanizable que queda de esta sesión:** una etiqueta cuyo criterio es una **negación o un cero** (`SIN DESTINO CONOCIDO`, `ndest == 0`) es una afirmación sobre *nuestro conocimiento*, no sobre los datos. Publicarla sin investigar a sus miembros es lo que produjo la etiqueta falsa. El explorador ya tiene una sonda de residuo de taxonomía; le falta distinguir **cubos de ausencia** de cubos normales y exigir evidencia antes de que salgan a un companion.

No lo construí hoy a propósito: hoy ya añadí tres checks y debo nueve retiradas de reglas. Añadir un cuarto sin pagar nada sería exactamente lo que critico.

**Y dos reglas que NO hay que mecanizar, hay que reubicar**: `predict_the_output_before_you_generate_it` y `a_warning_in_a_document_is_not_a_measurement` son epistemología. Pertenecen a **CP-003** como elaboración, no a las posiciones 219 y 220 de un fichero que nadie abre.

---

## 6. La deuda que dejo, dicha

- **La deuda de `one_rule_in_one_rule_out` sigue abierta, pero NO se paga retirando.** Añadí 7 ayer y 3 hoy; mecanicé 4. Lo que falta es **reubicar** las 22 CRITICAL sin punto de uso a donde apliquen —un check, un agente, un doc— no borrarlas.
- **68 items de PMO vivos**, el bloque `INCOMING` más antiguo del 18 de junio. Hoy metí 11 y cerré 2.
- **8 huérfanos** que el check nuevo destapa y que no arreglé.
- **El borrado de la configuración de Egipto en D01** queda pendiente de confirmación del usuario (H106), con snapshot previo guardado.

---

## 7. Lo que me llevo

Las cuatro contribuciones que hicieron el modelo fueron del usuario, no mías: *la sociedad es el primer driver*, *investiga en vez de etiquetar*, *un companion suelto no es conocimiento*, y *¿esto está encadenado o no lo usamos más?*.

El modelo que queda no es el que yo diseñé. **Es el que salió de que me corrigieran seis veces.** Y las seis correcciones eran la misma: conectar antes de producir.

> Construir rápido y conectar después no es rápido. Es construir dos veces.
