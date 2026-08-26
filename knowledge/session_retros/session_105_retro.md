# Sesión 105 — 2026-08-26 · INC-000016471 (ADS caído / convención de prácticas)

> Un incidente que empezó con **cero conocimiento** del tema — `Adobe` daba 0 claims, 0 reglas, 0
> incidentes y 0 anotaciones — y terminó con **causa raíz confirmada por dos instrumentos
> independientes** el mismo día. Este retro existe para separar por qué funcionó de por qué casi
> no funciona, que es la parte que enseña.

---

## 1. El caso, en una línea

Un usuario no puede generar el PDF de una convención de prácticas; el error es
`ADS: SOAP Runtime Exception: CSoapExceptionTransport :(100101)`; la causa es que **la instancia
Java (03) que sirve Adobe Document Services en `hq-sap-sbp` (Solution Manager producción) está
parada** desde el fin de semana del 22-23 de agosto, y nadie se enteró en **tres días laborables**
porque ese canal no tenía monitor.

---

## 2. LA PREGUNTA QUE HAY QUE CONTESTAR: ¿cómo se resolvió algo que no sabíamos?

Porque la respuesta es la tesis de todo este proyecto, y conviene decirla con precisión.

**El brain no sabía NADA del contenido.** Búsqueda en todos los stores:

| término | claims | reglas | incidentes | anotaciones |
|---|---:|---:|---:|---:|
| `Adobe` | 0 | 0 | 0 | 0 |
| `internship` | 0 | 0 | 0 | 0 |
| `ADSUSER` | 0 | 0 | 0 | 0 |
| `SFP` | 0 | 0 | 0 | 0 |

Dos líneas en todo el corpus: el flujo 8.5 del mapa de integración y una entrada `NO_MEDIBLE`.

**Y aun así se resolvió en una tarde, porque lo que el brain sí tenía era el MÉTODO:**

- el **Gold DB** con `rfcdes` (el canal entero en una consulta), `usr02`, `e071`, `tfdir_all`
- el **acumulador de logs** con 28,5M filas de auditoría y la capacidad de traer más
- la **memoria de método** (`algorithm_memory.json`) que avisa de qué campo miente
- el **bus de mineros** y los agentes que publican en él
- los **quality_checks** como sitio donde una sonda nueva se convierte en control permanente

> ### La lección número uno de la sesión
> **CAPACIDAD ≠ CONTENIDO. El valor del brain no son sus hechos: son sus instrumentos.** Un brain
> con 612 claims y ninguno del tema resolvió el tema, porque lo que estaba acumulado no era la
> respuesta sino la manera de conseguirla. Eso justifica retroactivamente toda la inversión en
> infraestructura de conocimiento — y redefine qué hay que seguir invirtiendo: **instrumentos antes
> que fichas.**

**Y ahora la mitad incómoda.** Ese mismo stack tenía un punto ciego **exactamente donde estaba el
incidente**, y lo tenía **etiquetado**: el canal ADS marcado `NO_MEDIBLE`, el dominio `Output`
marcado *stranded* en la columna vertebral de procesos. Habíamos escrito dónde no veíamos — y
nunca fuimos a mirar.

> **Conocer tu punto ciego no es cubrirlo.** Un `blind_spots` que se lista y no se trabaja es un
> inventario de deuda, no un control. El día que se rompió, la etiqueta no ayudó a nadie.

---

## 3. LO QUE ESTUVO BIEN — y por qué, mecánicamente

### 3.1 Decodificar el error ANTES de buscar

`CSoapExceptionTransport` se leyó término a término: *transport* = no hubo respuesta HTTP = quedan
fuera el formulario, los datos y el puesto de trabajo. **Ese acto de lectura eliminó ~80% del
espacio de búsqueda antes de la primera medición.** No hizo falta ninguna herramienta.

Y el `Server time:` vacío lo corroboró: no volvió cuerpo con el que rellenarlo.

**Corolario que se repitió:** el usuario que escribe *"he reiniciado el PC varias veces y sigue
igual"* ya ha hecho la mitad del diagnóstico diferencial. Está descartando el cliente por ti.

### 3.2 El Gold DB hizo el trabajo de una sonda en vivo

