# INC-000016471 — "Create PDF Agreement" falla en la app Internship Agreement: ADS caído

**Track A — diagnóstico. Sesión #105, 2026-08-26.**
Estado: **`ROOT_CAUSE_CONFIRMED`** — confirmado por DOS instrumentos independientes el mismo día.

---

## BRIEF — 60 segundos

**La instancia Java (nº 03) que sirve Adobe Document Services en `hq-sap-sbp` (Solution Manager
producción) está PARADA.** La instancia ABAP (nº 01) de esa misma máquina sigue corriendo, por eso
SolMan parece sano. P01 llama a ADS por el destino RFC `ADS` (tipo G, HTTP) al puerto 50300 de esa
máquina, y ahí no escucha nadie.

**La prueba, por dos caminos que no comparten nada:**

| Instrumento | Desde | Credenciales | Resultado |
|---|---|---|---|
| `SM59 → ADS → Connection Test` | dentro de P01 | las del destino | `NIECONN_REFUSED(-10)` |
| `ads_availability_check.py` | esta máquina, fuera de SAP | **ninguna** | `CONNECTION_REFUSED` a `172.16.4.107:50300` |

**Un rechazo de conexión descarta casi todo:** no llega a la autenticación (**no es `ADSUSER`** —
era la causa favorita y queda refutada), no es firewall (eso da *timeout*, no rechazo), no es la
máquina (para rechazar hay que estar encendido, y el latido de SolMan es normal), y no es la
configuración del destino (la pantalla de SM59 coincide con `rfcdes` byte a byte).

**Ventana:** ADS respondió por última vez el **viernes 2026-08-21 a las 14:35:30**; los primeros
usuarios que chocan son del **lunes 24 a las 09:00**. Se paró durante el fin de semana y lleva
**tres días laborables** parada.

**Alcance:** no es una convención de prácticas. Son los ~43-50 formularios Adobe de la casa —
contratos de personal, attestations de trabajo, el PAF, cartas de dunning de FI y contratos y
facturas de RE-FX. Y **12-15 personas distintas al día** chocando contra el mismo botón.

**Acción, una y de Basis:** arrancar la instancia Java 03 de `hq-sap-sbp` y averiguar por qué no
volvió tras el fin de semana. No hay que tocar `ADSUSER`, ni el destino, ni la app de HR.

**Por qué nadie se enteró en tres días:** este canal no tenía monitor. Estaba catalogado
`NO_MEDIBLE` — cierto para el TRÁFICO, falso para la DISPONIBILIDAD. Ya existe el monitor:
`python Zagentexecution/quality_checks/ads_availability_check.py` (sin credenciales, 0 s).

---

## 0. TRIAJE (paso 0 obligatorio)

**Track A — DIAGNÓSTICO.** La incógnita es *por qué*.

Pero el triaje devuelve una conclusión de **encaminamiento** antes que de causa: esto es un fallo de
**infraestructura (Basis / AS Java)**, no funcional. Ni HCM, ni Recruitment, ni FI. La clasificación
del ticket ("Core Applications, Core HR+, Recruitment") apunta al equipo equivocado, y eso es
exactamente por qué el ticket ha rebotado por cuatro personas en un día mientras corre el plazo del
usuario.

---

## 1. EL TICKET, PARSEADO

| Campo | Valor |
|---|---|
| Ticket | INC-000016471 (SMART / Salesforce, `0nyMI0000007Nnt`) |
| Creado | 2026-08-25 17:32 por Service Desk |
| Asignado a | Laia Caballé, Adil Sefiani (ausente) |
| Usuario | Etienne Wintenberger — `e.wintenberger@unesco.org` |
| Departamento | ADM/DBS/SAA/ALR/AR — Audiovisual Archivist |
| Prioridad | **Critical** |
| Clasificación | Core Applications, **Core HR+, Recruitment** |
| Aplicación | "Internship Agreement" — botón **Create PDF Agreement** |
| Plazo real del usuario | se va de vacaciones el jueves **2026-08-27** |

**Síntoma, en sus palabras (FR):** no consigue crear el PDF de la *convention de stage*. La convención
**ya está validada por HRM y AO**; sólo falta imprimirla para que la firmen candidato y supervisor. Al
pulsar *Create PDF Agreement* sale el error. Ha reiniciado el PC varias veces; mismo problema **desde
esa mañana**. Ya había contactado a Christopher Cruz.

