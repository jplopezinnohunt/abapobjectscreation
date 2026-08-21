# Session #102 · día 2 — Un alta de dos cuentas destapó cómo se mantiene el alcance de la revaluación

**Fecha**: 2026-08-21 · **Commits**: `c365309` → `fe6915c`
**Claims**: 554–565 · **Reglas**: +3 · **Dominios**: +2 (`Master_Data_Governance` creado, `Closing_Activities` **rescatado**)
**PMO**: +H107 · **Instrumentos**: `fsv_coverage_check.py`, `build_full_census.py`, `variant_selection`/`covered_in`

---

## 0. Qué fue esta sesión

Empezó con un ticket de dos cuentas de fondos monetarios (`INC-000016262`) y terminó con el
alcance completo de la revaluación FX de UNES medido, un dominio que llevaba cinco sesiones
declarado y sin registro, y un método de descubrimiento escrito.

Pero el hallazgo no es ninguna de esas cosas. Es que **el alcance de la revaluación depende de que
alguien se acuerde**, y eso se puede medir:

| Modo de selección | Cobertura | Huecos que genera |
|---|---|---|
| `RANGE` | 87 % | **0** |
| `ALL-BUT` | 10 % | 4 |
| `INDIVIDUAL` | **4 %** | **47** |

`4041011` no se cayó por descuido: se cayó porque está en el único universo que se mantiene a
mano. Y con ella hay **49 más** con `OB09` puesto, divisa abierta y ninguna variante.

---

## 1. El modo de fallo: medí antes de fijar el denominador

Cuatro falsos positivos, todos míos, **los cuatro cazados por JP y no por mí**:

| # | Lo que publiqué | La corrección | Qué era en realidad |
|---|---|---|---|
| 1 | «68 cuentas y **144 M EUR** fuera de la FSV» | — | barrí cuentas de **UNES** contra **FS11**, que es la versión de IIEP/ICTP. Contra FS10 el hueco son 4 cuentas y **0,01 EUR** |
| 2 | «**549** candidatos fuera de variante» | *"no puede ser que tengamos 549"* | `AKONTO` tenía 27 líneas y **las 27 de exclusión** = *todas menos esas*, no *ninguna*. Y mezclé `SKONTO` con `AKONTO` |
| 3 | «el criterio de `UNES_DEPOSIT` es la moneda» | los datos | dentro hay cuentas en USD con euros, correctamente incluidas. Hipótesis refutada el mismo día |
| 4 | «`4041011` es la excepción» *(en prosa)* | *"algo estás haciendo mal"* | **parcheé el desacuerdo del clasificador con una frase en vez de arreglar la regla** |

Es una sola falta con cuatro caras: **medir una población contra un patrón sin demostrar antes que
el patrón se le aplica.** Una versión de balance existe para todos y se *ejecuta* para algunos. Un
select-option vacío con exclusiones significa *todo menos eso*. Un campo de selección es un
universo, no una lista. En los cuatro casos había un paso previo —probar la aplicabilidad— que me
salté porque el dato estaba a mano.

**El cuarto es el peor** y merece nombre propio: cuando mi propio clasificador contradijo la
conclusión a la que ya había llegado, escribí un párrafo explicando la excepción en vez de admitir
que el criterio estaba mal. Eso es usar la evidencia para justificar, no para decidir.

---

## 2. Las tres correcciones de método que puso JP

No fueron matices: cada una cambió qué se reportaba.

**«Los universos los definen las variantes».** Yo medía contra el balance entero — 497 cuentas
fuera, un número sin significado. El universo son las **28 posiciones** que las variantes ocupan;
las otras 51 están fuera por diseño.

**«Para agrupar debes usar posición».** Yo había metido el bloque de numeración como segundo eje
porque me permitía rescatar `4041011`. Agrupar solo por posición da una lectura más limpia y más
incómoda: `1.1.2.1 Short Term Deposits` no la trabaja **nadie**, con 8 cuentas y 764 M USD. No es
«se olvidaron de una cuenta», es «esa posición del balance no se revalúa».

