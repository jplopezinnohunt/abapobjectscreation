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