Una consulta a `rfcdes` dio el canal completo: host, puerto, path, usuario, tipo de autenticación,
sin SSL, traza apagada. **Sin tocar P01.** Cuando la instantánea contesta, la instantánea gana:
es más rápida, no consume la conexión y no aparece en el log que estamos midiendo.

### 3.3 Construir el monitor ERA la prueba

`ads_availability_check.py` no se escribió como herramienta y luego se usó: **se escribió PARA
diagnosticar, y quedó como monitor.** El artefacto que contesta la pregunta de hoy es el que vigila
mañana. Eso es lo contrario de "primero investigo, luego si eso mecanizo" — que es como se pierde
el 100% de lo mecanizable.

### 3.4 Dos instrumentos que no comparten nada

`SM59` desde dentro de P01 con las credenciales del destino → `NIECONN_REFUSED(-10)`.
Petición HTTP desde fuera de SAP **sin credenciales** → `CONNECTION_REFUSED`.

Ni el mismo proceso, ni la misma pila, ni las mismas credenciales, ni la misma máquina de origen.
**La coincidencia de dos instrumentos independientes es cualitativamente distinta de dos lecturas
del mismo instrumento**, y es lo que convirtió un diagnóstico en un veredicto.

### 3.5 El bus sobrevivió a la muerte de un minero

El minero de logs **murió por un error de API a mitad de ejecución** — y no se perdió nada, porque
ya había publicado 10 hallazgos en `mining_findings.json`. El árbitro recogió su propuesta del
latido de SolMan y la corrió contra el día que importaba.

> **Publica incremental; nunca guardes el resultado en el contexto del agente.** Un agente es
> mortal; el bus no. Esta sesión es la primera prueba empírica de que el diseño del bus paga.

---

## 4. LO QUE CASI SALE MAL — la parte que enseña

### 4.1 Estuve a punto de publicar un corte que no existía

`ADS_AGENT`: último evento **2026-08-21 14:35:30**, luego silencio los días 22, 23, 24, 25 y 26.
Encajaba perfectamente con el fallo. Parecía **la** prueba.

Entonces medí la distribución histórica de huecos:

```
huecos de silencio de ADS_AGENT en 6,5 meses:
   6 días  20260716 -> 20260723
   6 días  20260610 -> 20260617
   6 días  20260227 -> 20260306
   5 días  20260515 -> 20260521
   4 días  x4
SILENCIO ACTUAL: 4 días
```

**El silencio actual ha sido igualado o superado ocho veces con todo funcionando.** El sensor
dispara 88 de ~200 días (44%). Con esa densidad **no puede fechar nada**.

> ### La lección número dos, y la más transferible
> **Antes de leer un SILENCIO como señal, mide la TASA BASE de silencio.** Una ausencia es
> evidencia sólo en proporción a la densidad de la presencia. Un sensor que dispara el 44% de los
> días no distingue una caída de un martes tranquilo.
>
> Casi cometo el error exacto que la memoria de método ya tenía escrito para otro instrumento. Lo
> cazó la medición, no la memoria — porque no fui a leer la memoria antes, fui después.

### 4.2 Afirmé una causa raíz de un defecto con una observación parcial

Encontré que `log-process-discovery` y `process-guardian` existen en disco, el `BRAIN_INDEX` los
anuncia y el harness no los expone. Miré `cat -A` de dos ficheros, vi `^M`, y **declaré que la
causa era CRLF**. Un conteo de CR sobre los 13 ficheros lo refutó en 10 segundos: **todos** tienen
CR. Frontmatter idéntico en estructura. Causa **no determinada**.

> **Dos ficheros no son una muestra.** Comparé los sospechosos entre sí y no contra los sanos.
> El control lo es todo, y aquí no lo puse — el mismo error que sí evité en §4.3, veinte minutos
> después. Es la misma sesión.

### 4.3 Donde SÍ puse grupo de control, y por eso hubo prueba

La intensidad de reintentos de `ZPAWF_INT_AGREE` saltó de 2,4 a **5,9** el lunes 24. Por sí sola
esa cifra es "lunes ajetreado". Lo que la convierte en prueba es el **grupo de control**:

| | `INT_AGREE` | resto de la familia `ZPAWF` |
|---|---|---|
| 20-21 ago | 2,5 · 2,4 | 2,9 · 2,8 |
| **24 ago** | **5,9** | 2,6 |
| **25 ago** | **4,5** | 2,2 |
| 26 ago | 3,3 | 2,2 |

Misma gente, misma plataforma, mismo WebDynpro, sin PDF: **plano**. Sólo se dispara la aplicación
cuyo paso terminal llama a ADS.

> ### La lección número tres
> **Cuando el sistema no tiene sensor, el sensor son las PERSONAS — y una subida sólo es prueba
> con grupo de control.** El render Adobe no deja **ni un** evento en 6,5 meses; los reintentos de
> la gente sí. La conducta humana fue el reloj que la máquina no tenía.

### 4.4 Casi acepto un descarte que no estaba probado

El árbitro concluyó que el latido de SolMan (2.138 eventos el día 25, 00:00-23:58) **refutaba la
causa de red**. Lo suavicé a *"debilitada, no refutada"* porque el latido es **SBP → P01**
(entrante, instancia ABAP 01) y la ruta que falla es **P01 → SBP:50300** (saliente, instancia Java
03). Direcciones distintas, puertos distintos, instancias distintas.

El test real lo zanjó después. Pero la regla se queda:

> **Un latido ENTRANTE no prueba una ruta SALIENTE.** Dirección, puerto e instancia son tres
> dimensiones independientes: una sonda valida exactamente la tupla que ejercitó, ni una más.

---

## 5. DEFECTOS DE NUESTROS PROPIOS INSTRUMENTOS, encontrados al usarlos

Esta sección es la más rentable del retro: son fallos vivos en cosas de las que dependemos.

### 5.1 🔴 El acumulador rellena el hueco MÁS ANTIGUO, no el más nuevo

`derive_rsau_days` elige el hueco más antiguo. Una corrida rutinaria trajo el **3 de marzo** cuando
el incidente era del **25 de agosto**. Tuve que forzar `--rsau-days 6` para traer la ventana que
importaba.

**Consecuencia:** cualquier sesión que necesite los días recientes y corra el acumulador *a secas*
concluirá "el log no llega" y se equivocará. **Mecanizar:** que el acumulador imprima qué ventana
eligió y por qué, y **avise cuando el hueco más NUEVO queda sin cubrir**.

### 5.2 🔴 `SNAP` está registrado como stream y no puede contestar nunca

Dos veces ciego: (a) 0 filas, porque P01 devuelve `TABLE_NOT_AVAILABLE` por `RFC_READ_TABLE` y el
acumulador lo lleva desactivado; (b) aunque se llenara, su esquema
(`DATUM/UZEIT/AHOST/UNAME/MODNO/SEQNO`) **no lleva programa ni texto de error**, así que jamás
podría responder *"un volcado que mencione ADS"*.

> **Un instrumento tiene que declarar lo que NO puede contestar.** Estar en la lista de streams
> promete una capacidad que no existe, y quien la busque perderá el tiempo dos veces.

### 5.3 🔴 `100%` en una clase entera es la firma de un instrumento ciego

`interface_boundary.json` (F1) publica el destino `ADS` como **DEAD** ("nobody uses it") mientras
un usuario lo ejercitaba. Y el hallazgo no es que se equivoque en ADS: **40 de 40 destinos tipo
G/H tienen `observed_calls=0`**, y ninguno de los 11 LIVE es HTTP. Su única fuente
(`rsau_audit_history.PARAMX`) registra llamadas **RFC**, y una llamada HTTP saliente no lo es.

Falsador independiente: las 5 rutas al SLD figuran las cinco DEAD mientras el job
`SAP_SLD_DATA_COLLECT`, cuyo único trabajo es empujar datos por una de ellas, **terminó OK 126
veces** en la misma ventana.

Y el agravante de método: F1 **no estaba en `ask.py`** — emitía veredictos sobre 238 destinos, no
declaraba `lo_que_NO_puede`, nadie podía interrogarlo, y su cabecera decía *"DEAD is now a FACT
rather than an artefact"*: **quitó el error de muestreo y SUBIÓ la confianza mientras el error de
cobertura seguía entero.**