**«No pierdas la agrupación por variante».** Una posición puede estar en dos variantes porque
contiene cuentas que se comportan distinto. `Cash with Banks` tiene cuatro tratamientos en una
línea de balance: banco principal por saldo, subcuenta por partidas abiertas, fondos monetarios
por lista, y 16 técnicas que no cubre nadie. Colapsarlo en una fila lo escondía.

---

## 3. Lo que se rescató sin buscarlo

**`Closing_Activities` estaba declarado canónico desde s097 y sin registro.** La propia ontología lo
decía —*"orphan by design… the registry is what is incomplete"*— y ahí llevaba cinco sesiones. Sus
**4 documentos, 17 claims, 2 companions y su incidente colgaban de nada**, y preguntar por «el
dominio de la revaluación» no devolvía dominio.

Y lo que lo permitió: **el validador solo comprobaba una dirección**. Ahora comprueba las dos y
falla con exit 1 — probado quitando el registro a propósito.

---

## 4. Qué aprendimos de SAP (Fase 4b)

- **`SKB1-WAERS` = moneda de la sociedad significa «admite cualquier moneda»**, no «cuenta en
  dólares». Ahí vive la clase de defecto entera: una cuenta en USD con euros dentro necesita
  revaluación y **el maestro no lo dice**.
- **Ninguna cuenta puede estar en dos variantes de F.05.** En una cuenta de partidas abiertas el
  saldo *es* la suma de las partidas: valorarla por las dos vías postearía la diferencia dos veces.
  Lo decide `SKB1-XOPVW`, no una elección.
- **Qué versión de balance se ejecuta lo dice la VARIANTE**, no `T011`: `RFBILA00`, parámetro
  `BILAVERS` + `SD_BUKRS`.
- **`XOPVW` decide la tabla de determinación**: `'X'` → KDF → `T030H` (una fila por cuenta, = OB09);
  vacío → KDB → `T030S` (una fila por clave). Pedir `T030H` a una cuenta de saldo produce 160 falsos
  defectos.
- **Los recortes individuales de una variante por rango son higiene**: las 3 de `UNES_OI_G/L` son
  cuentas `CLOSED` y bloqueadas.
- **Saldo no es exposición**: `4041011` tiene 571,6 M USD de saldo y **10 M EUR** que revaluar.

---

## 5. Lo que queda abierto

**Para Tesorería/FRA** — no «añadid `4041011`», sino: *¿por qué `404xxxx` y los clearing
`509x`/`920x` se mantienen a mano cuando bancos va por rango?* Y aparte: **725 M USD** de divisa
abierta viven en posiciones que **ninguna** variante trabaja —préstamos Miollis, condiciones con
donantes, patrimonio— y eso es pregunta de compensación o de política contable, no de F.05.

**Deuda propia**: el bloque de numeración a dos dígitos es demasiado grueso para asignar destino
(`50xxxxx` mezcla patrimonio, préstamos y clearing de institutos). Para asignación real, seis
dígitos.

**Durabilidad**: `D:\claude_backups` desconectado desde el 19-ago; la Golden DB (15,2 GB) y
`~/.claude` existen solo en este disco. 52 commits sin subir a `origin`.

---

## 6. La frase que resume el día

> **Un rango es una regla y una lista es un inventario.** La regla no envejece; el inventario sí.

Y la versión incómoda, sobre mí:

> **Cuatro veces medí antes de saber contra qué medía, y las cuatro me paró JP.** Lo que queda no
> es la lección en prosa: está metida en los instrumentos, que ahora derivan el denominador en vez
> de suponerlo.

---
---

# Retrospectiva PROFUNDA

Pedida por JP al cierre: *qué hicimos, qué logramos, qué podemos hacer mejor, qué hay que cambiar,
qué deberíamos mecanizar.* Con números, no con impresiones.

## 7. Qué hicimos — el inventario

