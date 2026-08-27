---
name: mining-canal-y-actor
description: >
  Mineria de tipo CANAL_Y_ACTOR: por donde ENTRA el trabajo al sistema y QUIEN lo mueve: interfaces, satelites, sesiones de batch input, personas frente a herramientas.
  Reune los 13 mineros de esta clase con su comando exacto y su modo de fallo.
  Usala cuando la pregunta sea de ESE tipo, sea cual sea el dominio: estos
  instrumentos se especializan por FORMA DE EXPLORAR, no por tema.
when_to_use: >
  antes de escribir un script que explore canal y actor · cuando quieras saber si
  esto ya se ha minado · cuando un instrumento de esta clase devuelva 0 o verde
---

# Mineria: CANAL_Y_ACTOR

**Qué contesta esta clase:** por donde ENTRA el trabajo al sistema y QUIEN lo mueve: interfaces, satelites, sesiones de batch input, personas frente a herramientas.

> Generado por `scripts/build_mining_skills.py` desde
> `brain_v2/methods/algorithms.json`. **No edites este fichero**: se
> regenera. Lo que se edita es la ficha del minero.

## Antes de correr ninguno

**Lee el `modo de fallo` del minero ANTES de correrlo, no después.** Todos los
de esta lista pueden devolver una cifra verosímil y falsa; el modo de fallo dice
cómo. Y si un minero devuelve **0**, la pregunta no es «no hay» sino «¿puede
verlo este instrumento?» — declara `UNOBSERVABLE`, nunca cero.

## Los 13 mineros de esta clase

### `A22_domain_composition`

**Contesta:** abrir un dominio: de que objetos esta hecho, quien lo conduce, cuando, por que canal, si LEE o MODIFICA, y que aplicacion hay detras del usuario tecnico

```bash
python brain_v2/domain_composition.py
```

**Cómo da una respuesta falsa:** AGREGAR SIN ABRIR INVIERTE LA IMPORTANCIA. PS salia con 3.501.373 ejecuciones, el 39,1% de toda la actividad de negocio, mas que FI y HCM juntos: parecia el corazon del sistema. Abierto, el 99,7% de su trafico RFC son DOS objetos con UN actor -- un satelite leyendo datos financieros de WBS en bucle. Un porcentaje por dominio es un numero sin proceso dentro. | Y el eje LEE/MODIFICA se deriva con la EVIDENCIA por…

**Aterriza en:** brain_v2/domain_composition.json (dataset) -> claims + capability_model A_PROCESS y U_USAGE

### `A23_channel_discovery_by_traffic`

**Contesta:** descubrir canales de entrada por su TRAFICO y no por su configuracion, y separar maquina de persona con una senal medible: una interfaz no hace logon de dialogo

```bash
python brain_v2/build_interface_inventory.py
```

**Cómo da una respuesta falsa:** DOS, y las dos producen un inventario que parece completo. (1) Derivar el inventario SOLO de la configuracion: rfcdes lista destinos SALIENTES y configurados, asi que un satelite que ENTRA autenticandose como usuario RFC no deja destino y es estructuralmente invisible -- EPAM-RFC llevaba 127.832 eventos desde dos IPs fijas sin figurar en ninguno de los 300 registros. (2) Separar maquina de persona por el NOMBRE: el…

**Aterriza en:** brain_v2/interface_inventory.json (canal RFC_INBOUND_OBSERVED) -> brain_v2/claims/claims.json - un canal de datos que el mapa de integracion no tenia es un…

### `A27_interface_nature`

**Contesta:** poner a cada interfaz DOS ejes: el dominio (donde pasa) y la NATURALEZA (que le hace al sistema: LECTURA, TRANSACCIONAL, MASTER_DATA o NO_MEDIBLE). El dominio sale de lo que el canal MUEVE de verdad -- los modulos que llama, ponderados -- no de su nombre

```bash
python brain_v2/build_interface_inventory.py
```

**Cómo da una respuesta falsa:** LO QUE TODOS LOS CANALES MUEVEN NO DICE PARA QUE SIRVE ESTE CANAL. Con el voto por numero de llamadas sin filtrar, RFCPING y RFC_READ_TABLE ganaban: UBO-RFC salia 63% 'sustrato tecnico' cuando en realidad es 100% Treasury_EBS, y MULESOFT 59,6% PS en vez de 89,9%. Excluida la fontaneria, el sustrato solo decide cuando NO hay ninguna llamada de negocio -- y entonces es la respuesta buena: EPAM-RFC no tiene ni una, es…