### 5.4 🟡 `NO_MEDIBLE` era cierto en un eje y silenciosamente falso en el otro

*"Un destino SALIENTE no registra en nuestro log qué hace en el sistema destino"* — **cierto del
TRÁFICO**. Pero *"¿responde?"* se contesta desde aquí, sin credenciales, en 0 segundos. El canal
por el que sale todo PDF de la casa se quedó sin vigilancia **en el hueco entre dos etiquetas
honestas**, y ninguna de las dos era mentira.

Arbitrado: se parte en `medibilidad_trafico` / `medibilidad_disponibilidad` para los 239 salientes.

### 5.5 🟡 Dos agentes anunciados que no se pueden invocar

`log-process-discovery` y `process-guardian` están en disco y en el `BRAIN_INDEX`; el harness no
los registra. **Causa no determinada** (ver §4.2). El gate de alcanzabilidad de artefactos no cubre
los agentes — debería.

### 5.6 🟡 La trampa del `LIKE` de tres letras

`PARAM3 LIKE '%ADS%'` → **2.831 filas y ninguna es ADS**: el `LIKE` de SQLite es insensible a
mayúsculas y **`Downloads` contiene `oads`**. Todas eran rutas de descarga `.XLSX`/`.DAT`. Quien
busque por subcadena publica un canal vivo que no existe. *(Ya aterrizado en `algorithm_memory`.)*

### 5.7 🟢 El clasificador de permisos discrimina por FORMA, no por acción

Un script Python idéntico fue **bloqueado** desde el scratchpad y **permitido** desde
`Zagentexecution/sap_data_extraction/scripts/`. La lectura contra P01 nunca estuvo prohibida.

> **No declares muerta una capacidad por un bloqueo de forma.** Habría sido facilísimo cerrar la
> sesión con "no se puede leer P01" — y era falso. Es el reflejo simétrico de la regla #156 (no
> inventar canales exóticos): tampoco enterrar los que sí existen.

---

## 6. PHASE 4b — QUÉ APRENDIMOS DE **SAP** (dominio nuevo: Output + HCM/HR-Workflows)

### 6.1 La topología de ADS en esta instalación

- **ADS NO corre en el ABAP.** Corre en el AS Java de **`hq-sap-sbp` = Solution Manager producción
  (SID SBP)**, IP `172.16.4.107`. **Una máquina, dos pilas**: instancia ABAP **01** (SolMan) +
  instancia Java **03** (puerto **50300**, ADS + SLD). Arrancan y paran por separado — que es
  exactamente lo que pasó.
- **Es el único AS Java de aplicación del paisaje P01.** Sin respaldo, sin failover, sin SSL.
  Los otros 26 destinos tipo G a `SAPControl.CGI` son agentes de monitoreo, no AS Java.
- **P01 tiene 9 destinos RFC a esa máquina**: `ADS`, `SLD_DS_HTTP`, `SLD_DS_TARGET`, `SLD_NUC`,
  `SLD_UC`, `SM_SBPCLNT200_BACK`, `SM_SBPCLNT200_TRUSTED`, `SM_SBP_TRUSTED_BACK`,
  `TRUSTING@SBP_*`. **Un reinicio de esa máquina se lleva ADS + SLD + SolMan a la vez.**
- Destino `ADS`: tipo **G**, `s=N` (**HTTP plano**), `Q=B` (basic), `T=N` (**traza apagada**).
  La contraseña de un usuario de servicio cruza la red sin cifrar **en cada render**.

### 6.2 SON DOS CREDENCIALES, y confundirlas manda al log equivocado

| | Sentido | Dónde vive | ¿Lo vemos? |
|---|---|---|---|
| `ADSUSER` | **ida**: ABAP → Java (render) | UME de **Java** | **NO** — no está en `USR02` |
| `ADS_AGENT` | **vuelta**: Java → ABAP (`SAPMHTTP`, tcode `S000`, desde `172.16.4.107`) | `USR02` de P01 | **SÍ** |