**41 commits**, **52 ficheros nuevos**, 12 claims, 3 reglas, 2 dominios, 5 instrumentos.

| Categoría | Qué |
|---|---|
| **Ticket cerrado** | `INC-000016262` — 2 cuentas MMF alineadas en D01/V01, OB09 + variante decididos, FSV verificada |
| **Alineación ejecutada** | GL master (2 en D01, 33 en V01) · 21/21 variantes · FSV FS10+FS11 byte-idénticas |
| **Dominios** | `Master_Data_Governance` **creado** · `Closing_Activities` **rescatado** tras 5 sesiones huérfano |
| **Instrumentos** | `fsv_coverage_check` · `fx_revaluation_peer_check` · `fx_revaluation_scope_check` · `build_full_census` · `variant_selection`/`covered_in` |
| **Método** | El proceso de descubrimiento en 6 pasos, escrito y cableado al agente |
| **Hallazgo** | 50 cuentas con OB09, divisa abierta y ninguna variante — `4041011` es una de 50 |

## 8. Qué logramos — lo que vale más que el inventario

**Un modelo, no una lista de defectos.** «Un rango es una regla y una lista es un inventario»
predice dónde aparecerán los próximos huecos sin volver a medir. `RANGE` cubre el 87 % y genera
**0**; `INDIVIDUAL` cubre el 4 % y genera **47**. Eso convierte la recomendación de *«añadid estas
cuentas»* en *«cambiad cómo se mantiene esta variante»*.

**Separar el hallazgo de la alarma.** De 744 M USD aparentemente sin revaluar, solo ~19 M son un
hueco real. Los otros 725 M son pregunta contable. Sin esa separación, el informe habría sido
inaccionable.

**Tres correcciones que vinieron del usuario y cambiaron el análisis**, no lo matizaron: *los
universos los definen las variantes* · *para agrupar usa la posición* · *no pierdas la agrupación
por variante*.

## 9. Qué podemos hacer mejor — el coste real de la sesión

**10 de 41 commits fueron auto-correcciones.** Casi uno de cada cuatro. Y de las cuatro
correcciones grandes, **las cuatro las detectó JP**, no yo:

| Publiqué | Era |
|---|---|
| 144 M EUR de hueco en la FSV | denominador equivocado — FS11 es de IIEP/ICTP |
| 549 cuentas fuera de variante | 497 — una selección con solo exclusiones significa *todo menos eso* |
| «el criterio es la moneda» | refutado por mis propios datos horas después |
| `4041011` como excepción explicada en prosa | el clasificador decía otra cosa y lo parcheé con un párrafo |

**La causa raíz no es descuido: es orden de operaciones.** Mido, publico, y verifico solo si algo
chirría. Los instrumentos que construí hoy verifican **después** de que yo haya afirmado. El coste
no fue el tiempo de rehacer — fue que **cuatro veces JP tuvo que hacer de gate**, y eso no escala.

**Un patrón que se repite de la sesión anterior.** El retro del día 1 decía: *«producir artefactos
más rápido de lo que los conecto»*. Hoy volvió a pasar en dos formas medibles:
- **Ninguno de los 5 checks nuevos está cableado a `run_all.py` ni a `rebuild_all.py`.** Cinco
  instrumentos que solo corren si alguien se acuerda — exactamente el defecto que denuncié en
  `UNES_DEPOSIT`.
- **Dos generadores de workbook** en la misma carpeta: `build_scope_workbook.py` quedó superado por
  `build_full_census.py` y nadie lo retiró.

**Y un fallo nuevo de disciplina**: commiteé `brain_state.json` **mientras un rebuild seguía
corriendo**, capturando un estado intermedio. La regla de un solo escritor la tenía por «no lanzar
dos rebuilds»; le faltaba «no commitear generados mientras uno corre».

## 10. Qué hay que cambiar — lo estructural

### 10.1 Un incidente sin proceso es un caso, no conocimiento

Lo señaló JP y se midió: **11 de 13 incidentes no tienen documento de proceso en su dominio.** Los
dos que sí lo tienen son los dos de hoy, y solo porque él lo pidió.