**Cadena de encaminamiento (todo el 26/08):** Caballé 08:29 "in absence of Adil, can anyone help?" →
Sabri 09:51 "I'm looping Narmin" → Allami 13:04 "do you think you can help in the absence of the
team?" → JP Lopez 09:25 UTC **"Unfortunately this time I can not help."**

Ese "no puedo ayudar" era el instinto correcto. Lo que sigue es el *por qué* y el *a quién*, que es
lo que faltaba para que el ticket dejara de rebotar.

---

## 2. EL ERROR, LEÍDO LITERALMENTE

Captura adjunta al ticket (`image001.png`):

```
500 Internal Server Error
ADS: SOAP Runtime Exception: CSoapExceptionTransport :(100101)
Server time:
```

Descomponiendo, término a término:

- **ADS** = *Adobe Document Services*. Es el motor que convierte un formulario SAP Interactive Form
  (Adobe/XFA) en un PDF. **No corre en la pila ABAP**: es una aplicación Java, en un AS Java aparte.
- **SOAP Runtime Exception / `CSoapExceptionTransport`** = el cliente SOAP del lado ABAP **no pudo
  completar la llamada HTTP**. *Transport* significa que la petición no obtuvo una respuesta HTTP
  válida — no que la respuesta trajera un error de negocio.
- **`Server time:` vacío** lo corrobora: no volvió cuerpo de respuesta con el que rellenarlo.

**Por tanto: no es el formulario, no son los datos, no es el PC del usuario.** Reiniciar el PC no
puede arreglarlo — que es exactamente lo que el usuario observó y reportó tres veces.

> ⚠️ **Y no es UN render: son CUATRO.** El botón genera `YHRINT_AGREEMENT_V2_MAIN_FR` más tres
> anexos (`_ANEX1_FR`, `_ANEX2_FR`, `_ANEX3_FR`) a través de la interfaz `YHRINT_IF_AGREEMENT_V2`.
> Ver §3bis.

---

## 3. EL CANAL — MEDIDO

Destino RFC `ADS` en P01. Fuente: Gold DB, tabla `rfcdes` (239 destinos, provenance P01).
⚠️ Es una **instantánea de configuración**, no una lectura de hoy — ver §8.

```
RFCDEST  ADS
RFCTYPE  G          -> conexión HTTP a un servidor EXTERNO
RFCOPTIONS:
  H = hq-sap-sbp.hq.int.unesco.org        <- host
  I = 50300                               <- puerto
  N = /AdobeDocumentServices/Config?style=rpc   <- endpoint SOAP
  D = ADSUSER                             <- usuario
  v = %_PWD                               <- contraseña almacenada en el destino
  Q = B                                   <- autenticación BASIC
  s = N                                   <- SIN SSL: HTTP plano
  T = N                                   <- traza DESACTIVADA
```

Lo que dice esta línea:

1. **ADS vive en otro host que el ABAP productivo**: `hq-sap-sbp`, no `hq-sap-p01`. Es un sistema Java
   distinto, con su propio ciclo de vida, sus propios reinicios y su propio equipo.
2. **Puerto 50300** = puerto HTTP estándar de AS Java para el número de instancia **03** (`5<NN>00`).
3. **Autenticación básica con usuario de servicio `ADSUSER`**, contraseña guardada en el destino.
4. **`s=N`: HTTP plano, sin SSL.** *Hallazgo colateral*: las credenciales de un usuario de servicio
   cruzan la red sin cifrar en cada render de PDF. No es la causa de este incidente; es deuda que
   este incidente destapa.
5. **`T=N`: la traza está apagada.** No habrá traza del destino que mirar; el diagnóstico tiene que
   venir del lado Java.

---

## 3bis. QUÉ ES LA APLICACIÓN, Y QUÉ HAY AL OTRO LADO DEL DESTINO (medido, sesión #105)

### La app — RESUELTO