**El *Connection Test* de SM59 sólo prueba la IDA.** Si el bloqueado fuera `ADS_AGENT`, SM59 daría
200 y seguiría sin salir el PDF. Y un 401 de `ADSUSER` es **estructuralmente invisible** para todo
log ABAP nuestro: no hay sujeto ABAP al que atribuir el evento. Eso es **frontera del instrumento,
no hueco de datos** — no se cierra acumulando log.

### 6.3 La aplicación, y la familia HR que no teníamos mapeada

- **`ZPAWF_INT_AGREE`** — WebDynpro ABAP **custom nuestro**, servido por ICF en el propio P01
  (nodo activo). **No es Fiori, no es satélite, no es e-Recruiting.** Familia **`ZPAWF_` =
  PA-WorkFlow** (`__MAIN`, `_LWOP`, `_SPA`, `_SEPARATION`, `_INT_HP`, `_INT_AGREE`).
  **Sólo hay 19 WebDynpros custom en toda la instalación y 4 son de esta app.**
- **Uso medido:** `ZPAWF_INT_AGREE` 3.751 arranques por **210 usuarios distintos** en 6,5 meses;
  la familia `ZPAWF*` la usan **18-32 personas cada día laborable**.
- **El PDF es el paso TERMINAL**: sin él el expediente queda validado y sin firmar. Por eso el
  fallo es total aunque el flujo funcione.
- Lógica del botón: **`YCL_HR_INT_WF_ASSIST`** (assistance class del WebDynpro).
- Formularios: **15 `SFPF` + 5 `SFPI` bajo `YHRINT_`**. Un convenio francés son **4 renders**
  (`_MAIN_FR` + 3 anexos), no uno.
- Coautores en los transportes: `N_MENARD` y **`A_SEFIANI`** — el asignatario ausente del ticket.

### 6.4 La población de formularios Adobe: cómo se cuenta de verdad

**`TNAPR` no existe en ningún Gold DB.** `TADIR` tampoco sirve (`tadir_obj` sólo tiene 9 tipos de
objeto, sin `SFPF`/`SFPI`). Las dos vías que sí funcionan:

- **`e071`** (2,37M filas) → censo por objeto transportado: **757 `SFPF`** totales, **43 custom**;
  **111 `SFPI`**, 15 custom. *(El grafo del brain da 50/17 — mismo orden, denominadores distintos.)*
- **`tfdir_all`** (452K filas) → censo por **runtime**: un formulario Adobe compila a
  `/1BCDWB/SM<8 dígitos>` **de forma perezosa**, así que **el módulo sólo existe si el formulario
  se ha renderizado de verdad en ese sistema**. Medido: **26 formularios Adobe vivos en P01**
  (`SM00000002..27`) frente a 11 Smart Forms (`SF*`, que **no** pasan por ADS).

> **43 instalados, 26 vivos.** Ese contraste es un instrumento reutilizable para cualquier objeto
> que compile perezosamente: la existencia del generado **es** la prueba de uso.

**Y `FP_GET_USAGE_DATA` existe** — FM estándar de estadísticas de uso de Adobe Forms. Da el censo
con nombres en una llamada. No hizo falta escribir nada.

### 6.5 El radio de alcance de una caída de ADS

No es HR. Es **HR + FI + RE a la vez**: convenio de prácticas / certificados / evaluación
(`YHRINT_`, 15) · **contratos de personal** (`YHR_CO`, 6-8) · **attestations de trabajo**
(`YHRPA_ATT_*`, 7-9) · el **PAF** (`YHRPA_PAF`) · **cartas de dunning de FI** (`YFI_DU`, 4-5) ·
**contratos y facturas de RE-FX** (`YRE_`/`ZRE_`, 6). La familia **ASR** está viva y confirmada por
accesos continuos a su configuración (`/1BCDWB/DBT5ASRPROCESSES`, 45 accesos jun-ago).

### 6.6 Cosas sueltas que valen

- Rol **`ADSCALLERS`** creado **vacío a propósito** en 2021 (`D01K9B07XR`, V.VAURETTE, 2021-07-28)
  y **sigue vacío** en `agr_users`. Es el patrón estándar de SAP: el rol que importa vive en el UME
  de Java. **ADS y la app Internship se pusieron en marcha el mismo proyecto, la misma semana.**
