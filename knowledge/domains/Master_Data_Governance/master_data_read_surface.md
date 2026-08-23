# La superficie de LECTURA de los datos maestros

> Medido 2026-08-22/23 sobre 28,5M de filas de SM20/RSAU acumuladas. Fuente:
> `brain_v2/log_reality.json` (algoritmo A19). Todo lo de aquí es **MEDIDO**, no inferido.

## Por qué este documento existe

El dominio ya modela **cómo se crean** los datos maestros: quién los pide, quién los valida,
quién los crea y qué tareas dispara cada tipo de objeto después. Lo que no modelaba es **cómo
se leen y se sacan**, y esa mitad apareció sola al clasificar el log.

No se buscaba. Salió del cubo de *no clasificados* de A19: 44 nombres que ninguna gramática
reconocía y que resultaron ser **consultas guardadas con nombre**, cuyo nombre dice su
objetivo. Por eso está aquí y no en `BusinessPartner`: `BusinessPartner` es el maestro en sí —
categoría SCSA, mapeo KTOKK→AKONT. Esto es **gobierno**: quién puede sacar qué, por un canal
que no es ni un informe ni una interfaz declarada.

## Lo que hay: 42 consultas catalogadas sobre datos maestros

Son objetos `AQ<área><NOMBRE>` — SAP Query guardadas, no ad-hoc. Alguien las creó, les puso
nombre y quedan disponibles.

**Personal (infotipos PA):** `PA_IT0000` medidas · `PA_IT0001_V2` asignación organizativa ·
`PA_IT0002` datos personales · `PA_IT0007` horario · **`PA_IT0008_M` salario base** ·
`PA_IT0016` contrato · **`PA_IT0021` familia** · `PA_IT0027` distribución de costes ·
`PA_IT0041` fechas · `PA_IT0064` · `PA_IT0351` · `PA_IT0961` · `PA_IT2001`/`PA_IT2002` ausencias

**Estructura organizativa:** `OM_ORGUNITS` · `OM_OUNITMANAGE` · `OM_POSPERSSTR` ·
`OM_POSSTRUCT_B` · `OM_POS_SECTOR`

**Librería HR estándar:** `H2BIRTHDAYLIST` · `H2DATE_MONITOR` · `H2EDUCATION` ·
`H2FAMILY_MEMBERS` · `H2FLUCTUATIONS` · `H2JUBILEE_LIST` · `H2STAFF_CHANGES2`

**Proveedor / cliente / banco:** **`VENDOR_BANK`** · `VENDOR_ADDRESS` · **`CUSTOMER_BANK`** ·
`BANK_STATEMENT` · `CASH_JOURNAL` · `SAPQUERY/FKF1` (acreedor) · `SAPQUERY/FDF1` (deudor) ·
`SAPQUERY/FSF1` (mayor)

**Compras y activos:** `MEMEBANF` · `MEMEPO` · `MEME80FN` · `MEMEBESTWERTAN` · `SAPQUERY/AM01`

**Viajes:** `FTDESTINATIONS` · `FTREC_OVER_MAX`

## Y un segundo canal: navegación directa de tablas

Programas `/1BCDWB/DB<TABLA>` — el navegador genérico sobre una tabla concreta. Entre las
navegadas hay maestras: `ADR6` (correos), `ADRP` (personas), `BNKA` (bancos), `CSKA`/`CSKS`
(clases y centros de coste). También `AGR_USERS` y `AGR_1251`, que son roles.

**El nombre del programa no es el hallazgo: la TABLA lo es.** Un `/1BCDWB/DBADR6` indexado
como programa es un objeto fantasma; leído como lo que es, dice que alguien listó los correos
de la base de interlocutores.

## Por qué esto es gobierno y no una curiosidad

Tres cosas que el modelo de creación no cubre:

1. **`PA_IT0008` es salario base y `PA_IT0021` es familia.** Son las dos categorías más
   sensibles del maestro de personal, y existen como consulta catalogada.
2. **`VENDOR_BANK` y `CUSTOMER_BANK` son datos bancarios.** El dominio ya sabe que el canal de
   escritura sobre proveedores tiene conflictos de segregación; esto es el mismo objeto por el
   lado de la lectura.
3. **No es una interfaz declarada.** No aparece como destino RFC, ni como fichero, ni como
   servicio. Es una consulta que un usuario ejecuta, y por eso ningún inventario de interfaces
   la ve.

## Lo que NO se sabe todavía

- **Quién las ejecuta y cuántas veces.** Se sabe que existen y que se ejecutaron dentro de la
  ventana del log; falta el reparto por actor y su perfil temporal.
- **Si el resultado sale del sistema.** Ejecutar una consulta y descargarla a fichero son dos
  hechos distintos y el log de auditoría no distingue el segundo por sí solo.
- **Quién las creó y con qué autorización.** Una consulta guardada tiene autor.

Marcar esto como riesgo sin medir esas tres cosas sería exactamente el error que este proyecto
ya cometió una vez: leer una medida de cobertura como si fuera una medida de aplicabilidad.
Aquí está lo que hay, con su fuente, y lo que falta, con su nombre.

## Cómo se regenera

```bash
python process_mining/log_reality_filter.py    # A19, paso 2j del rebuild
```

Las consultas viven en `programs.carried_signal.SAP_QUERY_NAMED` y las tablas navegadas en
`programs.carried_signal.TABLE_BROWSER` de `brain_v2/log_reality.json`.

## Enlaces

- Método: `brain_v2/methods/algorithms.json` → `A19_log_reality_filter`
- Trampas aprendidas: `brain_v2/methods/algorithm_memory.json` → `rsau.SLGREPNA` (CARRIER)
- Agente que lo trabaja: `.claude/agents/log-process-discovery.md`
- Dominio hermano (el maestro en sí): `knowledge/domains/BusinessPartner/`