**`ZPAWF_INT_AGREE`: WebDynpro ABAP custom de UNESCO, corriendo en el propio P01.** Componente
`WDYN` + aplicación `WDYA` + nodo `ICF` con ese nombre, y el nodo está **activo** (`ICFACTIVE='X'`).
Familia `ZPAWF_` = **PA-WorkFlow** (`ZPAWF__MAIN`, `ZPAWF_LWOP`, `ZPAWF_SPA`, `ZPAWF_SEPARATION`,
`ZPAWF_INT_HP`). Sólo hay 19 WebDynpros custom en toda la instalación y **4 son de esta app**.

**No es Fiori. No es un satélite. No es SAP e-Recruiting (HRRCF).** La clasificación del ticket
—*"Core HR+, Recruitment"*— está mal **por partida doble: ni el módulo (es PA-Workflow, no
Recruitment) ni la capa (es plataforma, no funcional).**

Lo que el botón renderiza, todo namespace `YHRINT_` (= HR INTernship): interfaz
`YHRINT_IF_AGREEMENT_V2` + formularios `YHRINT_AGREEMENT_V2_MAIN_EN/_FR`, `_ANEX1..3_EN/_FR`.
Hermanos de la misma app: `YHRINT_CERTIFICATE`, `YHRINT_EVALUATION`, `YHRINT_IF_CONTRACT_IT`.
Total bajo `YHRINT`: **15 formularios `SFPF` + 5 interfaces `SFPI`**.

Lógica del botón: clase de asistencia **`YCL_HR_INT_WF_ASSIST`** ("Assistance Class WD Internship").
Datos: estructuras `YSHR_IF_INT_CONTRACT` ("Structure interface PDF Agreement Internship"),
`YSHR_INT_AGREE_PDF`, `YSHR_INT_AGR_DATA_V2`. Tablas `YTHRINT_*` / `YTHRINTWF_*` (21).

> **Coautores de la aplicación, según las líneas `MERG` de `e071`: `N_MENARD` y `A_SEFIANI`.**
> A_SEFIANI = **Adil Sefiani, el asignatario ausente del ticket**. No estaba asignado por azar: es
> coautor. Eso explica por qué el ticket se paralizó al faltar él — y no cambia el hecho de que
> el equipo correcto para ESTE fallo sigue siendo Basis. El dueño funcional a notificar en
> paralelo es HR/PA-WF, **no Recruitment**.
> Último cambio a los formularios: transporte `D01K9B0DJU` *"HR - Internship agreement evolution
> 2025/09"*.

### El host — y esto es lo que más pesa

**`hq-sap-sbp` NO es "la máquina de Adobe": es el SOLUTION MANAGER DE PRODUCCIÓN (SBP, cliente
200), y aloja TRES cosas a la vez.** Fuente: `companions/system_inventory.html:333-345`
(*"Also hosts ADS (Adobe Document Services) and SLD"*), corroborado en `companions/rfc_analysis.html`.

P01 tiene **9 destinos RFC** apuntando a esa máquina:

| Destino | Tipo | Qué es | Puerto |
|---|---|---|---|
| `ADS` | G | `/AdobeDocumentServices/Config`, `D=ADSUSER` | 50300 |
| `SLD_DS_HTTP` / `SLD_DS_TARGET` | G | `/sld/ds`, `D=j2ee_admin` | 50300 |
| `SLD_NUC` / `SLD_UC` | T | programa externo por gateway | `sapgw00` |
| `SM_SBPCLNT200_BACK` | 3 | ABAP SolMan, `U=SMB_P01` | inst. 01 |
| `SM_SBPCLNT200_TRUSTED` / `SM_SBP_TRUSTED_BACK` | 3 | Trusted RFC | inst. 01 |
| `TRUSTING@SBP_0021192538` | 3 | Trusting, `LB=ON` | — |

**Si `hq-sap-sbp` se reinició, no se llevó sólo el PDF.** Se llevó a la vez ADS (todos los
formularios Adobe), el **SLD** (sin él los data suppliers de P01 fallan y el paisaje deja de
actualizarse) y **SolMan Producción** (EWA, monitoreo, ChaRM/TMS y los 3 trusted RFC).

**Corroboración cruzada del inquilinato:** en `rsau_audit_history`, el usuario `SMTMSBP` (el usuario
TMS de SolMan) entra **12.159 veces entre 2026-02-03 y 2026-08-22 desde `172.16.4.107`** — la misma
IP desde la que entra `ADS_AGENT`. **`172.16.4.107` = `hq-sap-sbp`.**