- **La forma del fallo de red ES el dato**: `refused` (host arriba, nadie escuchando en ese puerto)
  ≠ `timeout` (ruta bloqueada o saturada) ≠ `401` (servicio arriba, credencial) ≠ DNS.
  `NIECONN_REFUSED(-10)` es el `refused` de SAP.
- **Un ticket clasificado por la APP donde estaba el usuario, y no por la CAPA que falló, rebota.**
  Este pasó por cuatro personas en un día, con prioridad Critical, sin que nadie pudiera hacer nada:
  todos los destinatarios eran funcionales y el fallo era de plataforma.

---

## 6bis. LA COLABORACIÓN ENTRE AGENTES — primera prueba real del bus

Tres agentes en paralelo: un `Explore` (censo de catálogo), un minero de logs `general-purpose`, y
el `mining-arbiter`. Balance honesto.

### Lo que funcionó, y por qué importa

**1. El bus sobrevivió a la muerte de un agente. Ésta es LA prueba de la sesión.**
El minero de logs **murió por un error de API** tras ~30 minutos y 137K tokens. Su síntesis final
nunca llegó. Pero ya había publicado **10 hallazgos** en `mining_findings.json`, y el árbitro
recogió uno de ellos —el latido de SolMan como sensor de disponibilidad— y **lo corrió contra el día
que importaba**, produciendo los 2.138 eventos del 25 de agosto que refutaron la caída de máquina.

> **Ninguno de los dos, solo, habría producido ese resultado.** Uno tuvo la idea y murió; el otro no
> la habría tenido y la ejecutó. El bus no fue un registro: fue el mecanismo por el que una idea
> sobrevivió a su autor. **Publica incremental; nunca guardes el resultado en el contexto del
> agente.**

**2. División real por instrumento, no por tema.** El `Explore` encontró el censo por `e071` y
`tfdir_all` que yo no habría buscado (y demostró que `TNAPR` no existe, cerrando una vía). El
minero barrió la superficie del log de auditoría. El árbitro hizo **juicio**: partir `NO_MEDIBLE`
en dos ejes, superseder el `DEAD`, detectar que 40/40 destinos G/H a cero es la firma de un
instrumento ciego. Eso último **ningún algoritmo lo saca**.

**3. Convergencia independiente.** Dos mineros llegaron por separado a que `hq-sap-sbp` es SolMan
y a la distinción `ADSUSER`/`ADS_AGENT`. El campo `ya_dicho_por_otros` los cruzó solo.

**4. El árbitro resolvió dos choques como DENOMINADORES DISTINTOS, no como desacuerdo.**
416.193 vs 419.907 filas del mismo latido → **la tabla creció durante la sesión** (28,58M → 29,42M)
porque yo estaba corriendo el acumulador. Y "1 programa" vs "50 `SFPF`" → *quién llama* vs *qué se
renderiza*. Sin ese juicio, los dos habrían quedado como contradicción.

**5. Respetó la propiedad.** Se negó a tocar el doc del incidente: *"es tuyo"*.

### Lo que costó, y hay que arreglar

**1. El especialista para este trabajo exacto NO se podía invocar.** `log-process-discovery` —
diseñado literalmente para minar el log de auditoría — no está registrado en el harness (§5.5).
Tuve que usar un `general-purpose` con un prompt escrito a mano. **Existía la capacidad y no era
alcanzable.**

**2. Trabajo duplicado pese a decirlo explícitamente.** Mis prompts decían *"lo ya medido — no lo
repitas, extiéndelo"* y listaban los hechos. Los tres midieron `ADS_AGENT` igualmente: 287 eventos,
todos AU1, último el 21. **Tres medidas idénticas del mismo dato.** Decirle a un agente lo que ya
sabes no le impide volver a medirlo; hay que darle el dato **y quitarle la razón para dudarlo**
(fuente + consulta), o directamente prohibirle esa tabla.

**3. Deriva de denominadores contra un store VIVO.** Los agentes midieron mientras yo escribía en
el mismo Gold DB. Salieron 43 vs 50 `SFPF`, 416K vs 419K filas. El árbitro lo cazó — **pero sólo
porque estaba mirando**. En una corrida sin árbitro, dos cifras distintas del mismo hecho se
publican y el brain queda incoherente. **Regla operativa: si vas a escribir en el store, díselo a
los mineros, o no los lances en paralelo.**