Peor: hay **tres pares** — dos incidentes del mismo dominio y tipo — donde el proceso ya se podría
haber escrito y no está:

| Dominio | Tipo | Incidentes | Proceso que falta |
|---|---|---|---|
| `Treasury_EBS` | MASTER_DATA | `INC-000006313` + `INC-000011781` | **autorización bancaria BCM** — alta y baja de personas |
| `Payment_BCM` | REGULATORY | `INC-EGYPT-PPC` + `INC-PSTLADR-NOV2026` | requisito regulatorio de un banco |
| `PSM_FM` | ERROR | `INC-000005638` + `INC-BUDGETRATE-EQG` | tipo de cambio presupuestario |

El de BCM es idéntico al de hoy: **dos casos del mismo proceso, y el proceso en ninguna parte**.
La regla del skill dice *«por la 2ª ocurrencia debes un procedimiento»*, y llevamos tres pares
incumpliéndola.

**El cambio**: el cierre de un incidente no es el documento del caso. Es el documento del caso
**más** la respuesta a *¿qué proceso enseña esto y dónde vive?*. Si el dominio no existe, se crea;
si existe sin proceso, se escribe.

### 10.2 El gate bidireccional que hice hoy es la mitad del que hace falta

`validate_ontology.py` ya comprueba *declarado → registro*. Pero **no** comprueba
*incidente → dominio con registro*: `INC-CLASS-LOSS-2026-06` apunta a `BASIS`, que es una clave
transversal, no un dominio. Es el mismo defecto que tuvo `Closing_Activities` cinco sesiones.

### 10.3 Verificar antes de publicar, no después

Las cuatro correcciones tienen la misma forma: **afirmé sobre una población sin demostrar que el
patrón se le aplica**. El cambio no es «tener más cuidado» — es que **ninguna cifra sale sin que el
instrumento haya derivado su denominador**. Hoy los instrumentos lo hacen; yo lo hice a mano y por
eso fallé.

## 11. Qué deberíamos mecanizar — en orden de valor

| # | Mecanizar | Por qué | Estado |
|---|---|---|---|
| **1** | **`incident_domain_knowledge_check.py`** — todo incidente tiene dominio con registro y doc de proceso; avisa cuando hay 2+ del mismo tipo sin proceso | 11 de 13 incumplen; es la fuga de conocimiento más grande medida | **HECHO hoy** |
| **2** | **Cablear los 5 checks a `run_all.py`** con su tier | 5 instrumentos que solo corren si alguien se acuerda = el defecto de `UNES_DEPOSIT` aplicado a nosotros | pendiente |
| **3** | **Gate de artefactos huérfanos** — un `.py` nuevo en `quality_checks/` que no esté en `run_all` falla el cierre | tercera sesión seguida creando huérfanos | pendiente |
| **4** | **Guard de escritor único al commitear** — negarse a `git add` de generados si hay un `rebuild_all` vivo | commiteé un `brain_state` a medio construir | pendiente |
| **5** | **Retirar duplicados** — `build_scope_workbook.py` lo supera `build_full_census.py` | dos generadores del mismo Excel | pendiente |
| **6** | **Denominador declarado** — que todo check que publique un porcentaje imprima primero *contra qué* mide y de dónde lo dedujo | los 144 M y los 549 nacieron de no declararlo | parcial: `fsv_coverage_check` ya lo hace |

## 12. La medida honesta de la sesión

Produjimos un modelo que predice dónde fallará la revaluación, rescatamos un dominio perdido y
dejamos cinco instrumentos. También gastamos **una cuarta parte de los commits en corregirme**, y
**el gate de calidad fue JP cuatro veces**.

La diferencia entre una sesión buena y una excelente no está en el hallazgo — está en cuántas veces
el usuario tuvo que hacer de verificador. Hoy: cuatro. **Ese es el número que hay que bajar**, y se
baja mecanizando el punto 6, no prometiendo cuidado.