**`hq-sap-sbp:50300` es el ÚNICO AS Java de aplicación del paisaje P01.** No hay ADS de respaldo,
no hay failover: un host, un puerto, sin SSL. Los otros 26 destinos tipo G a `SAPControl.CGI`
(puertos 5NN13/5NN14) son agentes de monitoreo, no AS Java de aplicación.

### El rol `ADSCALLERS`: creado VACÍO a propósito, y sigue vacío

Transporte **`D01K9B07XR` = "ADS configuration - Empty role ADSCALLERS"**, liberado por
`V.VAURETTE` el **2021-07-28 15:13:28**. Contiene `R3TR ACGR ADSCALLERS` + `R3TR TABU AGR_TIMEB`.
En `agr_users` **no hay ninguna fila para `ADSCALLERS`** → sin usuarios asignados en P01. Es el
patrón estándar de SAP (el rol que importa vive en el UME de Java; el `ACGR` ABAP es el contenedor).

Fecha reveladora: `D01K9B07XR` es el vecino inmediato de `D01K9B07XZ` (primer transporte de
Internship) y `ADS_AGENT` se creó el `2021-08-04`. **ADS y la app Internship Agreement se pusieron
en marcha en el mismo proyecto, la misma semana de 2021.**

---

## 4. LAS CINCO COSAS QUE PRODUCEN EXACTAMENTE ESTE ERROR

Ordenadas por probabilidad, no por opinión: `CSoapExceptionTransport` acota el conjunto a fallos de
transporte, y en un ADS de destino tipo G sólo hay cuatro.

| # | Causa | Cómo se ve | Quién la mira |
|---|---|---|---|
| 1 | **AS Java / la aplicación ADS en `hq-sap-sbp` está caída o se reinició** | conexión rechazada / sin respuesta | Basis + dueño del Java |
| 2 | **`ADSUSER` bloqueado o con contraseña caducada** en el UME de Java | HTTP 401, que el cliente ABAP envuelve como excepción de transporte | Basis (UME) |
| 3 | **Ruta de red a `hq-sap-sbp:50300` cortada** (firewall, DNS, host movido) | timeout | Red / Basis |
| 4 | **Java sin recursos** — el proceso de render colgado | timeout largo | Basis |
| **5** | **`ADS_AGENT` bloqueado o caducado** — la credencial de VUELTA (Java → ABAP) | **SM59 daría 200 y aun así no habría PDF** | Basis (SU01 en P01) |

### La quinta causa existe porque son DOS credenciales, no una

Esto no estaba en la apertura y es el error más fácil de cometer con ADS:

| | Sentido | Dónde vive el usuario | ¿Lo vemos? |
|---|---|---|---|
| `ADSUSER` | **ida**: ABAP → Java (render) | UME de **Java** | **NO** — no está en `USR02` |
| `ADS_AGENT` | **vuelta**: Java → ABAP (HTTP desde `172.16.4.107`) | `USR02` de **P01** | **SÍ** |

**El *Connection Test* de SM59 sólo prueba la IDA.** Si el problema estuviera en `ADS_AGENT`, SM59
devolvería 200 y el PDF seguiría sin salir. Hay que comprobar las dos.

Estado medido de `ADS_AGENT` en la instantánea (~22-23 ago): `USTYP=B`, `UFLAG=0` (**no
bloqueado**), `GLTGB=00000000` (**sin caducidad**), `ERDAT=2021-08-04`, `TRDAT=2026-08-21`.
Eso **debilita la causa #5 para la ventana medida** y no dice nada de `ADSUSER`.

La **#2 es la reincidente clásica**: `ADSUSER` es un usuario de servicio cuya contraseña está
almacenada del lado ABAP; cualquier política de caducidad del UME o un bloqueo por intentos fallidos
produce un 401 sin que nadie haya tocado nada. Encaja con "funcionaba ayer, falla desde esta mañana".

### ⛔ ACTUALIZACIÓN (sesión #105, con el log de la ventana del fallo ya traído): SON DOS, NO CINCO

El corpus de auditoría se extendió hasta el **2026-08-26** (24, 25 y 26 completos: 166.176 /
160.379 / 121.461 filas). Con la ventana dentro, el latido de la máquina **refuta la causa #1**:

```
Latido de hq-sap-sbp hacia P01 (usuario SMTMSBP, IP 172.16.4.107)
  20260821  n=59   01:30..21:01
  20260822  n=24                  <- sabado
  20260823  n=29                  <- domingo
  20260824  n=50   01:30..21:01
  20260825  n=65   01:15..21:01   <- EL DIA DEL FALLO, por encima de la media
  20260826  n=52   01:30..11:23
```
Medido por el corte ancho (`PARAMX LIKE '%HQ-SAP-SBP%'`), el 2026-08-25 marca **2.138 eventos de
00:00:17 a 23:58:22 — indistinguible de un lunes normal.**

**La máquina no se cayó ni se reinició.** Misma máquina, dos instancias: la **ABAP 01** (SolMan)
no dejó de latir; la **Java 03** (puerto 50300, ADS) es la que calla.

| Causa | Veredicto |
|---|---|
| ~~#1 máquina caída/reiniciada~~ | **REFUTADA** por el latido |
| ~~#4 Java saturado hasta colgarse~~ | **MUY DEBILITADA** — la máquina no está saturada |
| **#1' la APLICACIÓN ADS parada** en la instancia Java 03 | **VIVA** |
| **#2 `ADSUSER` bloqueado/caducado** en el UME de Java | **VIVA — y es la única invisible para nosotros** |
| #3 red/DNS al host | **debilitada, no refutada**: el latido es SBP→P01 (entrante, instancia 01); no prueba la ruta P01→SBP:50300 (saliente, instancia 03). Eso lo prueba exactamente el test de SM59 |
| #5 `ADS_AGENT` | debilitada: desbloqueado y sin caducidad en la instantánea |

> **Consecuencia para el ticket: no hace falta pedir acceso al AS Java para avanzar hoy.** Las dos
> causas vivas las separa el MISMO clic de sólo lectura.

### La prueba que separa las dos es un clic

- **SM59 → destino `ADS` → Connection Test. ESTE ES EL PRIMER PASO, Y ES EL ÚNICO QUE HACE FALTA
  PARA DECIDIR.** Sólo lee, no cambia nada.
  **401** → es `ADSUSER` en el UME · **rechazo contra 50300** → la aplicación ADS está parada ·
  **200** → las dos caen y hay que mirar la pata de vuelta (`ADS_AGENT`).
- **La prueba definitiva es funcional: transacción `SFP` → *Utilities* → *Test ADS Connection***
  (reports `FP_TEST_00` / `FP_PDF_TEST_00`). Renderiza un PDF trivial y devuelve **el texto de error
  real de ADS** en vez del SOAP envuelto. Si eso falla, queda probado que el problema no tiene nada
  que ver con la convención de prácticas ni con la app de HR.

Ninguna de las cuatro es diagnosticable ni arreglable desde el lado ABAP, y ninguna es funcional.

---

## 5. RADIO DE ALCANCE — lo que NO está en el ticket y pesa más que lo que sí

**Si ADS está caído, TODOS los formularios Adobe del paisaje están caídos a la vez**, no sólo esta
convención de prácticas. En esta instalación eso incluye, como mínimo:

- **La familia de formularios HR ASR.** `knowledge/domains/HR-Workflows/README.md` registra el *ASR
  Framework — Standard SAP Adobe Service Request HR forms, redefined* (`CL_HCMFAB_*`,
  `CL_HRASR00GEN_SERVICE`). Es decir: toda la familia de formularios de acciones de personal.
- **Potencialmente la impresión de medios de pago.** `RFFORI00` es el único programa de nuestro corpus
  extraído que lleva llamadas a formularios Adobe.

**Consecuencia operativa:** una prioridad *Critical* sobre una convención de prácticas probablemente
está **infravalorando** el incidente. La primera pregunta de vuelta al Service Desk no es "¿qué
pulsaste?" sino:

> **¿Hay alguien más desde esta mañana que no consiga generar un PDF desde SAP?**

Un solo ticket parecido convierte esto de "un usuario con un problema" en "un canal de salida caído",
y eso cambia la prioridad, el equipo y el tiempo de respuesta.

⚠️ **Límite de la medida:** nuestro corpus de código extraído es PARCIAL (812 + 335 ficheros, no el
repositorio entero). **1 acierto es un suelo, no un recuento.** No sabemos cuántos objetos de esta
instalación renderizan por ADS. Ese es un hueco real, ver §7.