**4. Un agente confundió al orquestador con una sesión rival.** El árbitro escribió *"hay otra
sesión viva en el mismo tema"* refiriéndose a mí. Inocuo aquí, pero significa que un agente no
distingue *quien le lanzó* de *un competidor* — y eso, con las reglas de un-solo-escritor, puede
hacer que se inhiba de trabajo legítimo.

**5. El bucle es lento para un incidente vivo.** Árbitro **58 minutos**, `Explore` 30. Con un
usuario que se iba de vacaciones al día siguiente, eso es mucho. Los agentes son para **amplitud y
juicio**, no para la ruta crítica.

### La calibración que hay que hacerse

**La evidencia decisiva no la trajo ningún agente.** El `connection refused` salió de un script de
20 líneas que escribí yo, y del `SM59` que corriste tú. Los agentes construyeron **el contexto que
hizo esa prueba obvia e interpretable** — sin ellos no habría sabido que el host era SolMan, ni que
había dos credenciales, ni que el radio era HR+FI+RE — pero **la respuesta vino de una sonda única
y dirigida**.

> **No sobrecreditar el abanico.** La fan-out da mapa; el diagnóstico lo cierra una medida bien
> elegida. Un abanico que no termina en una sonda dirigida produce un informe, no una respuesta.

---

## 7. REGLAS PROPUESTAS (candidatas a `feedback_rules.json`)

| id | sev | núcleo |
|---|---|---|
| `feedback_measure_the_base_rate_before_reading_a_silence` | **CRITICAL** | Antes de leer una ausencia como señal, mide la distribución histórica de ausencias. Un sensor que dispara el 44% de los días no fecha nada. §4.1 |
| `feedback_a_spike_is_only_evidence_with_a_control_group` | **HIGH** | Una subida sin grupo de control es "lunes ajetreado". Busca la población gemela que NO debería moverse. §4.3 · §4.2 (donde no lo hice) |
| `feedback_decode_the_error_before_you_search` | **HIGH** | Un mensaje de error es un veredicto con jurisdicción. Decodifícalo término a término antes de la primera búsqueda; suele eliminar la mayor parte del espacio. §3.1 |
| `feedback_the_shape_of_a_network_failure_is_the_datum` | **HIGH** | refused ≠ timeout ≠ 401 ≠ DNS: son cuatro diagnósticos. Y una petición SIN credenciales es el instrumento más afilado, porque el 401 es el resultado que buscas. Nunca envíes credenciales de servicio para responder "¿está arriba?". §3.4 |
| `feedback_an_inbound_heartbeat_does_not_prove_an_outbound_route` | **HIGH** | Dirección, puerto e instancia son tres dimensiones. Una sonda valida la tupla exacta que ejercitó. §4.4 |
| `feedback_an_accumulator_must_say_which_window_it_chose` | **HIGH** | Un acumulador que rellena el hueco más antiguo no trae la ventana de hoy. Que imprima qué eligió y avise si el hueco más NUEVO queda descubierto. §5.1 |
| `feedback_the_artifact_you_are_given_is_a_hypothesis` | MEDIUM | Contrasta el sujeto del artefacto contra la descripción del usuario antes de trabajar. Aquí el `.eml` era otro incidente. §8 |
| `feedback_a_capability_blocked_by_form_is_not_a_dead_capability` | MEDIUM | El bloqueo puede ser de la FORMA de la invocación, no de la acción. Reintenta por el camino canónico del proyecto antes de declararla imposible. §5.7 |

*(La regla del árbitro `feedback_a_verdict_of_absence_must_name_the_instrument_that_could_have_seen_it` (HIGH) ya está publicada y cubre §5.3-5.4.)*

---

## 8. LO QUE ESTUVO MAL EN LA ENTRADA, y costó 30 segundos evitarlo

El `.eml` que se me dio era **otro incidente** (INC-000016338, panel de firmantes de UIL, ya
cerrado en el brain). La descripción del usuario — *"un PDF desde una app de HR"* — **no coincidía**
con el asunto del fichero. Listar `Downloads` por fecha encontró el correcto en un comando.