**Aterriza en:** brain_v2/interface_inventory.json (campos domain/domain_basis/nature/nature_basis)

### `A31_bdc_channel_mining`

**Contesta:** descubrir quien genera sesiones de batch input, de donde vienen y a que dominio pertenecen: por PROGID el programa generador, y para las externas por RFC (SAPMSSY1) abriendo el GROUPID, que es lo unico que la sesion externa trae

```bash
python process_mining/bdc_channel_mining.py
```

**Cómo da una respuesta falsa:** APQI ES UNA COLA, NO UN ARCHIVO: LAS SESIONES QUE SE PROCESAN BIEN SE BORRAN. Lo que queda es lo que fallo, lo que nadie corrio y lo reciente, asi que ninguna cifra de aqui es 'cuanto batch input se hace' sino 'cuanto QUEDA VISIBLE'. Confundir las dos produjo una conclusion falsa el 2026-08-24 -- se concluyo que el batch input era sobre todo viajes, cuando lo que pasa es que las de viajes fallan mas. | Segundo:…

**Aterriza en:** brain_v2/bdc_channel.json

### `A42_fm_executed_census`

**Contesta:** Contrasta el catalogo estatico de PSM-FM contra la evidencia de EJECUCION real y responde, por objeto: quien lo corre, por que canal (dialogo / report / RFC-BAPI / job batch) y cuanto. De ahi salio que solo el 15,7% de las 1.331 transacciones FM del catalogo esta viva (473 ejecutadas), que el canal…

```bash
python process_mining/fm_executed_census.py
```