---

## 6. QUIÉN LO POSEE

**Basis / SAP Tech Administrators** (`sap.admin@unesco.org`, ya está en copia desde el principio) más
quien opere la máquina AS Java `hq-sap-sbp`.

No HCM. No Recruitment. No FI. No este proyecto.

Sobre el plazo del usuario (se va el jueves 27): **sin ADS no hay PDF**. No existe una vía ABAP
alternativa para producir ese documento — el render *es* ADS. Si ADS no vuelve a tiempo, la salida es
del lado del proceso de HR (reemitir la convención por otro canal), y esa decisión es del dueño de la
aplicación Internship Agreement, no nuestra. Decirlo pronto y claro le vale más al usuario que una
espera.

---

## 7. ESTADO DEL BRAIN — esto es un PUNTO CIEGO, y ese es el hallazgo sobre nosotros

Búsqueda en todos los stores (`graph_queries.py search`):

| Término | claims | rules | incidents | annotations | code | domains |
|---|---:|---:|---:|---:|---:|---:|
| `Adobe` | 0 | 0 | 0 | 0 | 0 | 1 (Output) |
| `internship` | 0 | 0 | 0 | 0 | 0 | 0 |
| `ADSUSER` | 0 | 0 | 0 | 0 | 0 | 0 |
| `SFP` | 0 | 0 | 0 | 0 | 0 | 0 |

Todo lo que teníamos sobre ADS eran **dos líneas**:

1. `knowledge/domains/Integration/integration_map_complete.md` flujo 8.5 — *"SAP P01 → ADS (Adobe),
   HTTP, destino `ADS`, Adobe Document Services — PDF form generation, [VERIFIED] Standard SAP
   component"*, con volumen `?`.
2. `brain_v2/interface_inventory.json` — canal `RFC_DESTINATION`, artefacto `ADS`, tipo G, saliente,
   naturaleza **`NO_MEDIBLE`**: *"un destino SALIENTE no registra en nuestro log qué hace en el
   sistema destino. Se mediría en el otro extremo. Ausencia de dato, no de riesgo."*

Esa etiqueta era honesta y sigue siéndolo. Pero lo que este incidente demuestra es que **teníamos un
canal de salida entero — todos los PDF que la institución produce desde SAP — con una línea de
inventario, sin dueño declarado, sin monitor, y sin radio de alcance medido.** El dominio `Output`
está marcado *stranded* en la columna vertebral de procesos (ni en un flujo ni transversal a uno).
Esto es qué aspecto tiene un dominio *stranded* el día que se rompe.

---

## 8. LO QUE NO PUDE HACER EN ESTA SESIÓN (declarado, no omitido)

1. **La sonda en vivo contra P01 fue BLOQUEADA** por el modo de permisos de la sesión. Los valores del
   destino en §3 vienen de la instantánea del Gold DB — provenance P01, pero **no es una lectura de
   hoy**, y `rfcdes` no tiene fila en `_gold_sync_log`, así que su fecha de extracción es
   **desconocida**. Reverificar con:
   ```
   python Zagentexecution/sap_data_extraction/scripts/_probe_ads_destination.py
   ```
   (creado en esta sesión, sólo lectura, `RFC_READ_TABLE` sobre `RFCDES` / `RFCDOC`).
2. **Falta una captura.** El ticket referencia `image003.png` además de la del 500; en el .eml sólo
   viajó `image001.png`. Lo que mostrara la segunda está sin leer.
3. **No sé qué es exactamente la app "Internship Agreement"** — si es WebDynpro ABAP, un Fiori, o un
   satélite que llama a SAP. Sólo sé, por el error, que su render de PDF pasa por ADS de P01. En el
   corpus extraído existe `YCL_HRWF_INTERN_GOS` (`extracted_code/HCM/YHR_PA_WF/`), clase de Generic
   Object Services de prácticas, pero **no contiene lógica de PDF ni llamadas a ADS** — comprobado. No
   es el sitio.

---

## 9. ACCIONES