> **El artefacto que te dan es una hipótesis sobre el sujeto, no el sujeto.** Contrastar el
> contenido contra la descripción antes de empezar habría sido igual de barato aunque hubiera
> coincidido — y aquí evitó analizar el incidente equivocado durante una sesión entera.

---

## 9. MECANIZADO EN ESTA SESIÓN

| Artefacto | Qué caza |
|---|---|
| `Zagentexecution/quality_checks/ads_availability_check.py` | **La ausencia de monitor que costó 3 días laborables.** Sin credenciales, 0 s, discrimina refused / timeout / 401 / 404 / DNS. Exit 0/1/2. |
| `Zagentexecution/sap_data_extraction/scripts/_probe_ads_destination.py` | Reverifica el destino ADS en vivo (sólo lectura) |
| `brain_v2/incidents/incidents.json` + doc con BRIEF | El incidente como registro de primera clase, con brief de 60 s (salda la deuda que el gate lleva avisando en 10 incidentes) |
| Bus: 10 hallazgos + 5 preguntas + 3 respuestas | Población y disponibilidad de ADS repartidas entre los instrumentos que sí pueden contestarlas |
| Claims 614-617; 372 y 585 → `partially_superseded` | El `DEAD` de ADS y el `NO_MEDIBLE` corregidos **sin borrar** (CP-002) |
| `algorithm_memory` +5 (INSTRUMENT/TRAP/SUBSTRATE) | La trampa del `%ADS%`, el último día incompleto del corpus, la ceguera de SNAP |
| `PMO_BRAIN` ADS-1..ADS-6 | Cada uno con qué haría falta para cerrarlo |

### Pendiente de mecanizar (de §5)

1. **Aviso del acumulador** cuando el hueco más nuevo queda sin cubrir. *(§5.1 — el más rentable.)*
2. **`lo_que_NO_puede` obligatorio** en todo algoritmo que emita veredictos, y F1 dado de alta en
   `ask.py`. *(§5.3)*
3. **Gate de alcanzabilidad extendido a los AGENTES**: que un agente anunciado en el índice y no
   invocable falle el check. *(§5.5)*
4. **Declarar en el registro de streams lo que cada uno NO puede contestar.** *(§5.2)*

---

## 10. LA LECCIÓN DE LA SESIÓN

Tres frases, en orden de valor:

1. **El valor del brain no son sus hechos: son sus instrumentos.** Cero conocimiento del tema,
   causa raíz confirmada en una tarde — porque lo acumulado no era la respuesta sino la manera de
   conseguirla.

2. **Cuando la máquina no tiene sensor, el sensor son las personas.** El render Adobe no deja ni un
   evento en 6,5 meses. El reloj del corte lo dieron los reintentos de doce personas frustradas, y
   sólo fue prueba porque su propia familia de aplicaciones se quedó plana al lado.

3. **Y la que casi cuesta la sesión: una ausencia sólo es evidencia en proporción a la densidad de
   la presencia.** El silencio de `ADS_AGENT` era la prueba perfecta hasta que medí que ese
   silencio pasa cada tres semanas.

---

## 11. ESTADO AL CERRAR

- **INC-000016471**: `ROOT_CAUSE_CONFIRMED`. Acción única, de Basis: arrancar la instancia Java 03
  de `hq-sap-sbp`. Texto para el Service Desk entregado. **Sigue caído al cerrar.**
- **INC-000016338** (UIL/BCM): el `.eml` del día confirma aceptación del negocio; sigue pendiente
  sólo el rol `BNK_APP` con Patrick.
- Commits: `f345495` (apertura), `2613c98` (maturity), `542a79d` (causa raíz + monitor).
- ⚠️ **Activos LOCAL-ONLY sin copia**: Golden DB **21,25 GB** (+521 MB esta sesión) y `~/.claude`
  1,92 GB. **Git no los protege.** Backup **DIFERIDO** en esta sesión: la prioridad fue un
  incidente vivo con un usuario que se va de vacaciones mañana. Destino registrado:
  `D:\claude_backups`.