**Cómo da una respuesta falsa:** MEDIDO CORRIENDOLO (2026-08-26, Gold DB 28.580.216 filas). `TXSUBCLSID='Transaction Start'` NO significa "arranco una transaccion". El filtro de la linea 78 devuelve 1.235.225 filas de CINCO clases distintas: AU3 1.123.933 (arranque real) · DU9 79.110 (acceso generico a tabla: PARAM1 es un NOMBRE DE TABLA tecleado en SE16/SE11/SE16N/SQVI) · CUI 24.619 y CUJ 586 (arranque y FALLO de aplicaciones WebDynpro, PARAM1…

**No puede ver:** No puede decir CUANDO ni con que cadencia (no agrupa por SAL_DATE aunque el campo esta: sin eje temporal no separa vivo de muerto, que es justo lo que R_S4_READINESS necesita). No puede decir a que PROCESO sirvio cada ejecucion -- el propio doc de metodo avisa de que objeto<->proceso es…

**Aterriza en:** brain_v2/fm_executed_census.json -- EXISTE, esta commiteado y el script lo escribe; lo consume brain_v2/interpret_code.py, que promueve cada clave a una…

### `A45_actor_attribution_per_account`

**Contesta:** Dice, cuenta por cuenta, SI UNA ACCION SE PUEDE ATAR A UNA PERSONA. PARAMX lleva el `user=` que hay DETRAS de la cuenta tecnica, asi que la pregunta "¿este usuario generico esconde gente real?" deja de ser opinion y se mide: TRANSPARENT (la cuenta nombra llamantes reales), OPAQUE (una sola…

```bash
python brain_v2/build_security_posture.py
```

**Cómo da una respuesta falsa:** DECIDE LA CLASE CON UNA ASTILLA Y LA APLICA AL VOLUMEN ENTERO — y la astilla no falta, esta CORTADA. `derive_attribution` (brain_v2/build_security_posture.py:88-144) mide dos cosas distintas y las multiplica como si fueran una. `calls` es `COUNT(*)` de todas las filas de la cuenta (linea 111). La clasificacion solo mira las filas cuyo PARAMX rinde `user=` (linea 116 exige `PARAMX<>''`, linea 120 exige `if u`).…

**No puede ver:** No mide permisos: ningun componente de rol/perfil esta derivado (agr_1251 y usobt fuera; agr_users presente pero sin analisis). No dice si una cuenta OPAQUE hizo algo malo, solo que no se podria demostrar quien. No cubre mas alla de las 25 cuentas mayores — el LIMIT 25 es fijo y la cola larga queda…

**Aterriza en:** brain_v2/security_posture.json — REAL, existe y se escribe (14.545 bytes, 23/08/2026 18:28). Consumido por `brain_v2/system_profile/compose_profile.py`…

### `A46_mine_domain`

**Contesta:** Descubre, por DOMINIO, quien mueve de verdad cada objeto ejecutado y por que canal: separa el trabajo humano del que entra por satelite/RFC y del batch, con serie mensual, marca de objeto sin uso reciente y deteccion de extracciones ad-hoc por SAP Query. No dice que existe (eso ya lo dice el…

```bash
python process_mining/mine_domain.py
```

**Cómo da una respuesta falsa:** mine_domain.py — cuatro defectos MEDIDOS (2026-08-26, Gold DB p01_gold_master_data.db) que producen cifras verosimiles y falsas ya publicadas en .claude/skills/sap_process_mining/SKILL.md:129 y en brain_v2/domain_footprints/_index.json. (1) `dead` NO significa muerto, significa "no se ejecuto en el mes EN CURSO". mine_domain.py:155 fija `last_global = max(mes global)` = 202608, un mes cortado el dia 22 (SAL_DATE max…

**No puede ver:** No hace FLUJO: no hay caso, ni orden entre eventos, ni grafo de seguimiento — cuenta ejecuciones por objeto, no secuencias, asi que no puede decir que sigue a que ni donde se espera. No dice que HIZO una ejecucion: rsau registra el ARRANQUE, no los datos, ni el resultado, ni si termino bien; un…

**Aterriza en:** `brain_v2/domain_footprints/<DOMAIN>.json` + `_index.json` — el store EXISTE y se escribe (17 ficheros en el repo). Pero hacia el brain esta PENDIENTE:…

### `A49_tier2_sod`

**Contesta:** Descubre QUE PERSONAS CONCRETAS ejecutaron de verdad las dos mitades de un par de funciones incompatibles (SoD a nivel ACCION), a partir de lo que hicieron — no de lo que tienen autorizado. Es la mitad "actual" del angulo declarado-vs-real (research wwyujjqyk, modelo GRC funcion->accion->permiso) y…

```bash
python process_mining/tier2_sod.py
```

**Cómo da una respuesta falsa:** MEDIDO corriendolo (28.580.216 filas, span 20260203->20260822). Tres piernas; la primera es la grave. (1) UN "0 users in conflict" QUE NO ES LIMPIO, ES CIEGO. El script solo mira `TXSUBCLSID='Transaction Start'`: 1.235.225 filas de 28.580.216 = **4,3% de la tabla**. Fuera quedan 12.734.604 'RFC Function Call', 7.343.360 'Report Start' y 4.346.626 'RFC/CPIC Logon'. Consecuencia: 4 de las 5 reglas imprimen 0 y se leen…

**No puede ver:** No puede ver nada fuera del canal de dialogo. De las 8 clases de TXSUBCLSID medidas hoy lee UNA (Transaction Start, 1.235.225 filas) e ignora las otras 27,3 M — incluidas RFC Function Call (12.734.604) y Report Start (7.343.360). No puede decir si el usuario TENIA el derecho (no toca…

**Aterriza en:** PENDIENTE. El script solo imprime a stdout: no escribe ningun store, no publica en mining_bus, no alimenta mining_findings.json (lo unico que hay alli sobre el…

### `A59_bcm_dual_control_mining`

**Contesta:** encontrar los lotes de pago donde el que crea es el que aprueba (CRUSR=CHUSR) y -- lo que lo hace mineria y no un contador -- CLASIFICAR a cada operador por su FORMA DE TRABAJAR en vez de excluir a los 'usuarios batch'. Esa decision es todo el hallazgo: los dos de mas volumen no eran automatismos…

```bash
python Zagentexecution/analysis/bcm_dual_control_monitor.py
```

⚠️ **estado `WEAK`** — su salida NO se cita sin comprobarla.

**Cómo da una respuesta falsa:** CUATRO NARRATIVAS CABLEADAS QUE SE IMPRIMEN COMO SI FUERAN MEDIDA DE HOY. (a) `USER_PATTERNS` (lineas 46-54) es una clasificacion CONGELADA de la sesion #037 y `classify()` (62-63) devuelve en silencio 'Occasional / unclassified' para cualquier nombre nuevo: un operador que empiece manana sale como ocasional y el informe parece completo. (b) `historical_comparison` cablea 3.394 y 4.760 (lineas 247-250) y los vuelve…

**Aterriza en:** Zagentexecution/mcp-backend-server-python/bcm_dual_control_audit.json + .csv (bcm_dual_control_monitor.py:41 y 292). AVISO: aterriza DENTRO de la carpeta que…

### `A60_outbound_channel_availability`

**Contesta:** contestar la pregunta que ningun inventario nuestro contestaba: DE LOS 239 DESTINOS SALIENTES, ¿CUALES RESPONDEN AHORA MISMO? Parsea RFCOPTIONS (H host, I puerto, N path, s SSL, D usuario, Q auth), hace UNA peticion SIN CREDENCIALES por destino y clasifica la FORMA del fallo, que es el dato:…

```bash
python Zagentexecution/quality_checks/outbound_channel_availability_check.py
```

**Cómo da una respuesta falsa:** CONFUNDIR DISPONIBILIDAD CON USO, en los dos sentidos. 'Arriba' NO significa 'se usa': un destino vivo y sin trafico es indistinguible aqui de uno vivo y muy usado -- el trafico de un saliente se mide en el OTRO extremo. Y 'caido' NO significa 'incidente': muchos destinos estan configurados y nunca se usaron. Ademas: (a) un 200 en el endpoint de configuracion NO garantiza que la aplicacion funcione -- ADS puede…

**Aterriza en:** n/a - instrumento: contesta en PANTALLA (o --json), no produce artefacto persistente todavia

### `A62_lazy_generated_object_as_usage_proof`

**Contesta:** distinguir LO INSTALADO de LO VIVO usando la generacion PEREZOSA como prueba de uso. Un formulario Adobe compila a un grupo de funciones /1BCDWB/SM<8 digitos> que SOLO EXISTE si el formulario se ha renderizado de verdad EN ESE SISTEMA. Medido en P01: 43-50 SFPF custom instalados (censo por e071)…

```bash
python brain_v2/methods/algorithm_memory.json
```

**Cómo da una respuesta falsa:** CONFUNDIR /1BCDWB/SF* CON /1BCDWB/SM*: los SF son SMART FORMS y NO pasan por ADS -- meterlos en el censo de Adobe infla la poblacion y el radio de una caida. Y el numero NO trae nombre: el mapeo SM000000nn -> nombre de formulario vive en FPCONTEXT/FPLAYOUT, que NO estan extraidas al Gold DB (TNAPR tampoco existe, ni NAST, ni REPOSRC). Para nombrarlos hace falta una lectura nueva de P01 o el FM estandar…

**Aterriza en:** brain_v2/claims/claims.json

### `A8_change_to_executor_attribution`

**Contesta:** join a STATE-CHANGE stream to an EXECUTION stream on (user, day, hour) to derive WHAT WRITES a thing and through WHICH CHANNEL CHAIN. Scored by the phi coefficient over the slot contingency table, with an exclusivity constraint across classes. The channel is not a label but a CHAIN with evidence…

```bash
python process_mining/attribute_changes_to_programs.py
```

**Cómo da una respuesta falsa:** THREE SCORINGS WERE WRONG BEFORE ONE WAS RIGHT, and each failure is now a comment in the file. (1) RAW COINCIDENCE named a spool artifact as the writer of the largest class, because the RFC dispatcher runs constantly and coincides with everything. (2) LIFT fixed that and inverted the error: it rewards RARITY, so it ranked the real PBC engine below noise and filtered it out — HUNCALC0 runs on 91 of 108 days, so its…

**Aterriza en:** brain_v2/change_attribution.json (dataset) -> brain_v2/claims/claims.json + brain_v2/annotations/annotations.json - WHAT WRITES a thing, and through which…

### `F1_interface_boundary_analysis`

**Contesta:** enumerate the boundary (RFCDES / EDIDC / TBTCP / ICFSERVICE) and CORRELATE the configuration against observed traffic in the call stream. Configuration says what someone once set up; the call stream says what happens today; the GAP is the finding, in both directions.

```bash
python process_mining/interface_boundary.py
```

**Cómo da una respuesta falsa:** TRUNCATION: PARAMX is a FIXED-LENGTH field and SAP cuts the caller string when it does not fit — 'caller: host=HQ-SAP-P01_P01_00, dest=HQ-SAP-P01-1_P01_'. I had recorded this as 'the parse truncates names', which was WRONG ABOUT THE CAUSE: the regex extracts exactly what is stored, and no better pattern can recover a character the source never wrote. FIXED by reconciliation instead of parsing (caller_parse.py): a…

**Aterriza en:** brain_v2/interface_boundary.json (dataset) -> brain_v2/claims/claims.json - configuration that exists and never fires, and traffic with no configuration behind…

## Cómo se lee esta lista

Un minero **registrado que nunca se ejecuta es documentación**. Si corres uno
y descubre algo, aterrízalo donde dice `Aterriza en` — descubrir sin aterrizar
es pérdida por construcción.
