# FIX B — Cargar la región de 467 proveedores de US y Canadá

Generado 2026-08-19 sobre P01. Incidente `INC-PSTLADR-NOV2026`, pista **FIX B**.

---

## 1. Qué campo se toca, y sólo ése

**`ADRC-REGION`** — el estado (US) o la provincia (Canadá) de la dirección del proveedor.

En pantalla es el campo **Region** dentro de la dirección del maestro de acreedores:

```
XK02 (o FK02) -> proveedor -> Datos generales -> Direccion -> campo "Region"
```

No se toca calle, ni ciudad, ni código postal, ni país. **Un solo campo por proveedor.**

Nota de verificación: `LFA1-REGIO` está vacío en los 467 (comprobado), así que no hay un valor
antiguo en el maestro que contradiga lo que se cargue en ADRC.

## 2. Por qué hace falta

Citi compone su **Target Address Line 2** como `TwnNm` + coma + `CtrySubDvsn`, y su documentación
dice de los dos campos *"both fields are mandatory"* (reglas GOLD 2026-05-06, hoja `499_US_WIRE`).
Sin región, esa línea va incompleta. Y en Estados Unidos y Canadá el estado o la provincia **es
parte de la dirección**, no un adorno: `NEW YORK` sin `NY` o `AURORA` sin `CO` no identifican un
sitio.

La regla entra en vigor el **14-11-2026**. Que hoy Citi lo acepte no dice nada: hoy no está en
vigencia.

## 3. Los ficheros

| Fichero | Proveedores | Pagos 2026 | Qué hacer |
|---|---:|---:|---|
| **`FIXB_1_CARGAR_region.csv`** | **399** | 3.529 | Cargar la columna `REGION_a_cargar` |
| **`FIXB_2_REVISAR_a_mano.csv`** | **68** | 264 | Preguntar antes de tocar |
| `FIXB_proveedores_US_CA_sin_region.csv` | 467 | 3.793 | Los dos juntos, por si se quiere la foto completa |

Columnas útiles: `proveedor` · `ADDRNUMBER` (la ficha ADRC exacta) · `ciudad_ADRC` · `cod_postal` ·
`REGION_actual` (vacía en todos) · **`REGION_a_cargar`** · `confianza` · `pagos_2026` · `formatos`.

## 4. De dónde sale cada valor — y por qué 68 quedan fuera

Cada fila dice su procedencia. **Ninguna región está inventada.**

**A — extraída de `CITY1` (159 proveedores).** La región ya estaba en el dato, pegada dentro del
nombre de la ciudad: `Montreal Quebec` → `QC`, `Peterborough Ontario` → `ON`, `Morris CT` → `CT`,
`SEATTLE WA` → `WA`. No se deduce nada: se separa lo que ya había. **Verificable leyendo el CSV.**

**B — derivada del código postal (240 proveedores).** Dos reglas oficiales y deterministas:
- *Canadá*: la primera letra del código postal determina la provincia (`H`→QC, `M`→ON, `T`→AB…).
- *Estados Unidos*: los tres primeros dígitos del ZIP caen en un rango de estado (tabla USPS).
  `10017`→NY, `80011`→CO, `98122`→WA, `85284`→AZ.

**C — a revisar a mano (68 proveedores).** Y aquí está lo importante: **no es que falte el dato,
es que el código postal es un comodín** — `99999-9999` en Estados Unidos, `Z9Z 9Z9` en Canadá,
`00000`. Si se derivaran, saldrían estados falsos con toda la confianza del mundo: `DISERA Laurel
Anne` vive en **New York** y su `99999` cae en el rango de **Alaska**. Ese error se detectó y se
paró; por eso están separados.

64 de los 68 son proveedores `VS9…` — parecen altas puntuales de consultores, con el postal
rellenado a comodín por diseño. Su **ciudad sí es real** (New York, San Diego, Stanford, Toronto),
pero de una ciudad no se deduce el estado sin ambigüedad: hay Springfield, Columbia, Newark,
Cambridge y Athens en varios estados a la vez. Hay que preguntarlo.

Los 4 restantes: `TechSmith Corporation` (Okemos, CP `00000`), `Paulette O'SULLIVAN` y
`Estelle ZADRA` (New York, CP `99999`), y **`Tim FRANCIS`, que sale marcado con un aviso**: el pago
viaja como US pero su ficha ADRC dice `FR`, París. Ése no es un problema de región sino de país,
y conviene mirarlo aparte.

## 5. Reparto de lo que se va a cargar

```
NY 72   QC 67   CA 29   ON 23   FL 21   DC 19   MA 19   VA 15   MD 14
NJ  9   TX  9   WA  6   IL  6   BC  6   PA  6   DE  5   NS  5   WI  5   ...
```

## 6. Cómo cargarlo

**Pocos proveedores, o para probar:** `XK02` uno a uno. Son 399, así que a mano es viable pero
tedioso.

**En masa:** `XK99` (mantenimiento masivo de acreedores) o una carga LSMW/eCATT sobre la dirección.
El campo objetivo es `ADRC-REGION` de la `ADDRNUMBER` que da el CSV. **Confírmalo con quien
mantenga el maestro** — no he verificado qué vía está habilitada aquí, y prefiero decirlo a
suponerlo.

**Empieza por los de más pagos.** El CSV ya viene ordenado por `pagos_2026` descendente:
`GRAEBEL COMPANIES` (76 pagos, CO), `UNITED NATIONS` (64, NY), `COMINAR REAL ESTATE` (56, QC),
`UNICEF` (52, NY), `Globex Courrier Express` (52, QC).

## 7. Cómo comprobar que quedó bien

```bash
python Zagentexecution/quality_checks/structured_address_readiness.py --origin FI-AP --csv proveedores.csv
```

Los proveedores cargados deben desaparecer de la lista. Y sobre un pago real, el fichero debe
emitir `<CtrySubDvsn>` dentro del `<Cdtr><PstlAdr>`.

## 8. Lo que este arreglo NO cubre

Estos 467 son **sólo US y CA**, que son los urgentes porque allí el estado es parte de la
dirección. El total de proveedores sin región pagados por fichero es **8.149** en todos los rails
(CITI 4.357 · CGI 4.114 · SEPA 3.354 · ICTP 3.354).

Para el resto conviene separar antes los que ya llevan la región dentro de `CITY1`: como Citi
concatena `TwnNm` + coma + `CtrySubDvsn` en una sola línea, un `CITY1='Holland, MI'` produce
**exactamente la misma Línea 2** que la versión bien partida. Para Citi son inocuos y pueden
esperar. Los urgentes son los que no tienen la región en ninguna parte.