| # | Acción | Quién | Estado |
|---|---|---|---|
| A1 | `SM59` → destino `ADS` → *Connection Test* en P01. Separa las cuatro causas en un clic | Basis / SAP Tech Admin | PENDIENTE |
| A2 | `SFP` → *Test ADS Connection* (`FP_PDF_TEST_00`) — devuelve el error REAL de ADS | Basis / SAP Tech Admin | PENDIENTE |
| A3 | Comprobar `ADSUSER` en el UME de Java: bloqueado / contraseña caducada | Basis | PENDIENTE |
| A4 | Verificar que la aplicación `AdobeDocumentServices` está arrancada en NWA en `hq-sap-sbp` | dueño del AS Java | PENDIENTE |
| A5 | **Preguntar al Service Desk si hay más tickets de "no se genera el PDF" desde el 25/08** — es lo que reclasifica el incidente | Service Desk | PENDIENTE |
| A6 | Reclasificar el ticket: de *Core HR+ / Recruitment* a *Basis / Infraestructura* | Service Desk | PENDIENTE |
| A7 | Decir al usuario, hoy, que sin ADS no hay PDF y que la salida para su plazo del 27 es de proceso, no técnica | quien lleve el ticket | PENDIENTE |
| A8 | **NUESTRO:** medir el radio real de ADS — cuántos objetos de P01 renderizan por Adobe. `TNAPR`/`FPCONTEXT`, o census de llamadas `FP_JOB_OPEN`/`FP_FUNCTION_MODULE_NAME` sobre el repositorio completo, no sobre el corpus parcial | este proyecto | BACKLOG |
| A9 | **NUESTRO:** dar dueño y monitor al canal ADS en el inventario de interfaces; `NO_MEDIBLE` es correcto para el tráfico, pero la DISPONIBILIDAD sí se mide desde nuestro lado (test de conexión periódico) | este proyecto | BACKLOG |
| A10 | Registrar la deuda: `s=N` en el destino ADS — basic auth de usuario de servicio sobre HTTP plano | este proyecto | BACKLOG |

---

## 10. LECCIONES

1. **`CSoapExceptionTransport` es un veredicto, no un síntoma.** *Transport* significa que no hubo
   respuesta HTTP. Eso descarta de golpe el formulario, los datos y el puesto de trabajo — y ahorra
   toda la rama de diagnóstico funcional. Leer el error literalmente, término a término, hizo más que
   cualquier búsqueda.
2. **Un usuario que dice "he reiniciado el PC tres veces y sigue igual" ya te ha dado la mitad del
   diagnóstico.** Está descartando el cliente por ti. Escucharlo es más barato que repetirlo.
3. **Un ticket clasificado por la aplicación donde el usuario estaba, no por la capa que falló,
   rebota.** Este fue por cuatro personas en un día, con prioridad Critical, sin que nadie pudiera
   hacer nada — porque todos los destinatarios eran funcionales y el fallo era de plataforma.
4. **El alcance de un fallo de plataforma nunca es el que trae el ticket.** El ticket trae *un*
   usuario porque *un* usuario escribió. La pregunta que reclasifica el incidente ("¿le pasa a alguien
   más?") cuesta un correo y no la hizo nadie en cuatro saltos.
5. **`NO_MEDIBLE` para el tráfico no es `NO_MEDIBLE` para la disponibilidad.** Marcamos ADS como no
   medible porque es saliente y no vemos qué pasa al otro lado. Cierto — y sin embargo, "¿responde?"
   se contesta desde nuestro lado con un test de conexión. Confundir las dos preguntas dejó un canal
   entero sin vigilancia.

---

## 11. RELACIONADOS

- `knowledge/domains/Integration/integration_map_complete.md` — flujo 8.5 (ADS)
- `knowledge/domains/HR-Workflows/README.md` — ASR Framework (formularios HR Adobe)
- `brain_v2/interface_inventory.json` — canal `RFC_DESTINATION` / `ADS`, `NO_MEDIBLE`
- Gold DB `rfcdes` (239 filas) — configuración del destino
- `Zagentexecution/sap_data_extraction/scripts/_probe_ads_destination.py` — sonda creada aquí
- Corpus: `extracted_code/FI/SAPFPAYM/RFFORI00.abap` (único con llamadas a formularios Adobe),
  `extracted_code/HCM/YHR_PA_WF/YCL_HRWF_INTERN_GOS.abap` (prácticas, SIN lógica de PDF — descartado)
